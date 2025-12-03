from __future__ import annotations

import asyncio
import re
from aiogram import Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command

from bot.db.session import Database
from bot.services.formatting import LANGUAGES, format_channel_report
from bot.services.tgstat_client import TgstatAPIError, TgstatClient

router = Router()

CHANNEL_PATTERN = re.compile(r"(?:https?://t\.me/)?@?(?P<username>[A-Za-z0-9_]{3,})")


def normalize_channel(text: str) -> str | None:
    match = CHANNEL_PATTERN.search(text.strip())
    if not match:
        return None
    return match.group("username")


async def get_language(db: Database, chat_id: int) -> str:
    row = await asyncio.to_thread(
        db.fetchone, "SELECT language FROM user_settings WHERE chat_id=?", (chat_id,)
    )
    if row and row["language"] in LANGUAGES:
        return row["language"]
    return "ru"


async def save_history(
    db: Database, chat_id: int, channel: str, subscribers: int | None, er: float | None
) -> None:
    await asyncio.to_thread(
        db.execute,
        "INSERT INTO history(chat_id, channel_username, subscribers, engagement_rate) VALUES(?, ?, ?, ?)",
        (chat_id, channel, subscribers, er),
    )


def build_actions_keyboard(language: str, channel: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=LANGUAGES[language]["update"], callback_data=f"refresh:{channel}"),
                InlineKeyboardButton(text=LANGUAGES[language]["history"], callback_data="history"),
            ]
        ]
    )


async def handle_channel_request(message: types.Message, channel: str, db: Database, client: TgstatClient) -> None:
    language = await get_language(db, message.chat.id)
    try:
        data = await client.get_channel_stats(channel)
    except TgstatAPIError as exc:
        error_text = LANGUAGES[language]["service_error"]
        if "not found" in str(exc).lower():
            error_text = LANGUAGES[language]["channel_not_found"]
        await message.answer(error_text)
        return

    await save_history(
        db,
        chat_id=message.chat.id,
        channel=channel,
        subscribers=data.get("members_count") or data.get("subscribers"),
        er=data.get("er") or data.get("er_view"),
    )
    report = format_channel_report(data, language=language)
    await message.answer(report, reply_markup=build_actions_keyboard(language, channel))


@router.message()
async def process_text(message: types.Message, db: Database, client: TgstatClient) -> None:
    if not message.text or message.text.startswith("/"):
        return
    channel = normalize_channel(message.text)
    language = await get_language(db, message.chat.id)
    if not channel:
        await message.answer(LANGUAGES[language]["invalid_input"])
        return
    await handle_channel_request(message, channel, db, client)


@router.callback_query(lambda c: c.data.startswith("refresh:"))
async def refresh_callback(callback: types.CallbackQuery, db: Database, client: TgstatClient) -> None:
    channel = callback.data.split(":", 1)[1]
    await handle_channel_request(callback.message, channel, db, client)  # type: ignore[arg-type]
    await callback.answer()
