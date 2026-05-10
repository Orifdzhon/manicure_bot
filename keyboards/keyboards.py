# =============================================================
#  keyboards/keyboards.py — все inline-клавиатуры
# =============================================================
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.db import get_working_days, get_free_slots_for_date, get_slots_for_date
from config import config


# ─── Главное меню ─────────────────────────────────────────────────────────────

def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📅 Записаться",      callback_data="book_start"))
    builder.row(InlineKeyboardButton(text="❌ Отменить запись", callback_data="cancel_my_booking"))
    builder.row(InlineKeyboardButton(text="💅 Прайсы",          callback_data="prices"))
    builder.row(InlineKeyboardButton(text="🖼 Портфолио",        callback_data="portfolio"))
    return builder.as_markup()


# ─── Проверка подписки ────────────────────────────────────────────────────────

def subscription_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📢 Подписаться", url=config.CHANNEL_LINK)
    )
    builder.row(
        InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")
    )
    return builder.as_markup()


# ─── Выбор даты (календарь) ───────────────────────────────────────────────────

def dates_kb() -> InlineKeyboardMarkup:
    """Список доступных дат на месяц вперёд."""
    builder = InlineKeyboardBuilder()
    days = get_working_days()
    if not days:
        builder.row(InlineKeyboardButton(text="Нет доступных дат", callback_data="noop"))
    for day in days:
        # Красивый формат: «Вт 15 июля»
        from datetime import date
        d = date.fromisoformat(day["date"])
        months = ["янв","фев","мар","апр","май","июн","июл","авг","сен","окт","ноя","дек"]
        weekdays = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]
        label = f"{weekdays[d.weekday()]} {d.day} {months[d.month-1]}"
        builder.row(
            InlineKeyboardButton(text=label, callback_data=f"date:{day['date']}")
        )
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()


# ─── Выбор времени ────────────────────────────────────────────────────────────

def slots_kb(date: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    slots = get_free_slots_for_date(date)
    if not slots:
        builder.row(InlineKeyboardButton(text="Нет свободных слотов", callback_data="noop"))
    for slot in slots:
        builder.row(
            InlineKeyboardButton(
                text=f"🕐 {slot['time']}",
                callback_data=f"slot:{slot['id']}"
            )
        )
    builder.row(InlineKeyboardButton(text="◀️ Назад к датам", callback_data="book_start"))
    return builder.as_markup()


# ─── Подтверждение записи ─────────────────────────────────────────────────────

def confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_booking"),
        InlineKeyboardButton(text="❌ Отмена",       callback_data="main_menu"),
    )
    return builder.as_markup()


# ─── Подтверждение отмены ─────────────────────────────────────────────────────

def cancel_confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, отменить", callback_data="do_cancel_booking"),
        InlineKeyboardButton(text="◀️ Назад",        callback_data="main_menu"),
    )
    return builder.as_markup()


# ─── Кнопка «Назад в меню» ────────────────────────────────────────────────────

def back_to_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()


# ─── Портфолио ────────────────────────────────────────────────────────────────

def portfolio_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="👀 Смотреть портфолио",
            url="https://ru.pinterest.com/crystalwithluv/_created/"
        )
    )
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()


# ─── Админ: главное меню ──────────────────────────────────────────────────────

def admin_main_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Добавить рабочий день", callback_data="admin_add_day"))
    builder.row(InlineKeyboardButton(text="🕐 Добавить слот",         callback_data="admin_add_slot"))
    builder.row(InlineKeyboardButton(text="🗑 Удалить слот",           callback_data="admin_del_slot"))
    builder.row(InlineKeyboardButton(text="🚫 Закрыть день",           callback_data="admin_close_day"))
    builder.row(InlineKeyboardButton(text="❌ Отменить запись клиента",callback_data="admin_cancel_booking"))
    builder.row(InlineKeyboardButton(text="📋 Просмотр расписания",    callback_data="admin_view"))
    builder.row(InlineKeyboardButton(text="🏠 Выйти",                  callback_data="main_menu"))
    return builder.as_markup()


# ─── Админ: выбор даты из существующих ───────────────────────────────────────

def admin_dates_kb(callback_prefix: str) -> InlineKeyboardMarkup:
    """Список всех рабочих дней для административных действий."""
    from database.db import get_working_days
    from datetime import date as dt_date
    builder = InlineKeyboardBuilder()
    days = get_working_days()
    months = ["янв","фев","мар","апр","май","июн","июл","авг","сен","окт","ноя","дек"]
    weekdays = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]
    for day in days:
        d = dt_date.fromisoformat(day["date"])
        label = f"{weekdays[d.weekday()]} {d.day} {months[d.month-1]}"
        if day["is_closed"]:
            label = f"🚫 {label}"
        builder.row(
            InlineKeyboardButton(
                text=label,
                callback_data=f"{callback_prefix}:{day['date']}"
            )
        )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel"))
    return builder.as_markup()


# ─── Админ: слоты дня (с возможностью удаления) ───────────────────────────────

def admin_slots_kb(date: str, action: str) -> InlineKeyboardMarkup:
    """Список слотов для дня — action: 'del_slot' или 'cancel_booking'."""
    builder = InlineKeyboardBuilder()
    slots = get_slots_for_date(date)
    for slot in slots:
        status = "✅" if not slot["is_booked"] else "❌"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {slot['time']}",
                callback_data=f"{action}:{slot['id']}"
            )
        )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel"))
    return builder.as_markup()
