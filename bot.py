# =============================================================
#  bot.py — точка входа
# =============================================================
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database.db import init_db
from handlers import common, booking, admin
from utils.scheduler import scheduler, restore_reminders

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    # Инициализируем БД
    init_db()
    logger.info("База данных инициализирована.")

    # Создаём бота и диспетчер
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем роутеры (порядок важен: admin → booking → common)
    dp.include_router(admin.router)
    dp.include_router(booking.router)
    dp.include_router(common.router)

    # Запускаем планировщик и восстанавливаем напоминания
    scheduler.start()
    restore_reminders(bot)
    logger.info("Планировщик запущен, напоминания восстановлены.")

    # Запускаем поллинг
    logger.info("Бот запущен!")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
