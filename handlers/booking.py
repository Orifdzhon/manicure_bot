import re
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states.states import BookingStates
from keyboards.keyboards import (
    dates_kb, slots_kb, confirm_kb, cancel_confirm_kb,
    main_menu_kb, subscription_kb,
)
from database.db import (
    get_slot, get_user_booking, create_booking, cancel_booking_by_user,
)
from utils.channel import check_subscription, post_schedule_to_channel
from utils.scheduler import schedule_reminder, cancel_reminder
from config import config

router = Router()


@router.callback_query(F.data == "book_start")
async def cb_book_start(call: CallbackQuery, state: FSMContext, bot: Bot):
    """Начало записи — сначала проверяем подписку."""
    subscribed = await check_subscription(bot, call.from_user.id)
    if not subscribed:
        await call.message.edit_text(
            "📢 <b>Необходима подписка на канал</b>\n\n"
            "Для записи необходимо подписаться на наш канал.",
            parse_mode="HTML",
            reply_markup=subscription_kb(),
        )
        await call.answer()
        return
    await _show_dates(call, state)


@router.callback_query(F.data == "check_subscription")
async def cb_check_sub(call: CallbackQuery, state: FSMContext, bot: Bot):
    """Повторная проверка подписки."""
    subscribed = await check_subscription(bot, call.from_user.id)
    if not subscribed:
        await call.answer("❌ Вы ещё не подписаны!", show_alert=True)
        return
    await call.answer("✅ Подписка подтверждена!")
    await _show_dates(call, state)


async def _show_dates(call: CallbackQuery, state: FSMContext):
    existing = get_user_booking(call.from_user.id)
    if existing:
        await call.message.edit_text(
            f"⚠️ <b>У вас уже есть запись</b>\n\n"
            f"📅 Дата: <b>{existing['date']}</b>\n"
            f"🕐 Время: <b>{existing['time']}</b>\n\n"
            f"Сначала отмените текущую запись, чтобы записаться заново.",
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )
        await call.answer()
        return
    await state.set_state(BookingStates.choosing_date)
    await call.message.edit_text(
        "📅 <b>Выберите дату</b>\n\nДоступные даты:",
        parse_mode="HTML",
        reply_markup=dates_kb(),
    )
    await call.answer()


@router.callback_query(BookingStates.choosing_date, F.data.startswith("date:"))
async def cb_choose_date(call: CallbackQuery, state: FSMContext):
    date = call.data.split(":")[1]
    await state.update_data(date=date)
    await state.set_state(BookingStates.choosing_slot)
    await call.message.edit_text(
        f"🕐 <b>Выберите время</b>\n\nДата: <b>{date}</b>",
        parse_mode="HTML",
        reply_markup=slots_kb(date),
    )
    await call.answer()


@router.callback_query(BookingStates.choosing_slot, F.data.startswith("slot:"))
async def cb_choose_slot(call: CallbackQuery, state: FSMContext):
    slot_id = int(call.data.split(":")[1])
    slot = get_slot(slot_id)
    if not slot or slot["is_booked"]:
        await call.answer("⚠️ Этот слот уже занят!", show_alert=True)
        return
    await state.update_data(slot_id=slot_id)
    await state.set_state(BookingStates.entering_name)
    await call.message.edit_text(
        f"✏️ <b>Введите ваше имя</b>\n\n"
        f"📅 Дата: <b>{slot['date']}</b>\n"
        f"🕐 Время: <b>{slot['time']}</b>",
        parse_mode="HTML",
    )
    await call.answer()


@router.message(BookingStates.entering_name)
async def msg_enter_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("⚠️ Имя слишком короткое. Введите снова:")
        return
    await state.update_data(name=name)
    await state.set_state(BookingStates.entering_phone)
    await message.answer(
        "📱 <b>Введите номер телефона</b>\n\nФормат: +7XXXXXXXXXX",
        parse_mode="HTML",
    )


