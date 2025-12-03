from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    telegram_bot_token: str
    tgstat_api_key: str
    database_path: str = "data/bot.db"


def get_settings() -> Settings:
    """Load settings from environment variables and validate required values."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    api_key = os.getenv("TGSTAT_API_KEY")

    missing = []
    if not bot_token:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not api_key:
        missing.append("TGSTAT_API_KEY")

    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )

    db_path = os.getenv("BOT_DATABASE_PATH", "data/bot.db")
    return Settings(telegram_bot_token=bot_token, tgstat_api_key=api_key, database_path=db_path)
