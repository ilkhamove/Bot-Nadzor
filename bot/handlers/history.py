from __future__ import annotations

import asyncio
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.db.session import Database
from bot.services.formatting import LANGUAGES
from bot.handlers.analytics import get_language, handle_channel_request

router = Router()


async def fetch_history(db: Database, chat_id: int) -> list[dict]:
    rows = await asyncio.to_thread(
        db.fetchall,
        "SELECT channel_username, subscribers, engagement_rate, created_at FROM history\n         WHERE chat_id=? ORDER BY created_at DESC LIMIT 10",
        (chat_id,),
    )
    return [dict(row) for row in rows]


def build_history_keyboard(records: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"@{row['channel_username']}" if not str(row['channel_username']).startswith('@') else row['channel_username'],
                callback_data=f"history:{row['channel_username']}",
            )
        ]
        for row in records
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("history"))
async def history_command(message: types.Message, db: Database) -> None:
    language = await get_language(db, message.chat.id)
    records = await fetch_history(db, message.chat.id)
    if not records:
        await message.answer(LANGUAGES[language]["no_history"])
        return
    await message.answer(LANGUAGES[language]["history"], reply_markup=build_history_keyboard(records))


@router.callback_query(lambda c: c.data == "history")
async def history_callback(callback: types.CallbackQuery, db: Database) -> None:
    language = await get_language(db, callback.message.chat.id)  # type: ignore[union-attr]
    records = await fetch_history(db, callback.message.chat.id)  # type: ignore[union-attr]
    if not records:
        await callback.message.answer(LANGUAGES[language]["no_history"])  # type: ignore[union-attr]
    else:
        await callback.message.answer(LANGUAGES[language]["history"], reply_markup=build_history_keyboard(records))  # type: ignore[arg-type]
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("history:"))
async def repeat_history(callback: types.CallbackQuery, db: Database, client) -> None:
    channel = callback.data.split(":", 1)[1]
    await handle_channel_request(callback.message, channel, db, client)  # type: ignore[arg-type]
    await callback.answer()
