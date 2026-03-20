from __future__ import annotations

import sqlite3
from pathlib import Path


class SqliteStore:
    def __init__(self, path: Path):
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def init_db(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            schema_sql = Path(__file__).with_name("schema.sql").read_text()
            connection.executescript(schema_sql)

    def table_exists(self, name: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                (name,),
            )
            return cursor.fetchone() is not None
