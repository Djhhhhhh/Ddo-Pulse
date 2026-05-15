"""Fetch blog list pages via httpx + BeautifulSoup."""

from __future__ import annotations

import httpx

from ddo_pulse_core.fetchers.base import BaseFetcher
from ddo_pulse_core.fetchers.html_common import (
    USER_AGENT,
    extract_raw_items_from_html,
    parse_list_config,
    resolve_list_url,
    warn_if_rss_available,
)
from ddo_pulse_core.models import RawItem

TIMEOUT = 30.0


class HtmlListFetcher(BaseFetcher):
    def fetch(self, source_id: int, url: str, config_json: str) -> list[RawItem]:
        config = parse_list_config(config_json)
        list_url = resolve_list_url(url, config)
        selectors = config["selectors"]

        headers = {"User-Agent": USER_AGENT}
        with httpx.Client(timeout=TIMEOUT, headers=headers, follow_redirects=True) as client:
            resp = client.get(list_url)
            resp.raise_for_status()
            html = resp.text

        base_url = str(resp.url)
        warn_if_rss_available(html, base_url, source_id)
        return extract_raw_items_from_html(
            html,
            source_id=source_id,
            base_url=base_url,
            selectors=selectors,
        )
