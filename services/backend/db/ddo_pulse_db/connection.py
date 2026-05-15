"""SQLite connection helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from ddo_pulse_db.paths import get_db_path


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    # FastAPI runs teardown of sync generator deps (e.g. get_db) on a thread-pool
    # worker that may differ from the thread that opened the connection.
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
