from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import date as dt_date
from config import config

MONTHS = ["янв","фев","мар","апр","май","июн","июл","авг","сен","окт","ноя","дек"]
WEEKDAYS = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]

def _fmt_date(date_str: str) -> str:
    d = dt_date.fromisoformat(date_str)
    return f"{WEEKDAYS[d.weekday()]} {d.day} {MONTHS[d.month-1]}"

def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📅 Записаться",      callback_data="book_start"))
    builder.row(InlineKeyboardButton(text="❌ Отменить запись", callback_data="cancel_my_booking"))
    builder.row(InlineKeyboardButton(text="💅 Прайсы",          callback_data="prices"))
    builder.row(InlineKeyboardButton(text="🖼 Портфолио",        callback_data="portfolio"))
    return builder.as_markup()

def subscription_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📢 Подписаться", url=config.CHANNEL_LINK))
    builder.row(InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription"))
    return builder.as_markup()

def dates_kb() -> InlineKeyboardMarkup:
    from database.db import get_working_days
    builder = InlineKeyboardBuilder()
    days = get_working_days()
    if not days:
        builder.row(InlineKeyboardButton(text="Нет доступных дат", callback_data="noop"))
    for day in days:
        builder.row(InlineKeyboardButton(
            text=_fmt_date(day["date"]),
            callback_data=f"date:{day['date']}"
        ))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()

def slots_kb(date: str) -> InlineKeyboardMarkup:
    from database.db import get_free_slots_for_date
    builder = InlineKeyboardBuilder()
    slots = get_free_slots_for_date(date)
    if not slots:
        builder.row(InlineKeyboardButton(text="Нет свободных слотов", callback_data="noop"))
    for slot in slots:
        builder.row(InlineKeyboardButton(
            text=f"🕐 {slot['time']}",
            callback_data=f"slot:{slot['id']}"
        ))
    builder.row(InlineKeyboardButton(text="◀️ Назад к датам", callback_data="book_start"))
    return builder.as_markup()

def confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_booking"),
        InlineKeyboardButton(text="❌ Отмена",       callback_data="main_menu"),
    )
    return builder.as_markup()

def cancel_confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, отменить", callback_data="do_cancel_booking"),
        InlineKeyboardButton(text="◀️ Назад",        callback_data="main_menu"),
    )
    return builder.as_markup()

def back_to_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()

def portfolio_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="👀 Смотреть портфолио",
        url="https://ru.pinterest.com/crystalwithluv/_created/"
    ))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()

def admin_main_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Добавить рабочий день",  callback_data="admin_add_day"))
    builder.row(InlineKeyboardButton(text="🕐 Добавить слот",          callback_data="admin_add_slot"))
    builder.row(InlineKeyboardButton(text="🗑 Удалить слот",            callback_data="admin_del_slot"))
    builder.row(InlineKeyboardButton(text="🚫 Закрыть/открыть день",   callback_data="admin_close_day"))
    builder.row(InlineKeyboardButton(text="❌ Отменить запись клиента", callback_data="admin_cancel_booking"))
    builder.row(InlineKeyboardButton(text="📋 Просмотр расписания",    callback_data="admin_view"))
    builder.row(InlineKeyboardButton(text="🏠 Выйти",                  callback_data="main_menu"))
    return builder.as_markup()

def admin_dates_kb(callback_prefix: str) -> InlineKeyboardMarkup:
    from database.db import get_working_days
    builder = InlineKeyboardBuilder()
    days = get_working_days()
    if not days:
        builder.row(InlineKeyboardButton(text="Нет рабочих дней", callback_data="noop"))
    for day in days:
        label = _fmt_date(day["date"])
        if day["is_closed"]:
            label = f"🚫 {label}"
        builder.row(InlineKeyboardButton(
            text=label,
            callback_data=f"{callback_prefix}:{day['date']}"
        ))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel"))
    return builder.as_markup()

def admin_slots_kb(date: str, action: str) -> InlineKeyboardMarkup:
    from database.db import get_slots_for_date
    builder = InlineKeyboardBuilder()
    slots = get_slots_for_date(date)
    if not slots:
        builder.row(InlineKeyboardButton(text="Нет слотов", callback_data="noop"))
    for slot in slots:
        status = "✅" if not slot["is_booked"] else "❌"
        builder.row(InlineKeyboardButton(
            text=f"{status} {slot['time']}",
            callback_data=f"{action}:{slot['id']}"
        ))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel"))
    return builder.as_markup()
