import logging
from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from config import config
from database.db import get_all_bookings_for_date, get_slots_for_date
from datetime import date as dt_date

logger = logging.getLogger(__name__)

async def post_schedule_to_channel(bot: Bot, date: str):
    """Публикует расписание на дату в канал."""
    d = dt_date.fromisoformat(date)
    months = ["января","февраля","марта","апреля","мая","июня",
              "июля","августа","сентября","октября","ноября","декабря"]
    weekdays = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"]
    header = f"📅 <b>{weekdays[d.weekday()]}, {d.day} {months[d.month-1]} {d.year}</b>\n\n"
    slots = get_slots_for_date(date)
    bookings = {b["slot_id"]: b for b in get_all_bookings_for_date(date)}
    lines = []
    for slot in slots:
        if slot["is_booked"]:
            b = bookings.get(slot["id"])
            name = b["name"] if b else "—"
            lines.append(f"🔴 <b>{slot['time']}</b> — {name}")
        else:
            lines.append(f"🟢 <b>{slot['time']}</b> — свободно")
    body = "\n".join(lines) if lines else "Нет слотов."
    text = header + body
    try:
        await bot.send_message(config.CHANNEL_ID, text, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Ошибка публикации в канал: {e}")

async def check_subscription(bot: Bot, user_id: int) -> bool:
    """
    Проверяет подписку пользователя на канал.
    ВАЖНО: бот должен быть администратором канала!
    """
    try:
        member = await bot.get_chat_member(config.CHANNEL_ID, user_id)
        # Все статусы кроме left/kicked считаются подписанными
        return member.status not in (
            ChatMemberStatus.LEFT,
            ChatMemberStatus.KICKED,
        )
    except Exception as e:
        logger.warning(f"Ошибка проверки подписки для {user_id}: {e}")
        # При ошибке (например бот не админ) — пропускаем проверку
        return True
