from __future__ import annotations

import asyncio
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.db.session import Database
from bot.services.formatting import LANGUAGES

router = Router()


async def set_language(db: Database, chat_id: int, language: str) -> None:
    await asyncio.to_thread(
        db.execute,
        "INSERT INTO user_settings(chat_id, language) VALUES(?, ?)\n            ON CONFLICT(chat_id) DO UPDATE SET language=excluded.language",
        (chat_id, language),
    )


def build_language_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Русский"), KeyboardButton(text="O‘zbek")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


@router.message(Command("start"))
async def handle_start(message: types.Message, db: Database) -> None:
    text = (
        f"{LANGUAGES['ru']['greeting']}\n{LANGUAGES['ru']['prompt']}\n\n"
        f"{LANGUAGES['uz']['greeting']}\n{LANGUAGES['uz']['prompt']}"
    )
    await message.answer(
        text,
        reply_markup=build_language_keyboard(),
    )


@router.message(lambda m: (m.text or "").lower() in ["русский", "o‘zbek", "ozbek", "o'zbek"])
async def handle_language_choice(message: types.Message, db: Database) -> None:
    text = (message.text or "").lower()
    language = "ru" if "рус" in text else "uz"
    await set_language(db, message.chat.id, language)
    await message.answer(LANGUAGES[language]["prompt"])
