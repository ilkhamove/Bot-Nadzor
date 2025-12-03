from __future__ import annotations

import asyncio
import logging

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject
from typing import Any, Awaitable, Callable, Dict

from bot.config import get_settings
from bot.db.session import get_database, Database
from bot.handlers import analytics, history, start
from bot.services.tgstat_client import TgstatClient


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DependencyMiddleware(BaseMiddleware):
    def __init__(self, db: Database, client: TgstatClient) -> None:
        super().__init__()
        self.db = db
        self.client = client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["db"] = self.db
        data["client"] = self.client
        return await handler(event, data)


async def main() -> None:
    settings = get_settings()
    bot = Bot(token=settings.telegram_bot_token, parse_mode=ParseMode.HTML)
    db = get_database(settings.database_path)
    client = TgstatClient(settings.tgstat_api_key)

    dp = Dispatcher()
    dp.message.middleware(DependencyMiddleware(db, client))
    dp.callback_query.middleware(DependencyMiddleware(db, client))

    dp.include_router(start.router)
    dp.include_router(history.router)
    dp.include_router(analytics.router)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await client.close()
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