@router.message(BookingStates.entering_phone)
async def msg_enter_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not re.match(r"^[\+\d\s\(\)\-]{7,15}$", phone):
        await message.answer("⚠️ Неверный формат телефона. Попробуйте ещё раз:")
        return
    await state.update_data(phone=phone)
    data = await state.get_data()
    slot = get_slot(data["slot_id"])
    await state.set_state(BookingStates.confirming)
    await message.answer(
        f"📋 <b>Подтвердите запись</b>\n\n"
        f"👤 Имя: <b>{data['name']}</b>\n"
        f"📱 Телефон: <b>{phone}</b>\n"
        f"📅 Дата: <b>{slot['date']}</b>\n"
        f"🕐 Время: <b>{slot['time']}</b>",
        parse_mode="HTML",
        reply_markup=confirm_kb(),
    )


@router.callback_query(BookingStates.confirming, F.data == "confirm_booking")
async def cb_confirm(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    slot = get_slot(data["slot_id"])
    if not slot or slot["is_booked"]:
        await call.message.edit_text(
            "⚠️ Слот уже занят. Выберите другое время.",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        await call.answer()
        return

    success = create_booking(
        user_id=call.from_user.id,
        slot_id=data["slot_id"],
        name=data["name"],
        phone=data["phone"],
    )
    if not success:
        await call.message.edit_text(
            "⚠️ Не удалось создать запись. Попробуйте позже.",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        await call.answer()
        return

    booking = get_user_booking(call.from_user.id)
    if booking:
        schedule_reminder(
            bot=bot,
            booking_id=booking["id"],
            user_id=call.from_user.id,
            date_str=slot["date"],
            time_str=slot["time"],
        )

    await call.message.edit_text(
        f"✅ <b>Вы успешно записаны!</b>\n\n"
        f"📅 Дата: <b>{slot['date']}</b>\n"
        f"🕐 Время: <b>{slot['time']}</b>\n\n"
        f"Ждём вас! 💅",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )

    try:
        await bot.send_message(
            config.ADMIN_ID,
            f"🔔 <b>Новая запись!</b>\n\n"
            f"👤 Имя: <b>{data['name']}</b>\n"
            f"📱 Телефон: <b>{data['phone']}</b>\n"
            f"🆔 TG ID: <code>{call.from_user.id}</code>\n"
            f"📅 Дата: <b>{slot['date']}</b>\n"
            f"🕐 Время: <b>{slot['time']}</b>",
            parse_mode="HTML",
        )
    except Exception:
        pass

    await post_schedule_to_channel(bot, slot["date"])
    await state.clear()
    await call.answer()


@router.callback_query(F.data == "cancel_my_booking")
async def cb_cancel_my_booking(call: CallbackQuery):
    booking = get_user_booking(call.from_user.id)
    if not booking:
        await call.message.edit_text(
            "ℹ️ У вас нет активных записей.",
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )
        await call.answer()
        return
    await call.message.edit_text(
        f"❓ <b>Отменить запись?</b>\n\n"
        f"📅 Дата: <b>{booking['date']}</b>\n"
        f"🕐 Время: <b>{booking['time']}</b>",
        parse_mode="HTML",
        reply_markup=cancel_confirm_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "do_cancel_booking")
async def cb_do_cancel(call: CallbackQuery, bot: Bot):
    booking = get_user_booking(call.from_user.id)
    if not booking:
        await call.message.edit_text("ℹ️ Запись не найдена.", reply_markup=main_menu_kb())
        await call.answer()
        return

    cancel_reminder(booking["id"])
    date = booking["date"]
    cancel_booking_by_user(call.from_user.id)

    await call.message.edit_text(
        "✅ <b>Ваша запись отменена.</b>",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )
    try:
        await bot.send_message(
            config.ADMIN_ID,
            f"❌ <b>Отмена записи клиентом</b>\n\n"
            f"🆔 TG ID: <code>{call.from_user.id}</code>\n"
            f"📅 Дата: <b>{date}</b>",
            parse_mode="HTML",
        )
    except Exception:
        pass
    await post_schedule_to_channel(bot, date)
    await call.answer()
