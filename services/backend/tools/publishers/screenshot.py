"""截图工具。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def generate_screenshots(
    html_path: Path,
    output_dir: Path,
    width: int = 1080
) -> List[Path]:
    """生成 HTML 报告截图"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright not installed, skipping screenshots")
        return []

    if not html_path.exists():
        logger.warning("HTML file not found: %s", html_path)
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    screenshots: List[Path] = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 800})
            page.goto(f"file://{html_path.absolute()}")

            # 获取幻灯片数量
            slide_count = page.eval_on_selector_all(".slide", "els => els.length")

            for i in range(slide_count):
                # 显示当前幻灯片
                page.evaluate(f"show({i})")
                page.wait_for_timeout(500)

                # 截图
                screenshot_path = output_dir / f"page-{i+1:02d}.png"
                page.screenshot(path=str(screenshot_path))
                screenshots.append(screenshot_path)
                logger.info("Screenshot saved: %s", screenshot_path)

            browser.close()
    except Exception as exc:
        logger.exception("Screenshot generation failed: %s", exc)

    return screenshots
