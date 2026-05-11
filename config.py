import os
from dataclasses import dataclass

@dataclass
class Config:
    BOT_TOKEN: str
    ADMIN_ID: int
    CHANNEL_ID: str
    CHANNEL_LINK: str
    DB_PATH: str = "database/bot.db"

def load_config() -> Config:
    return Config(
        BOT_TOKEN=os.getenv("BOT_TOKEN", "1234567890:AAFakeTokenForTesting"),
        ADMIN_ID=int(os.getenv("ADMIN_ID", "123456789")),
        CHANNEL_ID=os.getenv("CHANNEL_ID", "@your_channel"),
        CHANNEL_LINK=os.getenv("CHANNEL_LINK", "https://t.me/your_channel"),
    )

config = load_config()
