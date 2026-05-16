"""SQLite repository for Ddo-Pulse."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from ddo_pulse_db.connection import connect
from ddo_pulse_db.datetime_util import storage_cutoff_iso, storage_now_iso
from ddo_pulse_db.paths import ensure_data_dir, get_db_path

_SCHEMA_FILE = Path(__file__).resolve().parent.parent / "schema.sql"

_MISSING = object()


class Database:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or get_db_path()
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = connect(self.db_path)
            self._migrate_pipeline_jobs_feishu_webhook()
            self._migrate_analyzed_items_push_read()
        return self._conn

    def _migrate_analyzed_items_push_read(self) -> None:
        tbl = self._conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='analyzed_items'"
        ).fetchone()
        if tbl is None:
            return
        rows = self._conn.execute("PRAGMA table_info(analyzed_items)").fetchall()
        names = {str(r[1]) for r in rows}
        if "pushed_at" not in names:
            self._conn.execute("ALTER TABLE analyzed_items ADD COLUMN pushed_at TEXT")
        if "read_at" not in names:
            self._conn.execute("ALTER TABLE analyzed_items ADD COLUMN read_at TEXT")
        self._conn.commit()

    def _migrate_pipeline_jobs_feishu_webhook(self) -> None:
        # Runs on every new connection. Skip until schema exists (init_schema uses
        # executescript after first conn open — table may not exist yet).
        tbl = self._conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='pipeline_jobs'"
        ).fetchone()
        if tbl is None:
            return
        rows = self._conn.execute("PRAGMA table_info(pipeline_jobs)").fetchall()
        names = {str(r[1]) for r in rows}
        if "feishu_webhook_url" in names:
            return
        self._conn.execute(
            "ALTER TABLE pipeline_jobs ADD COLUMN feishu_webhook_url TEXT NOT NULL DEFAULT ''"
        )
        self._conn.commit()

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
        job_id: int,
        name: str,
        type_: str,
        url: str,
        config_json: str = "{}",
        enabled: bool = True,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO sources (job_id, name, type, url, config_json, enabled, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                name,
                type_,
                url,
                config_json,
                1 if enabled else 0,
                storage_now_iso(),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_sources(
        self, enabled_only: bool = False, job_id: int | None = None
    ) -> list[sqlite3.Row]:
        clauses: list[str] = []
        params: list[Any] = []
        if enabled_only:
            clauses.append("enabled = 1")
        if job_id is not None:
            clauses.append("job_id = ?")
            params.append(job_id)
        where = " AND ".join(clauses) if clauses else "1=1"
        rows = self.conn.execute(
            f"SELECT * FROM sources WHERE {where} ORDER BY id", params
        ).fetchall()
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

    def update_source(
        self,
        source_id: int,
        *,
        job_id: int | None = None,
        name: str | None = None,
        type_: str | None = None,
        url: str | None = None,
        config_json: str | None = None,
        enabled: bool | None = None,
    ) -> bool:
        row = self.get_source(source_id)
        if not row:
            return False
        self.conn.execute(
            """
            UPDATE sources
            SET job_id = ?, name = ?, type = ?, url = ?, config_json = ?, enabled = ?
            WHERE id = ?
            """,
            (
                job_id if job_id is not None else row["job_id"],
                name if name is not None else row["name"],
                type_ if type_ is not None else row["type"],
                url if url is not None else row["url"],
                config_json if config_json is not None else row["config_json"],
                (1 if enabled else 0) if enabled is not None else row["enabled"],
                source_id,
            ),
        )
        self.conn.commit()
        return True

    def count_sources(self, enabled_only: bool = False) -> int:
        if enabled_only:
            sql = "SELECT COUNT(*) AS c FROM sources WHERE enabled = 1"
        else:
            sql = "SELECT COUNT(*) AS c FROM sources"
        row = self.conn.execute(sql).fetchone()
        return int(row["c"]) if row else 0

    def count_unanalyzed_raw_items(self) -> int:
        row = self.conn.execute(
            """
            SELECT COUNT(*) AS c FROM raw_items r
            LEFT JOIN analyzed_items a ON a.raw_item_id = r.id
            WHERE a.id IS NULL
            """
        ).fetchone()
        return int(row["c"]) if row else 0

    def count_quality_items(self, score_threshold: int | None = None) -> int:
        threshold = score_threshold
        if threshold is None:
            profile = self.get_default_llm_profile()
            threshold = int(profile["score_threshold"]) if profile else 7
        row = self.conn.execute(
            """
            SELECT COUNT(*) AS c FROM analyzed_items
            WHERE is_quality = 1 AND score >= ?
            """,
            (threshold,),
        ).fetchone()
        return int(row["c"]) if row else 0

    def get_last_job_run(self) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM job_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()

    def list_analyzed_items_page(
        self,
        *,
        days: int = 30,
        min_score: int | None = None,
        source_id: int | None = None,
        category: str | None = None,
        title_q: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[sqlite3.Row], int]:
        since = storage_cutoff_iso(days)
        clauses = ["a.analyzed_at >= ?"]
        params: list[Any] = [since]
        if min_score is not None:
            clauses.append("a.score >= ?")
            params.append(min_score)
        if source_id is not None:
            clauses.append("r.source_id = ?")
            params.append(source_id)
        if category:
            clauses.append(
                "EXISTS (SELECT 1 FROM json_each(a.categories_json) "
                "WHERE json_each.value = ?)"
            )
            params.append(category)
        if title_q:
            clauses.append("(r.title LIKE ? ESCAPE '\\')")
            escaped = title_q.replace("%", "\\%").replace("_", "\\_")
            params.append(f"%{escaped}%")
        where = " AND ".join(clauses)
        count_row = self.conn.execute(
            f"""
            SELECT COUNT(*) AS c
            FROM analyzed_items a
            INNER JOIN raw_items r ON r.id = a.raw_item_id
            WHERE {where}
            """,
            params,
        ).fetchone()
        total = int(count_row["c"]) if count_row else 0
        params.extend([int(limit), int(offset)])
        rows = self.conn.execute(
            f"""
            SELECT
                a.id, a.raw_item_id, a.profile_id, a.is_quality, a.score,
                a.categories_json, a.summary_zh, a.reason, a.analyzed_at,
                a.pushed_at, a.read_at,
                r.title, r.url, r.source_id, r.published_at
            FROM analyzed_items a
            INNER JOIN raw_items r ON r.id = a.raw_item_id
            WHERE {where}
            ORDER BY a.score IS NULL, a.score DESC, a.analyzed_at DESC
            LIMIT ? OFFSET ?
            """,
            params,
        ).fetchall()
        return list(rows), total

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
        fetched = fetched_at or storage_now_iso()
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

    def count_analyzed_items(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS c FROM analyzed_items").fetchone()
        return int(row["c"]) if row else 0

    def count_read_items(self) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS c FROM analyzed_items WHERE read_at IS NOT NULL"
        ).fetchone()
        return int(row["c"]) if row else 0

    def add_llm_profile(
        self,
        name: str,
        model: str,
        api_key: str = "",
        *,
        provider: str = "openrouter",
        base_url: str = "https://openrouter.ai/api/v1",
        site_url: str | None = None,
        app_title: str | None = "Ddo-Pulse",
        temperature: float = 0.3,
        max_tokens: int = 1024,
        prompt_template: str | None = None,
        system_prompt: str | None = None,
        score_threshold: int = 7,
        category_hints: str | list[str] | None = None,
        is_default: bool = False,
    ) -> int:
        if isinstance(category_hints, list):
            hints_json = json.dumps(category_hints, ensure_ascii=False)
        elif category_hints:
            hints_json = category_hints
        else:
            hints_json = "[]"

        if is_default:
            self.conn.execute("UPDATE llm_profiles SET is_default = 0")

        cur = self.conn.execute(
            """
            INSERT INTO llm_profiles (
                name, provider, base_url, model, api_key, site_url, app_title,
                temperature, max_tokens, prompt_template, system_prompt, score_threshold,
                category_hints, is_default
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                provider,
                base_url,
                model,
                api_key,
                site_url,
                app_title,
                temperature,
                max_tokens,
                prompt_template,
                system_prompt,
                score_threshold,
                hints_json,
                1 if is_default else 0,
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_llm_profiles(self) -> list[sqlite3.Row]:
        rows = self.conn.execute(
            "SELECT * FROM llm_profiles ORDER BY is_default DESC, id"
        ).fetchall()
        return list(rows)

    def get_llm_profile(self, profile_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM llm_profiles WHERE id = ?", (profile_id,)
        ).fetchone()

    def get_llm_profile_by_name(self, name: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM llm_profiles WHERE name = ?", (name,)
        ).fetchone()

    def upsert_llm_profile(
        self,
        name: str,
        model: str,
        api_key: str = "",
        *,
        provider: str = "openrouter",
        base_url: str = "https://openrouter.ai/api/v1",
        site_url: str | None = None,
        app_title: str | None = "Ddo-Pulse",
        temperature: float = 0.3,
        max_tokens: int = 1024,
        prompt_template: str | None = None,
        system_prompt: str | None = None,
        score_threshold: int = 7,
        category_hints: str | list[str] | None = None,
        is_default: bool = False,
        preserve_api_key_if_empty: bool = True,
    ) -> int:
        """Insert or update profile by unique name."""
        existing = self.get_llm_profile_by_name(name)
        key = api_key
        if preserve_api_key_if_empty and existing and not (key or "").strip():
            key = existing["api_key"] or ""

        if isinstance(category_hints, list):
            hints_json = json.dumps(category_hints, ensure_ascii=False)
        elif category_hints:
            hints_json = category_hints
        else:
            hints_json = "[]"

        if is_default:
            self.conn.execute("UPDATE llm_profiles SET is_default = 0")

        if existing:
            self.conn.execute(
                """
                UPDATE llm_profiles SET
                    provider = ?, base_url = ?, model = ?, api_key = ?,
                    site_url = ?, app_title = ?, temperature = ?, max_tokens = ?,
                    prompt_template = ?, system_prompt = ?, score_threshold = ?, category_hints = ?,
                    is_default = ?
                WHERE name = ?
                """,
                (
                    provider,
                    base_url,
                    model,
                    key,
                    site_url,
                    app_title,
                    temperature,
                    max_tokens,
                    prompt_template,
                    system_prompt,
                    score_threshold,
                    hints_json,
                    1 if is_default else 0,
                    name,
                ),
            )
            self.conn.commit()
            return int(existing["id"])

        return self.add_llm_profile(
            name=name,
            model=model,
            api_key=key,
            provider=provider,
            base_url=base_url,
            site_url=site_url,
            app_title=app_title,
            temperature=temperature,
            max_tokens=max_tokens,
            prompt_template=prompt_template,
            system_prompt=system_prompt,
            score_threshold=score_threshold,
            category_hints=hints_json,
            is_default=is_default,
        )

    def get_default_llm_profile(self) -> sqlite3.Row | None:
        row = self.conn.execute(
            "SELECT * FROM llm_profiles WHERE is_default = 1 ORDER BY id LIMIT 1"
        ).fetchone()
        if row:
            return row
        return self.conn.execute(
            "SELECT * FROM llm_profiles ORDER BY id LIMIT 1"
        ).fetchone()

    def set_default_llm_profile(self, profile_id: int) -> bool:
        if not self.get_llm_profile(profile_id):
            return False
        self.conn.execute("UPDATE llm_profiles SET is_default = 0")
        self.conn.execute(
            "UPDATE llm_profiles SET is_default = 1 WHERE id = ?", (profile_id,)
        )
        self.conn.commit()
        return True

    def update_llm_profile(
        self,
        profile_id: int,
        *,
        api_key: str | None = None,
        model: str | None = None,
        score_threshold: int | None = None,
        prompt_template: str | None = None,
        system_prompt: str | None = None,
        category_hints: str | list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> bool:
        row = self.get_llm_profile(profile_id)
        if not row:
            return False
        hints_val = row["category_hints"]
        if category_hints is not None:
            if isinstance(category_hints, list):
                hints_val = json.dumps(category_hints, ensure_ascii=False)
            else:
                hints_val = category_hints
        self.conn.execute(
            """
            UPDATE llm_profiles
            SET api_key = ?, model = ?, score_threshold = ?,
                prompt_template = ?, system_prompt = ?, category_hints = ?,
                temperature = ?, max_tokens = ?
            WHERE id = ?
            """,
            (
                api_key if api_key is not None else row["api_key"],
                model if model is not None else row["model"],
                score_threshold
                if score_threshold is not None
                else row["score_threshold"],
                prompt_template
                if prompt_template is not None
                else row["prompt_template"],
                system_prompt
                if system_prompt is not None
                else row["system_prompt"],
                hints_val,
                float(temperature)
                if temperature is not None
                else row["temperature"],
                int(max_tokens) if max_tokens is not None else row["max_tokens"],
                profile_id,
            ),
        )
        self.conn.commit()
        return True

    def import_llm_profiles_from_yaml(
        self, profiles: list[dict[str, Any]], default_name: str | None = None
    ) -> int:
        if not profiles:
            return 0
        default_name = default_name or "default"
        default_idx = 0
        for idx, p in enumerate(profiles):
            if p.get("is_default") or p.get("name") == default_name:
                default_idx = idx
                break
        count = 0
        for idx, p in enumerate(profiles):
            name = p.get("name")
            model = p.get("model")
            if not name or not model:
                continue
            hints = p.get("category_hints")
            if isinstance(hints, list):
                hints_json = json.dumps(hints, ensure_ascii=False)
            elif hints:
                hints_json = str(hints)
            else:
                hints_json = "[]"
            is_default = idx == default_idx
            self.upsert_llm_profile(
                name=str(name),
                model=str(model),
                api_key=str(p.get("api_key") or ""),
                provider=str(p.get("provider") or "openrouter"),
                base_url=str(p.get("base_url") or "https://openrouter.ai/api/v1"),
                site_url=p.get("site_url"),
                app_title=p.get("app_title"),
                temperature=float(p.get("temperature", 0.3)),
                max_tokens=int(p.get("max_tokens", 1024)),
                prompt_template=p.get("prompt_template"),
                system_prompt=p.get("system_prompt"),
                score_threshold=int(p.get("score_threshold", 7)),
                category_hints=hints_json,
                is_default=is_default,
            )
            count += 1
        return count

    def ensure_default_profile_from_dict(self, profile: dict[str, Any]) -> int:
        existing = self.list_llm_profiles()
        if existing:
            return int(existing[0]["id"])
        return self.add_llm_profile(
            name=str(profile.get("name") or "default"),
            model=str(profile.get("model") or "openai/gpt-4o-mini"),
            api_key=str(profile.get("api_key") or ""),
            provider=str(profile.get("provider") or "openrouter"),
            base_url=str(profile.get("base_url") or "https://openrouter.ai/api/v1"),
            site_url=profile.get("site_url"),
            app_title=profile.get("app_title"),
            temperature=float(profile.get("temperature", 0.3)),
            max_tokens=int(profile.get("max_tokens", 1024)),
            prompt_template=profile.get("prompt_template"),
            system_prompt=profile.get("system_prompt"),
            score_threshold=int(profile.get("score_threshold", 7)),
            category_hints=profile.get("category_hints") or ["AI", "工程", "产品", "安全"],
            is_default=True,
        )

    def list_unanalyzed_raw_items(
        self,
        limit: int | None = 50,
        source_ids: list[int] | None = None,
    ) -> list[sqlite3.Row]:
        if source_ids is not None and len(source_ids) == 0:
            return []
        clause = "a.id IS NULL"
        params: list[Any] = []
        if source_ids:
            placeholders = ",".join("?" * len(source_ids))
            clause += f" AND r.source_id IN ({placeholders})"
            params.extend(source_ids)
        sql = f"""
            SELECT r.*
            FROM raw_items r
            LEFT JOIN analyzed_items a ON a.raw_item_id = r.id
            WHERE {clause}
            ORDER BY r.fetched_at ASC
        """
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        return list(self.conn.execute(sql, params).fetchall())

    def insert_analyzed_item(
        self,
        raw_item_id: int,
        profile_id: int,
        is_quality: bool,
        score: int,
        categories_json: str,
        summary_zh: str,
        reason: str,
        analyzed_at: str | None = None,
    ) -> int:
        analyzed = analyzed_at or storage_now_iso()
        cur = self.conn.execute(
            """
            INSERT INTO analyzed_items (
                raw_item_id, profile_id, is_quality, score, categories_json,
                summary_zh, reason, analyzed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                raw_item_id,
                profile_id,
                1 if is_quality else 0,
                score,
                categories_json,
                summary_zh,
                reason,
                analyzed,
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_analyzed_items_recent(
        self,
        days: int = 7,
        *,
        min_score: int | None = None,
        limit: int = 100,
    ) -> list[sqlite3.Row]:
        since = storage_cutoff_iso(days)
        clauses = ["a.analyzed_at >= ?"]
        params: list[Any] = [since]
        if min_score is not None:
            clauses.append("a.score >= ?")
            params.append(min_score)
        params.append(int(limit))
        sql = f"""
            SELECT
                a.id, a.raw_item_id, a.profile_id, a.is_quality, a.score,
                a.categories_json, a.summary_zh, a.reason, a.analyzed_at,
                r.title, r.url, r.source_id, r.published_at
            FROM analyzed_items a
            INNER JOIN raw_items r ON r.id = a.raw_item_id
            WHERE {" AND ".join(clauses)}
            ORDER BY a.analyzed_at DESC
            LIMIT ?
        """
        return list(self.conn.execute(sql, params).fetchall())

    def list_analyzed_items(
        self,
        limit: int = 20,
        *,
        min_score: int | None = None,
        quality_only: bool = False,
    ) -> list[sqlite3.Row]:
        clauses = ["1=1"]
        params: list[Any] = []
        if min_score is not None:
            clauses.append("a.score >= ?")
            params.append(min_score)
        if quality_only:
            clauses.append("a.is_quality = 1")
        params.append(int(limit))
        sql = f"""
            SELECT
                a.id, a.raw_item_id, a.profile_id, a.is_quality, a.score,
                a.categories_json, a.summary_zh, a.reason, a.analyzed_at,
                r.title, r.url, r.source_id, r.published_at
            FROM analyzed_items a
            INNER JOIN raw_items r ON r.id = a.raw_item_id
            WHERE {" AND ".join(clauses)}
            ORDER BY a.analyzed_at DESC
            LIMIT ?
        """
        return list(self.conn.execute(sql, params).fetchall())

    def get_analyzed_item(self, analyzed_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            """
            SELECT
                a.id, a.raw_item_id, a.profile_id, a.is_quality, a.score,
                a.categories_json, a.summary_zh, a.reason, a.analyzed_at,
                a.pushed_at, a.read_at,
                r.title, r.url, r.source_id, r.published_at
            FROM analyzed_items a
            INNER JOIN raw_items r ON r.id = a.raw_item_id
            WHERE a.id = ?
            """,
            (analyzed_id,),
        ).fetchone()

    def mark_articles_pushed(self, analyzed_ids: list[int]) -> int:
        if not analyzed_ids:
            return 0
        now = storage_now_iso()
        placeholders = ",".join("?" * len(analyzed_ids))
        cur = self.conn.execute(
            f"""
            UPDATE analyzed_items
            SET pushed_at = ?, read_at = COALESCE(read_at, ?)
            WHERE id IN ({placeholders}) AND pushed_at IS NULL
            """,
            [now, now, *analyzed_ids],
        )
        self.conn.commit()
        return int(cur.rowcount)

    def mark_article_read(self, analyzed_id: int) -> bool:
        now = storage_now_iso()
        cur = self.conn.execute(
            """
            UPDATE analyzed_items
            SET read_at = COALESCE(read_at, ?)
            WHERE id = ?
            """,
            (now, analyzed_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def mark_article_unread(self, analyzed_id: int) -> bool:
        cur = self.conn.execute(
            """
            UPDATE analyzed_items
            SET read_at = NULL
            WHERE id = ?
            """,
            (analyzed_id,),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def list_analyzed_items_by_ids(self, analyzed_ids: list[int]) -> list[sqlite3.Row]:
        if not analyzed_ids:
            return []
        placeholders = ",".join("?" * len(analyzed_ids))
        return list(
            self.conn.execute(
                f"""
                SELECT
                    a.id, a.raw_item_id, a.is_quality, a.score,
                    a.categories_json, a.summary_zh, a.reason, a.analyzed_at,
                    a.pushed_at, a.read_at,
                    r.title, r.url
                FROM analyzed_items a
                INNER JOIN raw_items r ON r.id = a.raw_item_id
                WHERE a.id IN ({placeholders})
                ORDER BY a.score IS NULL, a.score DESC, a.analyzed_at DESC
                """,
                analyzed_ids,
            ).fetchall()
        )

    def list_digest_candidates(
        self,
        score_threshold: int,
        limit: int = 8,
        source_ids: list[int] | None = None,
        *,
        exclude_pushed: bool = True,
    ) -> list[sqlite3.Row]:
        if source_ids is not None and len(source_ids) == 0:
            return []
        clause = "a.is_quality = 1 AND a.score >= ?"
        params: list[Any] = [score_threshold]
        if exclude_pushed:
            clause += " AND a.pushed_at IS NULL"
        if source_ids:
            placeholders = ",".join("?" * len(source_ids))
            clause += f" AND r.source_id IN ({placeholders})"
            params.extend(source_ids)
        params.append(int(limit))
        return list(
            self.conn.execute(
                f"""
                SELECT
                    a.id, a.raw_item_id, a.is_quality, a.score,
                    a.categories_json, a.summary_zh, a.reason, a.analyzed_at,
                    a.pushed_at, a.read_at,
                    r.title, r.url
                FROM analyzed_items a
                INNER JOIN raw_items r ON r.id = a.raw_item_id
                WHERE {clause}
                ORDER BY a.score IS NULL, a.score DESC, a.analyzed_at DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        )

    def merged_digest_item_ids(
        self, job_id: int, date: str, new_ids: list[int]
    ) -> list[int]:
        """Return existing digest item ids for (job, date) plus new ids, de-duplicated."""
        existing = self.get_digest_by_date_and_job(date, job_id)
        merged: list[int] = []
        seen: set[int] = set()
        if existing:
            try:
                for raw_id in json.loads(existing["item_ids_json"] or "[]"):
                    iid = int(raw_id)
                    if iid not in seen:
                        seen.add(iid)
                        merged.append(iid)
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        for iid in new_ids:
            if iid not in seen:
                seen.add(iid)
                merged.append(iid)
        return merged

    def get_digest_by_date_and_job(self, date: str, job_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM digests WHERE date = ? AND job_id = ?", (date, job_id)
        ).fetchone()

    def get_digest_by_id(self, digest_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM digests WHERE id = ?", (digest_id,)
        ).fetchone()

    def upsert_digest(
        self,
        job_id: int,
        date: str,
        item_ids_json: str,
        markdown_body: str,
    ) -> int:
        existing = self.get_digest_by_date_and_job(date, job_id)
        now = storage_now_iso()
        if existing:
            self.conn.execute(
                """
                UPDATE digests
                SET item_ids_json = ?, markdown_body = ?, created_at = ?
                WHERE date = ? AND job_id = ?
                """,
                (item_ids_json, markdown_body, now, date, job_id),
            )
            self.conn.commit()
            return int(existing["id"])
        cur = self.conn.execute(
            """
            INSERT INTO digests (job_id, date, item_ids_json, markdown_body, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (job_id, date, item_ids_json, markdown_body, now),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_article_categories(self, days: int = 365) -> list[str]:
        since = storage_cutoff_iso(days)
        rows = self.conn.execute(
            """
            SELECT DISTINCT j.value AS cat
            FROM analyzed_items a,
                 json_each(a.categories_json) AS j
            WHERE a.analyzed_at >= ? AND j.value IS NOT NULL AND TRIM(j.value) != ''
            ORDER BY j.value
            """,
            (since,),
        ).fetchall()
        return [str(r["cat"]) for r in rows]

    def has_successful_push(self, digest_id: int) -> bool:
        row = self.conn.execute(
            """
            SELECT 1 FROM push_logs
            WHERE digest_id = ? AND channel = 'feishu' AND status = 'ok'
            LIMIT 1
            """,
            (digest_id,),
        ).fetchone()
        return row is not None

    def insert_push_log(
        self,
        digest_id: int,
        status: str,
        response: str | None = None,
        channel: str = "feishu",
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO push_logs (digest_id, channel, status, response, pushed_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (digest_id, channel, status, response, storage_now_iso()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def sync_settings_from_yaml(self, data: dict[str, Any]) -> None:
        feishu = data.get("feishu") or {}
        webhook = feishu.get("webhook_url")
        if webhook is not None:
            self.set_app_setting("feishu.webhook_url", str(webhook))

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
        default_jid = self.get_first_pipeline_job_id()
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
            job_id = (
                int(s["job_id"]) if s.get("job_id") is not None else default_jid
            )
            if job_id is None:
                continue
            self.add_source(
                job_id=job_id,
                name=str(name),
                type_=str(type_),
                url=str(url),
                config_json=config_json,
                enabled=bool(enabled),
            )
            count += 1
        return count

    def get_first_pipeline_job_id(self) -> int | None:
        """First pipeline job id, or None if there are no jobs (no auto-insert)."""
        row = self.conn.execute(
            "SELECT id FROM pipeline_jobs ORDER BY id LIMIT 1"
        ).fetchone()
        return int(row["id"]) if row else None

    def list_pipeline_jobs(self) -> list[sqlite3.Row]:
        return list(
            self.conn.execute(
                "SELECT * FROM pipeline_jobs ORDER BY id"
            ).fetchall()
        )

    def get_pipeline_job(self, job_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM pipeline_jobs WHERE id = ?", (job_id,)
        ).fetchone()

    def add_pipeline_job(
        self,
        name: str,
        *,
        schedule_cron: str = "0 8 * * *",
        enabled: bool = True,
        analyze_limit: int = 50,
        digest_top_n: int = 8,
        push_digest: bool = False,
        score_threshold: int = 7,
        interest_keywords_json: str = "[]",
        keyword_prefilter: bool = False,
        prompt_template: str | None = None,
        scoring_rubric: str | None = None,
        system_prompt: str | None = None,
        llm_profile_id: int | None = None,
        feishu_webhook_url: str | None = None,
    ) -> int:
        now = storage_now_iso()
        webhook = (feishu_webhook_url or "").strip()
        cur = self.conn.execute(
            """
            INSERT INTO pipeline_jobs (
                name, enabled, schedule_cron, analyze_limit, digest_top_n, push_digest,
                score_threshold, interest_keywords_json, keyword_prefilter,
                prompt_template, scoring_rubric, system_prompt, llm_profile_id,
                feishu_webhook_url, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                1 if enabled else 0,
                schedule_cron,
                analyze_limit,
                digest_top_n,
                1 if push_digest else 0,
                score_threshold,
                interest_keywords_json,
                1 if keyword_prefilter else 0,
                prompt_template,
                scoring_rubric,
                system_prompt,
                llm_profile_id,
                webhook,
                now,
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_pipeline_job(
        self,
        job_id: int,
        *,
        name: str | None = None,
        schedule_cron: str | None = None,
        enabled: bool | None = None,
        analyze_limit: int | None = None,
        digest_top_n: int | None = None,
        push_digest: bool | None = None,
        score_threshold: int | None = None,
        interest_keywords_json: str | None = None,
        keyword_prefilter: bool | None = None,
        prompt_template: Any = _MISSING,
        scoring_rubric: Any = _MISSING,
        system_prompt: Any = _MISSING,
        llm_profile_id: Any = _MISSING,
        feishu_webhook_url: Any = _MISSING,
    ) -> bool:
        row = self.get_pipeline_job(job_id)
        if not row:
            return False
        new_prompt = (
            row["prompt_template"]
            if prompt_template is _MISSING
            else prompt_template
        )
        new_rubric = (
            row["scoring_rubric"]
            if scoring_rubric is _MISSING
            else scoring_rubric
        )
        new_system = (
            row["system_prompt"]
            if system_prompt is _MISSING
            else system_prompt
        )
        new_llm = (
            row["llm_profile_id"]
            if llm_profile_id is _MISSING
            else llm_profile_id
        )
        new_wh = (
            row["feishu_webhook_url"]
            if feishu_webhook_url is _MISSING
            else feishu_webhook_url
        )
        self.conn.execute(
            """
            UPDATE pipeline_jobs SET
                name = ?, schedule_cron = ?, enabled = ?, analyze_limit = ?,
                digest_top_n = ?, push_digest = ?, score_threshold = ?,
                interest_keywords_json = ?, keyword_prefilter = ?,
                prompt_template = ?, scoring_rubric = ?, system_prompt = ?,
                llm_profile_id = ?, feishu_webhook_url = ?
            WHERE id = ?
            """,
            (
                name if name is not None else row["name"],
                schedule_cron if schedule_cron is not None else row["schedule_cron"],
                (1 if enabled else 0) if enabled is not None else row["enabled"],
                analyze_limit
                if analyze_limit is not None
                else row["analyze_limit"],
                digest_top_n
                if digest_top_n is not None
                else row["digest_top_n"],
                (1 if push_digest else 0)
                if push_digest is not None
                else row["push_digest"],
                score_threshold
                if score_threshold is not None
                else row["score_threshold"],
                interest_keywords_json
                if interest_keywords_json is not None
                else row["interest_keywords_json"],
                (1 if keyword_prefilter else 0)
                if keyword_prefilter is not None
                else row["keyword_prefilter"],
                new_prompt,
                new_rubric,
                new_system,
                new_llm,
                (new_wh or "").strip(),
                job_id,
            ),
        )
        self.conn.commit()
        return True

    def delete_pipeline_job(self, job_id: int) -> bool:
        self.conn.execute(
            "DELETE FROM job_runs WHERE pipeline_job_id = ?", (job_id,)
        )
        cur = self.conn.execute(
            "DELETE FROM pipeline_jobs WHERE id = ?", (job_id,)
        )
        self.conn.commit()
        return cur.rowcount > 0

    def start_job_run(
        self, *, pipeline_job_id: int | None, trigger: str
    ) -> int:
        now = storage_now_iso()
        cur = self.conn.execute(
            """
            INSERT INTO job_runs (
                started_at, status, pipeline_job_id, trigger
            ) VALUES (?, 'running', ?, ?)
            """,
            (now, pipeline_job_id, trigger),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def finish_job_run(
        self,
        run_id: int,
        status: str,
        *,
        error: str | None = None,
        result_json: str | None = None,
        digest_id: int | None = None,
    ) -> None:
        now = storage_now_iso()
        self.conn.execute(
            """
            UPDATE job_runs
            SET finished_at = ?, status = ?, error = ?,
                result_json = ?, digest_id = ?
            WHERE id = ?
            """,
            (now, status, error, result_json, digest_id, run_id),
        )
        self.conn.commit()

    def list_job_runs(self, *, limit: int = 30, pipeline_job_id: int | None = None) -> list[sqlite3.Row]:
        if pipeline_job_id is None:
            rows = self.conn.execute(
                """
                SELECT j.*, p.name AS pipeline_job_name
                FROM job_runs j
                INNER JOIN pipeline_jobs p ON p.id = j.pipeline_job_id
                ORDER BY j.id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """
                SELECT j.*, p.name AS pipeline_job_name
                FROM job_runs j
                INNER JOIN pipeline_jobs p ON p.id = j.pipeline_job_id
                WHERE j.pipeline_job_id = ?
                ORDER BY j.id DESC
                LIMIT ?
                """,
                (pipeline_job_id, int(limit)),
            ).fetchall()
        return list(rows)

    def get_job_run(self, run_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            """
            SELECT j.*, p.name AS pipeline_job_name
            FROM job_runs j
            LEFT JOIN pipeline_jobs p ON p.id = j.pipeline_job_id
            WHERE j.id = ?
            """,
            (run_id,),
        ).fetchone()

    def record_job_run(
        self, status: str, error: str | None = None, job_id: int | None = None
    ) -> int:
        """Legacy: insert completed row or update in-flight run."""
        now = storage_now_iso()
        if job_id is None:
            cur = self.conn.execute(
                """
                INSERT INTO job_runs (started_at, status, trigger)
                VALUES (?, ?, 'legacy')
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
