"""Persistent per-user delivery history."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class HistoryStore:
    def __init__(self, path: str | Path = "history.sqlite3") -> None:
        self.path = Path(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS delivered_releases (
                    user_id INTEGER NOT NULL,
                    release_url TEXT NOT NULL,
                    delivered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, release_url)
                )
                """
            )

    def urls_for_user(self, user_id: int) -> set[str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT release_url FROM delivered_releases WHERE user_id = ?",
                (user_id,),
            )
            return {row[0] for row in rows}

    def add(self, user_id: int, release_url: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO delivered_releases (user_id, release_url)
                VALUES (?, ?)
                """,
                (user_id, release_url),
            )

    def clear_user(self, user_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM delivered_releases WHERE user_id = ?",
                (user_id,),
            )
