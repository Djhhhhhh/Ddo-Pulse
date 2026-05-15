"""SQLite repository for Ddo-Pulse."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ddo_pulse_db.connection import connect
from ddo_pulse_db.paths import ensure_data_dir, get_db_path

_SCHEMA_FILE = Path(__file__).resolve().parent.parent / "schema.sql"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Database:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or get_db_path()
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = connect(self.db_path)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def init_schema(self) -> None:
        ensure_data_dir()
        sql = _SCHEMA_FILE.read_text(encoding="utf-8")
        self.conn.executescript(sql)
        self.conn.commit()

    def add_source(
        self,
        name: str,
        type_: str,
        url: str,
        config_json: str = "{}",
        enabled: bool = True,
        fetch_cron: str | None = None,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO sources (name, type, url, config_json, enabled, fetch_cron, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                type_,
                url,
                config_json,
                1 if enabled else 0,
                fetch_cron,
                _utc_now_iso(),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_sources(self, enabled_only: bool = False) -> list[sqlite3.Row]:
        if enabled_only:
            rows = self.conn.execute(
                "SELECT * FROM sources WHERE enabled = 1 ORDER BY id"
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM sources ORDER BY id").fetchall()
        return list(rows)

    def get_source(self, source_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM sources WHERE id = ?", (source_id,)
        ).fetchone()

    def delete_source(self, source_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def set_source_enabled(self, source_id: int, enabled: bool) -> bool:
        cur = self.conn.execute(
            "UPDATE sources SET enabled = ? WHERE id = ?",
            (1 if enabled else 0, source_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def upsert_raw_item(
        self,
        source_id: int,
        url: str,
        title: str,
        published_at: str | None,
        content_snippet: str,
        fetched_at: str | None = None,
    ) -> bool:
        """Insert if url is new. Returns True if inserted."""
        fetched = fetched_at or _utc_now_iso()
        cur = self.conn.execute(
            """
            INSERT OR IGNORE INTO raw_items
            (source_id, url, title, published_at, content_snippet, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (source_id, url, title, published_at, content_snippet, fetched),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def count_raw_items(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS c FROM raw_items").fetchone()
        return int(row["c"]) if row else 0

    def set_app_setting(self, key: str, value: str) -> None:
        self.conn.execute(
            """
            INSERT INTO app_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        self.conn.commit()

    def get_app_setting(self, key: str) -> str | None:
        row = self.conn.execute(
            "SELECT value FROM app_settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def import_sources_from_yaml(self, sources: list[dict[str, Any]]) -> int:
        count = 0
        for s in sources:
            name = s.get("name")
            type_ = s.get("type")
            url = s.get("url")
            if not name or not type_ or not url:
                continue
            enabled = s.get("enabled", True)
            config = s.get("config") or s.get("config_json") or {}
            if isinstance(config, str):
                config_json = config
            else:
                config_json = json.dumps(config, ensure_ascii=False)
            self.add_source(
                name=str(name),
                type_=str(type_),
                url=str(url),
                config_json=config_json,
                enabled=bool(enabled),
                fetch_cron=s.get("fetch_cron"),
            )
            count += 1
        return count

    def record_job_run(
        self, status: str, error: str | None = None, job_id: int | None = None
    ) -> int:
        now = _utc_now_iso()
        if job_id is None:
            cur = self.conn.execute(
                """
                INSERT INTO job_runs (started_at, status) VALUES (?, ?)
                """,
                (now, status),
            )
            self.conn.commit()
            return int(cur.lastrowid)
        self.conn.execute(
            """
            UPDATE job_runs SET finished_at = ?, status = ?, error = ? WHERE id = ?
            """,
            (now, status, error, job_id),
        )
        self.conn.commit()
        return job_id
