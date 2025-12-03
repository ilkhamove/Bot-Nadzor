from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserSettings:
    chat_id: int
    language: str


@dataclass
class HistoryRecord:
    id: int
    chat_id: int
    channel_username: str
    subscribers: int | None
    engagement_rate: float | None
    created_at: datetime
