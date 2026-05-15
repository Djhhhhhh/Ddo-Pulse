"""FastAPI dependencies."""

from __future__ import annotations

from collections.abc import Generator

from ddo_pulse_db.repository import Database


def get_db() -> Generator[Database, None, None]:
    db = Database()
    try:
        yield db
    finally:
        db.close()
