"""Feishu custom bot webhook notifier."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

FEISHU_SETTING_KEY = "feishu.webhook_url"
DEFAULT_TOP_N = 8
RETRY_DELAYS = (1.0, 2.0, 4.0)


def _parse_categories(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x) for x in data]
    except json.JSONDecodeError:
        pass
    return []


def build_feishu_post_payload(date: str, rows: list[Any]) -> dict[str, Any]:
    """Rich post message for Feishu bot webhook."""
    title = f"Ddo-Pulse 精选 · {date}"
    blocks: list[list[dict[str, str]]] = []

    if not rows:
        blocks.append([{"tag": "text", "text": "今日暂无达到阈值的精选文章。"}])
    else:
        for idx, row in enumerate(rows, start=1):
            item_title = row["title"] or row["url"]
            url = row["url"]
            score = row["score"]
            cats = "、".join(_parse_categories(row["categories_json"])) or "未分类"
            summary = (row["summary_zh"] or "").strip()
            header = f"{idx}. 【{score}分·{cats}】{item_title}\n"
            blocks.append([{"tag": "text", "text": header}])
            if summary:
                blocks.append([{"tag": "text", "text": f"{summary}\n"}])
            blocks.append(
                [{"tag": "a", "text": "阅读原文", "href": url}, {"tag": "text", "text": "\n\n"}]
            )

    return {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": blocks,
                }
            }
        },
    }


def send_feishu_webhook(
    webhook_url: str,
    payload: dict[str, Any],
    *,
    max_attempts: int = 3,
) -> tuple[bool, str]:
    """POST to Feishu webhook with retries. Returns (ok, response_text)."""
    last_body = ""
    for attempt in range(max_attempts):
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(webhook_url, json=payload)
                last_body = resp.text
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict):
                    code = data.get("code", data.get("StatusCode"))
                    if code is not None and int(code) != 0:
                        msg = data.get("msg") or data.get("StatusMessage") or last_body
                        raise RuntimeError(f"Feishu API error: {msg}")
                return True, last_body
        except Exception as exc:
            logger.warning("Feishu push attempt %s failed: %s", attempt + 1, exc)
            last_body = str(exc)
            if attempt < max_attempts - 1:
                time.sleep(RETRY_DELAYS[attempt])
    return False, last_body
