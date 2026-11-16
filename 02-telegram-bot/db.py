"""Хранилище записей на SQLite.

Отдельный модуль, чтобы бот не знал, как именно хранятся данные:
сейчас это SQLite, при росте проекта можно заменить на PostgreSQL.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any

import aiosqlite

DB_PATH = os.getenv("BOOKING_DB", "booking.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS bookings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    username    TEXT,
    name        TEXT NOT NULL,
    phone       TEXT NOT NULL,
    service     TEXT NOT NULL,
    price       INTEGER NOT NULL,
    visit_date  TEXT NOT NULL,
    visit_time  TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active',
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_bookings_date ON bookings (visit_date);
CREATE UNIQUE INDEX IF NOT EXISTS idx_bookings_slot
    ON bookings (visit_date, visit_time)
    WHERE status = 'active';
"""


class BookingStore:
    """Асинхронный доступ к базе записей."""

    def __init__(self, path: str = DB_PATH) -> None:
        self.path = path

    async def init(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(SCHEMA)
            await db.commit()

    async def add(
        self,
        *,
        user_id: int,
        username: str | None,
        name: str,
        phone: str,
        service: str,
        price: int,
        visit_date: str,
        visit_time: str,
    ) -> int:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                INSERT INTO bookings
                    (user_id, username, name, phone, service, price,
                     visit_date, visit_time, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    name,
                    phone,
                    service,
                    price,
                    visit_date,
                    visit_time,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            await db.commit()
            return int(cursor.lastrowid or 0)

    async def booked_times(self, visit_date: str) -> set[str]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "SELECT visit_time FROM bookings WHERE visit_date = ? AND status = 'active'",
                (visit_date,),
            )
            rows = await cursor.fetchall()
            return {row[0] for row in rows}

    async def by_user(self, user_id: int) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM bookings
                WHERE user_id = ? AND status = 'active' AND visit_date >= ?
                ORDER BY visit_date, visit_time
                """,
                (user_id, date.today().isoformat()),
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def by_date(self, visit_date: str) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM bookings WHERE visit_date = ? AND status = 'active' "
                "ORDER BY visit_time",
                (visit_date,),
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def cancel(self, booking_id: int, user_id: int) -> bool:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "UPDATE bookings SET status = 'cancelled' "
                "WHERE id = ? AND user_id = ? AND status = 'active'",
                (booking_id, user_id),
            )
            await db.commit()
            return cursor.rowcount > 0
