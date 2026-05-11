import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
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

# ─── Прокси ───────────────────────────────────────────────────
# Раскомментируйте и укажите рабочий прокси если нужен,
# или оставьте None если используете системный VPN (Psiphon, WARP и др.)
#
# PROXY_URL = "socks5://IP:PORT"
# PROXY_URL = "socks5://user:pass@IP:PORT"
# PROXY_URL = "http://IP:PORT"
PROXY_URL = None


async def main():
    init_db()
    logger.info("База данных инициализирована.")

    if PROXY_URL:
        from aiohttp_socks import ProxyConnector
        import aiohttp
        connector = ProxyConnector.from_url(PROXY_URL)
        client_session = aiohttp.ClientSession(connector=connector)
        session = AiohttpSession()
        # Ждём создания внутренней сессии и подменяем её
        await session.create_session()
        old = session._session
        session._session = client_session
        await old.close()
        logger.info(f"Прокси: {PROXY_URL}")
    else:
        session = AiohttpSession()

    bot = Bot(
        token=config.BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(admin.router)
    dp.include_router(booking.router)
    dp.include_router(common.router)

    scheduler.start()
    restore_reminders(bot)
    logger.info("Планировщик запущен, напоминания восстановлены.")

    logger.info("Бот запущен!")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
