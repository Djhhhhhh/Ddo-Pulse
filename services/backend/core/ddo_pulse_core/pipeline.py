"""Pipeline orchestration."""

from __future__ import annotations

import json
import logging
import time

from ddo_pulse_core.fetchers import RssFetcher
from ddo_pulse_core.models import normalize_url
from ddo_pulse_db.repository import Database

logger = logging.getLogger(__name__)

RSS_TYPES = frozenset({"rss", "json_feed"})
_fetcher_rss = RssFetcher()


def _get_fetcher(source_type: str):
    if source_type in RSS_TYPES:
        return _fetcher_rss
    raise ValueError(f"Unsupported source type in M1: {source_type}")


def run_once(db: Database | None = None) -> dict[str, int]:
    """
    Fetch all enabled sources and upsert raw_items.
    Returns stats: sources, fetched_entries, new_items, errors.
    """
    own_db = db is None
    database = db or Database()
    job_id = database.record_job_run("running")
    stats = {"sources": 0, "fetched_entries": 0, "new_items": 0, "errors": 0}

    try:
        sources = database.list_sources(enabled_only=True)
        stats["sources"] = len(sources)

        for row in sources:
            source_id = int(row["id"])
            type_ = row["type"]
            url = row["url"]
            config_json = row["config_json"] or "{}"
            try:
                fetcher = _get_fetcher(type_)
                items = fetcher.fetch(source_id, url, config_json)
                stats["fetched_entries"] += len(items)
                for item in items:
                    norm_url = normalize_url(item.url)
                    inserted = database.upsert_raw_item(
                        source_id=source_id,
                        url=norm_url,
                        title=item.title,
                        published_at=item.published_at,
                        content_snippet=item.content_snippet,
                    )
                    if inserted:
                        stats["new_items"] += 1
                time.sleep(1.0)
            except Exception as exc:
                stats["errors"] += 1
                logger.exception("Fetch failed for source %s (%s): %s", source_id, url, exc)

        database.record_job_run("ok", job_id=job_id)
    except Exception as exc:
        database.record_job_run("failed", error=str(exc), job_id=job_id)
        raise
    finally:
        if own_db:
            database.close()

    return stats
