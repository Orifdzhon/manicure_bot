# =============================================================
#  handlers/admin.py — административная панель
# =============================================================
from datetime import date as dt_date, timedelta
import re

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from states.states import AdminStates
from keyboards.keyboards import (
    admin_main_kb, admin_dates_kb, admin_slots_kb, back_to_menu_kb,
)
from database.db import (
    add_working_day, add_time_slot, delete_time_slot,
    close_day, get_all_bookings_for_date, get_slots_for_date,
    cancel_booking_by_slot, get_slot, get_booking_for_slot,
)
from utils.channel import post_schedule_to_channel
from utils.scheduler import cancel_reminder
from config import config

router = Router()

# ─── Доступ только для администратора ─────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_ID


# ─── Команда /admin ───────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    await state.clear()
    await message.answer(
        "🛠 <b>Административная панель</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=admin_main_kb(),
    )


# ─── Возврат в панель администратора ──────────────────────────────────────────

@router.callback_query(F.data == "admin_panel")
async def cb_admin_panel(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    await state.clear()
    await call.message.edit_text(
        "🛠 <b>Административная панель</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=admin_main_kb(),
    )
    await call.answer()


# ─── Добавить рабочий день ────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_add_day")
async def cb_admin_add_day(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔", show_alert=True)
        return
    await state.set_state(AdminStates.add_day)

    # Подсказка: ближайшие 30 дней
    today = dt_date.today()
    days_hint = ", ".join(
        [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 4)]
    )
    await call.message.edit_text(
        f"📅 <b>Добавить рабочий день</b>\n\n"
        f"Введите дату в формате <code>YYYY-MM-DD</code>\n"
        f"Например: <code>{days_hint}</code>",
        parse_mode="HTML",
    )
    await call.answer()


@router.message(AdminStates.add_day)
async def msg_admin_add_day(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    text = message.text.strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        await message.answer("⚠️ Неверный формат. Введите дату в виде <code>YYYY-MM-DD</code>:", parse_mode="HTML")
        return
    try:
        d = dt_date.fromisoformat(text)
    except ValueError:
        await message.answer("⚠️ Неверная дата. Попробуйте ещё раз:")
        return
    if d < dt_date.today():
        await message.answer("⚠️ Нельзя добавить прошедшую дату.")
        return
    if (d - dt_date.today()).days > 31:
        await message.answer("⚠️ Расписание формируется только на 1 месяц вперёд.")
        return

    ok = add_working_day(text)
    await state.clear()
    await message.answer(
        f"✅ День <b>{text}</b> добавлен." if ok else f"⚠️ День <b>{text}</b> уже существует.",
        parse_mode="HTML",
        reply_markup=admin_main_kb(),
    )


# ─── Добавить временной слот ──────────────────────────────────────────────────

@router.callback_query(F.data == "admin_add_slot")
async def cb_admin_add_slot(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔", show_alert=True)
        return
    await state.set_state(AdminStates.add_slot_date)
    await call.message.edit_text(
        "📅 <b>Добавить слот</b>\n\nВыберите дату:",
        parse_mode="HTML",
        reply_markup=admin_dates_kb("aslot_date"),
    )
    await call.answer()


@router.callback_query(AdminStates.add_slot_date, F.data.startswith("aslot_date:"))
async def cb_slot_date_chosen(call: CallbackQuery, state: FSMContext):
    date = call.data.split(":")[1]
    await state.update_data(slot_date=date)
    await state.set_state(AdminStates.add_slot_time)
    await call.message.edit_text(
        f"🕐 <b>Введите время для {date}</b>\n\nФормат: <code>HH:MM</code>, например <code>10:00</code>",
        parse_mode="HTML",
    )
    await call.answer()


@router.message(AdminStates.add_slot_time)
async def msg_admin_add_slot(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    text = message.text.strip()
    if not re.match(r"^\d{2}:\d{2}$", text):
        await message.answer("⚠️ Неверный формат. Введите время как <code>HH:MM</code>:", parse_mode="HTML")
        return
    data = await state.get_data()
    date = data["slot_date"]
    ok = add_time_slot(date, text)
    await state.clear()
    await message.answer(
        f"✅ Слот <b>{text}</b> на <b>{date}</b> добавлен." if ok
        else "⚠️ Не удалось добавить слот. Проверьте дату.",
        parse_mode="HTML",
        reply_markup=admin_main_kb(),
    )


# ─── Удалить временной слот ───────────────────────────────────────────────────

@router.callback_query(F.data == "admin_del_slot")
async def cb_admin_del_slot(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔", show_alert=True)
        return
    await state.set_state(AdminStates.delete_slot)
    await call.message.edit_text(
        "🗑 <b>Удалить слот</b>\n\nВыберите дату:",
        parse_mode="HTML",
        reply_markup=admin_dates_kb("del_slot_date"),
    )
    await call.answer()


@router.callback_query(AdminStates.delete_slot, F.data.startswith("del_slot_date:"))
async def cb_del_slot_date(call: CallbackQuery, state: FSMContext):
    date = call.data.split(":")[1]
    await state.update_data(del_date=date)
    await call.message.edit_text(
        f"🗑 <b>Выберите слот для удаления ({date})</b>",
        parse_mode="HTML",
        reply_markup=admin_slots_kb(date, "do_del_slot"),
    )
    await call.answer()


@router.callback_query(AdminStates.delete_slot, F.data.startswith("do_del_slot:"))
async def cb_do_del_slot(call: CallbackQuery, state: FSMContext, bot: Bot):
    slot_id = int(call.data.split(":")[1])
    slot = get_slot(slot_id)

    # Если слот занят — отменяем запись и напоминание
    booking = get_booking_for_slot(slot_id)
    if booking:
        cancel_reminder(booking["id"])

    delete_time_slot(slot_id)
    await state.clear()
    await call.message.edit_text(
        "✅ Слот удалён.",
        reply_markup=admin_main_kb(),
    )
    if slot:
        await post_schedule_to_channel(bot, slot["date"])
    await call.answer()


# ─── Закрыть день ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_close_day")
async def cb_admin_close_day(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔", show_alert=True)
        return
    await state.set_state(AdminStates.manage_day)
    await call.message.edit_text(
        "🚫 <b>Закрыть/открыть день</b>\n\nВыберите дату:",
        parse_mode="HTML",
        reply_markup=admin_dates_kb("toggle_day"),
    )
    await call.answer()


@router.callback_query(AdminStates.manage_day, F.data.startswith("toggle_day:"))
async def cb_toggle_day(call: CallbackQuery, state: FSMContext, bot: Bot):
    from database.db import get_day, open_day
    date = call.data.split(":")[1]
    day = get_day(date)
    if day and day["is_closed"]:
        open_day(date)
        msg = f"✅ День <b>{date}</b> открыт."
    else:
        close_day(date)
        msg = f"🚫 День <b>{date}</b> закрыт."
    await state.clear()
    await call.message.edit_text(msg, parse_mode="HTML", reply_markup=admin_main_kb())
    await post_schedule_to_channel(bot, date)
    await call.answer()


# ─── Отменить запись клиента ──────────────────────────────────────────────────

@router.callback_query(F.data == "admin_cancel_booking")
async def cb_admin_cancel_booking(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔", show_alert=True)
        return
    await state.set_state(AdminStates.cancel_booking)
    await call.message.edit_text(
        "❌ <b>Отменить запись</b>\n\nВыберите дату:",
        parse_mode="HTML",
        reply_markup=admin_dates_kb("adm_cancel_date"),
    )
    await call.answer()


@router.callback_query(AdminStates.cancel_booking, F.data.startswith("adm_cancel_date:"))
async def cb_admin_cancel_date(call: CallbackQuery, state: FSMContext):
    date = call.data.split(":")[1]
    await state.update_data(cancel_date=date)
    await call.message.edit_text(
        f"❌ <b>Выберите слот для отмены ({date})</b>\n\n"
        "✅ — свободен  |  ❌ — занят",
        parse_mode="HTML",
        reply_markup=admin_slots_kb(date, "adm_cancel_slot"),
    )
    await call.answer()


@router.callback_query(AdminStates.cancel_booking, F.data.startswith("adm_cancel_slot:"))
async def cb_admin_cancel_slot(call: CallbackQuery, state: FSMContext, bot: Bot):
    slot_id = int(call.data.split(":")[1])
    booking = get_booking_for_slot(slot_id)
    if not booking:
        await call.answer("ℹ️ На этот слот нет записи.", show_alert=True)
        return

    slot = get_slot(slot_id)

    # Удаляем напоминание
    cancel_reminder(booking["id"])

    cancelled = cancel_booking_by_slot(slot_id)
    await state.clear()
    await call.message.edit_text(
        f"✅ Запись клиента <b>{booking['name']}</b> отменена.",
        parse_mode="HTML",
        reply_markup=admin_main_kb(),
    )

    # Уведомляем клиента
    try:
        await bot.send_message(
            booking["user_id"],
            f"⚠️ <b>Ваша запись отменена администратором</b>\n\n"
            f"📅 Дата: <b>{slot['date']}</b>\n"
            f"🕐 Время: <b>{slot['time']}</b>\n\n"
            "Приносим извинения за неудобства.",
            parse_mode="HTML",
        )
    except Exception:
        pass

    if slot:
        await post_schedule_to_channel(bot, slot["date"])
    await call.answer()


# ─── Просмотр расписания ──────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_view")
async def cb_admin_view(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔", show_alert=True)
        return
    await state.set_state(AdminStates.view_date)
    await call.message.edit_text(
        "📋 <b>Просмотр расписания</b>\n\nВыберите дату:",
        parse_mode="HTML",
        reply_markup=admin_dates_kb("view_date"),
    )
    await call.answer()


@router.callback_query(AdminStates.view_date, F.data.startswith("view_date:"))
async def cb_admin_view_date(call: CallbackQuery, state: FSMContext):
    date = call.data.split(":")[1]
    slots = get_slots_for_date(date)
    bookings_map = {b["slot_id"]: b for b in get_all_bookings_for_date(date)}

    lines = [f"📋 <b>Расписание на {date}</b>\n"]
    if not slots:
        lines.append("Нет слотов.")
    for slot in slots:
        if slot["is_booked"]:
            b = bookings_map.get(slot["id"])
            name = b["name"] if b else "—"
            phone = b["phone"] if b else "—"
            lines.append(f"🔴 <b>{slot['time']}</b> — {name} ({phone})")
        else:
            lines.append(f"🟢 <b>{slot['time']}</b> — свободно")

    await state.clear()
    await call.message.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=admin_main_kb(),
    )
    await call.answer()
