"""RSS / Atom / JSON Feed fetcher via feedparser."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from ddo_pulse_core.fetchers.base import BaseFetcher
from ddo_pulse_core.models import RawItem, normalize_url

USER_AGENT = "Ddo-Pulse/0.1 (+https://github.com/ddo-pulse)"
TIMEOUT = 30.0


def _entry_published(entry: feedparser.FeedParserDict) -> str | None:
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            try:
                dt = datetime(*parsed[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except (TypeError, ValueError):
                pass
    for key in ("published", "updated"):
        raw = entry.get(key)
        if raw:
            try:
                return parsedate_to_datetime(raw).astimezone(timezone.utc).isoformat()
            except (TypeError, ValueError, OverflowError):
                return str(raw)
    return None


def _entry_snippet(entry: feedparser.FeedParserDict) -> str:
    for key in ("summary", "description", "content"):
        val = entry.get(key)
        if not val:
            continue
        if isinstance(val, list) and val:
            val = val[0].get("value", "")
        if val:
            text = str(val)
            return text[:8000] if len(text) > 8000 else text
    return ""


class RssFetcher(BaseFetcher):
    def fetch(self, source_id: int, url: str, config_json: str) -> list[RawItem]:
        headers = {"User-Agent": USER_AGENT}
        with httpx.Client(timeout=TIMEOUT, headers=headers, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            content = resp.text

        parsed = feedparser.parse(content)
        if parsed.bozo and not parsed.entries:
            raise ValueError(f"Failed to parse feed: {parsed.bozo_exception}")

        items: list[RawItem] = []
        seen: set[str] = set()
        for entry in parsed.entries:
            link = entry.get("link") or entry.get("id")
            if not link:
                continue
            norm = normalize_url(link)
            if norm in seen:
                continue
            seen.add(norm)
            title = (entry.get("title") or "").strip() or norm
            items.append(
                RawItem(
                    source_id=source_id,
                    url=norm,
                    title=title,
                    published_at=_entry_published(entry),
                    content_snippet=_entry_snippet(entry),
                )
            )
        return items
