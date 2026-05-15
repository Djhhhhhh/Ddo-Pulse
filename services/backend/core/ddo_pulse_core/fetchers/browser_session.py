"""Fetch list pages using Playwright + local browser profile."""

from __future__ import annotations

import logging

from ddo_pulse_core.fetchers.base import BaseFetcher
from ddo_pulse_core.fetchers.browser_paths import resolve_browser_user_data_dir
from ddo_pulse_core.fetchers.html_common import (
    extract_raw_items_from_html,
    parse_list_config,
    resolve_list_url,
    warn_if_rss_available,
)
from ddo_pulse_core.models import RawItem

logger = logging.getLogger(__name__)


class BrowserSessionFetcher(BaseFetcher):
    def fetch(self, source_id: int, url: str, config_json: str) -> list[RawItem]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "browser_session requires Playwright. Install with: "
                "pip install 'ddo-pulse[browser]' && playwright install chromium"
            ) from exc

        config = parse_list_config(config_json)
        list_url = resolve_list_url(url, config)
        selectors = config["selectors"]
        profile_name = config.get("browser_profile", "chrome")
        headless = bool(config.get("headless", True))
        wait_for = config.get("wait_for")

        user_data_dir = resolve_browser_user_data_dir(str(profile_name))
        if not user_data_dir.exists():
            raise FileNotFoundError(
                f"Browser user data not found: {user_data_dir}. "
                "Log in via Chrome/Edge first, or set browser_profile to a valid path."
            )

        logger.info(
            "browser_session source %s: profile=%s dir=%s (close browser if launch fails)",
            source_id,
            profile_name,
            user_data_dir,
        )

        html = ""
        final_url = list_url
        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(user_data_dir),
                    channel="chrome",
                    headless=headless,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                try:
                    page = context.pages[0] if context.pages else context.new_page()
                    page.goto(list_url, wait_until="domcontentloaded", timeout=60_000)
                    if wait_for:
                        page.wait_for_selector(str(wait_for), timeout=60_000)
                    final_url = page.url
                    html = page.content()
                finally:
                    context.close()
        except Exception as exc:
            raise RuntimeError(
                f"Playwright failed for source {source_id}. "
                "Close Chrome/Edge using this profile and retry, or use html_list if the page is public. "
                f"Original error: {exc}"
            ) from exc

        warn_if_rss_available(html, final_url, source_id)
        return extract_raw_items_from_html(
            html,
            source_id=source_id,
            base_url=final_url,
            selectors=selectors,
        )
