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

                # 截图（full_page=True 捕获完整页面内容）
                screenshot_path = output_dir / f"page-{i+1:02d}.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                screenshots.append(screenshot_path)
                logger.info("Screenshot saved: %s", screenshot_path)

            browser.close()
    except Exception as exc:
        logger.exception("Screenshot generation failed: %s", exc)

    return screenshots


def generate_covers(
    html_path: Path,
    output_dir: Path
) -> dict:
    """生成公众号封面图

    生成两种尺寸的封面图：
    - 头条封面：900×383 像素（约 2.35:1 比例）
    - 次条封面：200×200 像素（1:1 比例）

    Args:
        html_path: HTML 报告文件路径
        output_dir: 输出目录

    Returns:
        dict: {"main": Path, "sub": Path} 封面图路径
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright not installed, skipping cover generation")
        return {}

    if not html_path.exists():
        logger.warning("HTML file not found: %s", html_path)
        return {}

    output_dir.mkdir(parents=True, exist_ok=True)
    covers = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()

            # 头条封面（900×383）
            page_main = browser.new_page(viewport={"width": 900, "height": 383})
            page_main.goto(f"file://{html_path.absolute()}")
            page_main.evaluate("show(0)")
            page_main.wait_for_timeout(500)
            cover_main_path = output_dir / "cover-main.png"
            page_main.screenshot(path=str(cover_main_path))
            covers["main"] = cover_main_path
            logger.info("Cover main saved: %s", cover_main_path)
            page_main.close()

            # 次条封面（200×200）
            page_sub = browser.new_page(viewport={"width": 200, "height": 200})
            page_sub.goto(f"file://{html_path.absolute()}")
            page_sub.evaluate("show(0)")
            page_sub.wait_for_timeout(500)
            cover_sub_path = output_dir / "cover-sub.png"
            page_sub.screenshot(path=str(cover_sub_path))
            covers["sub"] = cover_sub_path
            logger.info("Cover sub saved: %s", cover_sub_path)
            page_sub.close()

            browser.close()
    except Exception as exc:
        logger.exception("Cover generation failed: %s", exc)

    return covers
