from __future__ import annotations

from datetime import datetime
from typing import Any

LANGUAGES = {
    "ru": {
        "greeting": "Привет! Я помогу получить статистику Telegram-канала.",
        "prompt": "Отправьте @username или ссылку на канал.",
        "history": "История запросов",
        "update": "Обновить",
        "choose_language": "Выберите язык / Tilni tanlang",
        "no_history": "История пуста.",
        "service_error": "Сервис временно недоступен, попробуйте позже.",
        "invalid_input": "Укажите корректный @username или ссылку на канал.",
        "channel_not_found": "Канал не найден.",
    },
    "uz": {
        "greeting": "Salom! Men Telegram kanal statistikasi bilan yordam beraman.",
        "prompt": "@username yoki kanal havolasini yuboring.",
        "history": "So'rovlar tarixi",
        "update": "Yangilash",
        "choose_language": "Выберите язык / Tilni tanlang",
        "no_history": "Tarix bo'sh.",
        "service_error": "Xizmat vaqtincha mavjud emas, keyinroq urinib ko'ring.",
        "invalid_input": "To'g'ri @username yoki kanal havolasini yuboring.",
        "channel_not_found": "Kanal topilmadi.",
    },
}


def format_channel_report(data: dict[str, Any], language: str = "ru") -> str:
    name = data.get("title") or data.get("name") or "—"
    username = data.get("username") or data.get("chat") or "—"
    category = data.get("category") or data.get("category_name") or "—"
    lang = data.get("language") or "—"
    subscribers = data.get("members_count") or data.get("subscribers")
    avg_views = data.get("avg_post_reach") or data.get("avgReach")
    er = data.get("er") or data.get("er_view")
    created_at = data.get("created_at") or data.get("creation_date")

    if isinstance(created_at, str):
        try:
            created_dt = datetime.fromisoformat(created_at)
            created_at = created_dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    lines = [
        "📊 Отчет по каналу" if language == "ru" else "📊 Kanal hisobot", 
        f"Название: {name}",
        f"Username: @{username}" if username != "—" and not username.startswith("@") else f"Username: {username}",
        f"Категория: {category}" if language == "ru" else f"Kategoriya: {category}",
        f"Язык: {lang}" if language == "ru" else f"Til: {lang}",
        f"Подписчики: {subscribers if subscribers is not None else '—'}" if language == "ru" else f"Obunachilar: {subscribers if subscribers is not None else '—'}",
        f"Средний охват поста: {avg_views if avg_views is not None else '—'}" if language == "ru" else f"O'rtacha qamrov: {avg_views if avg_views is not None else '—'}",
        f"ER: {er if er is not None else '—'}",
        f"Дата создания: {created_at if created_at is not None else '—'}" if language == "ru" else f"Yaratilgan sana: {created_at if created_at is not None else '—'}",
    ]
    return "\n".join(lines)
