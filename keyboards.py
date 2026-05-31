from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import date as dt_date, timedelta
from config import config

MONTHS = ["Январь","Февраль","Март","Апрель","Май","Июнь",
          "Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"]
MONTHS_SHORT = ["янв","фев","мар","апр","май","июн","июл","авг","сен","окт","ноя","дек"]
WEEKDAYS = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]


def main_menu_kb(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Главное меню — 2 колонки."""
    builder = InlineKeyboardBuilder()
    # Ряд 1
    builder.row(
        InlineKeyboardButton(text="📅 Записаться",      callback_data="book_start"),
        InlineKeyboardButton(text="❌ Отменить запись", callback_data="cancel_my_booking"),
    )
    # Ряд 2
    builder.row(
        InlineKeyboardButton(text="💅 Прайсы",   callback_data="prices"),
        InlineKeyboardButton(text="🖼 Портфолио", callback_data="portfolio"),
    )
    # Кнопка админ-панели — только для администратора
    if is_admin:
        builder.row(
            InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin_panel")
        )
    return builder.as_markup()


def subscription_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📢 Подписаться", url=config.CHANNEL_LINK))
    builder.row(InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription"))
    return builder.as_markup()


def calendar_kb(year: int = None, month: int = None) -> InlineKeyboardMarkup:
    """
    Календарь с подсветкой доступных дней.
    Свободные дни — кнопки с датой, остальные — пустые/закрытые.
    """
    from database.db import get_working_days
    today = dt_date.today()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    # Собираем доступные даты в set для быстрого поиска
    available = {row["date"] for row in get_working_days()}

    builder = InlineKeyboardBuilder()

    # ── Заголовок: месяц и стрелки навигации ──
    prev_month = month - 1 if month > 1 else 12
    prev_year  = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year  = year if month < 12 else year + 1

    builder.row(
        InlineKeyboardButton(text="◀️", callback_data=f"cal:{prev_year}:{prev_month}"),
        InlineKeyboardButton(text=f"📅 {MONTHS[month-1]} {year}", callback_data="noop"),
        InlineKeyboardButton(text="▶️", callback_data=f"cal:{next_year}:{next_month}"),
    )

    # ── Заголовки дней недели ──
    builder.row(*[
        InlineKeyboardButton(text=wd, callback_data="noop")
        for wd in WEEKDAYS
    ])

    # ── Дни месяца ──
    # Первый день месяца
    first_day = dt_date(year, month, 1)
    # Сдвиг: weekday() → 0=Пн, 6=Вс
    start_offset = first_day.weekday()

    # Кол-во дней в месяце
    if month == 12:
        last_day = dt_date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = dt_date(year, month + 1, 1) - timedelta(days=1)
    days_in_month = last_day.day

    # Строим недели
    week = []
    # Пустые ячейки до первого дня
    for _ in range(start_offset):
        week.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    for day_num in range(1, days_in_month + 1):
        current = dt_date(year, month, day_num)
        date_str = current.isoformat()

        if date_str in available and current >= today:
            # Доступный день — кликабельная кнопка
            btn = InlineKeyboardButton(
                text=f"✅{day_num}",
                callback_data=f"date:{date_str}"
            )
        elif current < today:
            # Прошедший день
            btn = InlineKeyboardButton(text="·", callback_data="noop")
        else:
            # Будущий, но не рабочий
            btn = InlineKeyboardButton(text=str(day_num), callback_data="noop")

        week.append(btn)

        if len(week) == 7:
            builder.row(*week)
            week = []

    # Добираем последнюю неполную неделю
    if week:
        while len(week) < 7:
            week.append(InlineKeyboardButton(text=" ", callback_data="noop"))
        builder.row(*week)

    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()


def slots_kb(date: str) -> InlineKeyboardMarkup:
    from database.db import get_free_slots_for_date
    builder = InlineKeyboardBuilder()
    slots = get_free_slots_for_date(date)
    if not slots:
        builder.row(InlineKeyboardButton(text="Нет свободных слотов", callback_data="noop"))
    else:
        # Слоты по 3 в ряд
        row_btns = []
        for slot in slots:
            row_btns.append(InlineKeyboardButton(
                text=f"🕐 {slot['time']}",
                callback_data=f"slot:{slot['id']}"
            ))
            if len(row_btns) == 3:
                builder.row(*row_btns)
                row_btns = []
        if row_btns:
            builder.row(*row_btns)
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
    builder.row(
        InlineKeyboardButton(text="➕ Добавить день",    callback_data="admin_add_day"),
        InlineKeyboardButton(text="🕐 Добавить слот",    callback_data="admin_add_slot"),
    )
    builder.row(
        InlineKeyboardButton(text="🗑 Удалить слот",     callback_data="admin_del_slot"),
        InlineKeyboardButton(text="🚫 Закрыть день",     callback_data="admin_close_day"),
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отменить запись",  callback_data="admin_cancel_booking"),
        InlineKeyboardButton(text="📋 Расписание",       callback_data="admin_view"),
    )
    builder.row(InlineKeyboardButton(text="🏠 Выйти", callback_data="main_menu"))
    return builder.as_markup()


def admin_dates_kb(callback_prefix: str) -> InlineKeyboardMarkup:
    from database.db import get_working_days
    builder = InlineKeyboardBuilder()
    days = get_working_days()
    if not days:
        builder.row(InlineKeyboardButton(text="Нет рабочих дней", callback_data="noop"))
    for day in days:
        d = dt_date.fromisoformat(day["date"])
        label = f"{WEEKDAYS[d.weekday()]} {d.day} {MONTHS_SHORT[d.month-1]}"
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
        status = "🟢" if not slot["is_booked"] else "🔴"
        builder.row(InlineKeyboardButton(
            text=f"{status} {slot['time']}",
            callback_data=f"{action}:{slot['id']}"
        ))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel"))
    return builder.as_markup()
