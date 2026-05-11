from __future__ import annotations
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from aiogram import Bot

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(
    jobstores={"default": MemoryJobStore()},
    timezone="Europe/Moscow",
)

async def _send_reminder(bot: Bot, user_id: int, time_str: str):
    text = (
        f"⏰ <b>Напоминание!</b>\n\n"
        f"Напоминаем, что вы записаны на маникюр завтра в <b>{time_str}</b>.\n"
        f"Ждём вас! 💅"
    )
    try:
        await bot.send_message(user_id, text, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Не удалось отправить напоминание {user_id}: {e}")

def schedule_reminder(bot: Bot, booking_id: int, user_id: int, date_str: str, time_str: str):
    appointment_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    remind_at = appointment_dt - timedelta(hours=24)
    if remind_at <= datetime.now():
        logger.info(f"Напоминание для записи {booking_id} не создано (менее 24 ч).")
        return
    job_id = f"reminder_{booking_id}"
    scheduler.add_job(
        _send_reminder,
        trigger="date",
        run_date=remind_at,
        args=[bot, user_id, time_str],
        id=job_id,
        replace_existing=True,
    )
    logger.info(f"Запланировано напоминание [{job_id}] на {remind_at}")

def cancel_reminder(booking_id: int):
    job_id = f"reminder_{booking_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Напоминание [{job_id}] удалено.")

def restore_reminders(bot: Bot):
    from database.db import get_all_future_bookings
    from datetime import datetime, timedelta
    bookings = get_all_future_bookings()
    now = datetime.now()
    restored = 0
    for b in bookings:
        remind_at = datetime.strptime(
            f"{b['date']} {b['time']}", "%Y-%m-%d %H:%M"
        ) - timedelta(hours=24)
        if remind_at > now:
            job_id = f"reminder_{b['id']}"
            scheduler.add_job(
                _send_reminder,
                trigger="date",
                run_date=remind_at,
                args=[bot, b["user_id"], b["time"]],
                id=job_id,
                replace_existing=True,
            )
            restored += 1
    logger.info(f"Восстановлено напоминаний: {restored}")
