# =============================================================
#  config.py — конфигурация бота
# =============================================================
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    BOT_TOKEN: str
    ADMIN_ID: int          # Telegram ID администратора
    CHANNEL_ID: str        # ID канала для расписания, например "@my_channel" или "-100123456"
    CHANNEL_LINK: str      # Ссылка на канал, например "https://t.me/my_channel"
    DB_PATH: str = "database/bot.db"

def load_config() -> Config:
    return Config(
        BOT_TOKEN=os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE"),
        ADMIN_ID=int(os.getenv("ADMIN_ID", "123456789")),
        CHANNEL_ID=os.getenv("CHANNEL_ID", "@your_schedule_channel"),
        CHANNEL_LINK=os.getenv("CHANNEL_LINK", "https://t.me/your_channel"),
    )

config = load_config()
