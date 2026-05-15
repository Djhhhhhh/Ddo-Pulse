"""Shared HTML list parsing for html_list and browser_session fetchers."""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from ddo_pulse_core.models import RawItem, normalize_url

logger = logging.getLogger(__name__)

USER_AGENT = "Ddo-Pulse/1.0 (+https://github.com/ddo-pulse)"
REQUIRED_SELECTORS = ("item", "title", "link")


def parse_list_config(config_json: str) -> dict[str, Any]:
    try:
        data = json.loads(config_json or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid config_json: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("config_json must be a JSON object")
    selectors = data.get("selectors")
    if not isinstance(selectors, dict):
        raise ValueError("config_json must include selectors object")
    for key in REQUIRED_SELECTORS:
        if not selectors.get(key):
            raise ValueError(f"selectors.{key} is required")
    return data


def resolve_list_url(source_url: str, config: dict[str, Any]) -> str:
    return str(config.get("list_url") or source_url).strip()


def _parse_selector_spec(spec: str) -> tuple[str, str | None]:
    if "@" in spec:
        css, attr = spec.rsplit("@", 1)
        return css.strip(), attr.strip() or None
    return spec.strip(), None


def _element_field(element: Any, spec: str, base_url: str) -> str:
    css, attr = _parse_selector_spec(spec)
    target = element.select_one(css) if css else element
    if target is None:
        return ""
    if attr:
        if attr == "href":
            raw = target.get("href") or ""
        else:
            raw = target.get(attr) or ""
        if not raw and attr != "text":
            raw = target.get_text(strip=True)
        text = str(raw).strip()
        if attr == "href" and text:
            return urljoin(base_url, text)
        return text
    return target.get_text(" ", strip=True)


def extract_raw_items_from_html(
    html: str,
    *,
    source_id: int,
    base_url: str,
    selectors: dict[str, str],
) -> list[RawItem]:
    soup = BeautifulSoup(html, "lxml")
    items: list[RawItem] = []
    seen: set[str] = set()
    date_spec = selectors.get("date")

    for el in soup.select(selectors["item"]):
        title = _element_field(el, selectors["title"], base_url)
        link = _element_field(el, selectors["link"], base_url)
        if not link:
            continue
        norm = normalize_url(link)
        if norm in seen:
            continue
        seen.add(norm)
        published = _element_field(el, date_spec, base_url) if date_spec else None
        if published == "":
            published = None
        items.append(
            RawItem(
                source_id=source_id,
                url=norm,
                title=title or norm,
                published_at=published,
                content_snippet="",
            )
        )
    return items


def find_rss_alternate_url(html: str, base_url: str) -> str | None:
    """Return RSS/Atom alternate link if present (for user hint)."""
    soup = BeautifulSoup(html, "lxml")
    for link in soup.find_all("link", href=True):
        rel = link.get("rel") or []
        if isinstance(rel, str):
            rel = [rel]
        rel_lower = " ".join(r.lower() for r in rel)
        if "alternate" not in rel_lower:
            continue
        type_ = (link.get("type") or "").lower()
        if "rss" in type_ or "atom" in type_ or "json" in type_:
            return urljoin(base_url, link["href"])
    return None


def warn_if_rss_available(html: str, base_url: str, source_id: int) -> None:
    alt = find_rss_alternate_url(html, base_url)
    if alt:
        logger.warning(
            "Source %s: found RSS/JSON feed at %s — consider type=rss instead of html_list",
            source_id,
            alt,
        )
