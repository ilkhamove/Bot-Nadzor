from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Iterable


class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                chat_id INTEGER PRIMARY KEY,
                language TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                channel_username TEXT NOT NULL,
                subscribers INTEGER,
                engagement_rate REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self._conn.commit()

    def execute(self, query: str, params: Iterable[Any] | None = None) -> sqlite3.Cursor:
        cur = self._conn.cursor()
        cur.execute(query, params or [])
        self._conn.commit()
        return cur

    def fetchone(self, query: str, params: Iterable[Any] | None = None) -> sqlite3.Row | None:
        cur = self._conn.cursor()
        cur.execute(query, params or [])
        return cur.fetchone()

    def fetchall(self, query: str, params: Iterable[Any] | None = None) -> list[sqlite3.Row]:
        cur = self._conn.cursor()
        cur.execute(query, params or [])
        return cur.fetchall()

    def close(self) -> None:
        self._conn.close()


def get_database(db_path: str) -> Database:
    return Database(db_path)
