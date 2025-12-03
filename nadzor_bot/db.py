import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

DB_PATH = Path(__file__).resolve().parent / "data.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_user_id INTEGER,
                tg_username TEXT,
                name TEXT,
                phone TEXT,
                district TEXT,
                address TEXT,
                area TEXT,
                comment TEXT,
                status TEXT,
                created_at TEXT
            )
            """
        )
        conn.commit()


def add_request(
    *,
    tg_user_id: int,
    tg_username: Optional[str],
    name: str,
    phone: str,
    district: str,
    address: str,
    area: str,
    comment: str,
    status: str = "NEW",
) -> int:
    created_at = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO requests (
                tg_user_id, tg_username, name, phone, district, address, area, comment, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tg_user_id,
                tg_username,
                name,
                phone,
                district,
                address,
                area,
                comment,
                status,
                created_at,
            ),
        )
        conn.commit()
        request_id = cursor.lastrowid
    logging.info("Request created: %s", request_id)
    return int(request_id)


def get_request(request_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM requests WHERE id = ?",
            (request_id,),
        )
        return cursor.fetchone()


def get_last_requests(limit: int = 10) -> Iterable[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM requests ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return cursor.fetchall()


def update_request_status(request_id: int, status: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE requests SET status = ? WHERE id = ?",
            (status, request_id),
        )
        conn.commit()
        updated = cursor.rowcount > 0
    if updated:
        logging.info("Request %s status updated to %s", request_id, status)
    return updated
