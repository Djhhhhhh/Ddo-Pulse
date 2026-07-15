"""Pool-based ranking algorithm for digest article selection.

Groups articles into AI/dev/other pools by category tags,
selects articles per pool according to quotas, backfills from
other pools when a pool is short, then globally re-sorts.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def categorize_article(
    categories: list[str],
    ai_tags: list[str],
    dev_tags: list[str],
) -> str:
    """Classify an article into 'ai', 'dev', or 'other' based on its categories."""
    cat_lower = {c.strip().lower() for c in categories if c.strip()}
    ai_lower = {t.strip().lower() for t in ai_tags if t.strip()}
    dev_lower = {t.strip().lower() for t in dev_tags if t.strip()}

    if cat_lower & ai_lower:
        return "ai"
    if cat_lower & dev_lower:
        return "dev"
    return "other"


def rank_with_pools(
    candidates: list[Any],
    *,
    ai_tags: list[str],
    dev_tags: list[str],
    ai_quota: int,
    dev_quota: int,
    other_quota: int,
    top_n: int,
) -> list[Any]:
    """Select articles using pool-based ranking.

    1. Categorize each candidate into ai/dev/other pool
    2. Sort each pool by composite_score DESC
    3. Select up to quota from each pool
    4. Backfill shortages from remaining candidates
    5. Globally re-sort by composite_score DESC
    6. Truncate to top_n

    Args:
        candidates: analyzed_items rows (sqlite3.Row or dict) with
                    categories_json and composite_score fields.
        ai_tags: category tags that define the AI pool.
        dev_tags: category tags that define the dev pool.
        ai_quota / dev_quota / other_quota: per-pool selection limits.
        top_n: final maximum number of articles.

    Returns:
        Selected rows sorted by composite_score DESC, length <= top_n.
    """
    if not candidates:
        return []

    ai_pool: list[Any] = []
    dev_pool: list[Any] = []
    other_pool: list[Any] = []

    for row in candidates:
        # Parse categories from JSON string or use list directly
        cats_raw = row["categories_json"] if isinstance(row, dict) else row["categories_json"]
        if isinstance(cats_raw, str):
            try:
                cats = json.loads(cats_raw)
            except (json.JSONDecodeError, TypeError):
                cats = []
        else:
            cats = cats_raw or []

        pool = categorize_article(cats, ai_tags, dev_tags)
        if pool == "ai":
            ai_pool.append(row)
        elif pool == "dev":
            dev_pool.append(row)
        else:
            other_pool.append(row)

    # Sort each pool by composite_score DESC (NULL last)
    def sort_key(r: Any) -> float:
        cs = r["composite_score"] if isinstance(r, dict) else r["composite_score"]
        if cs is None:
            return -1.0
        return float(cs)

    ai_pool.sort(key=sort_key, reverse=True)
    dev_pool.sort(key=sort_key, reverse=True)
    other_pool.sort(key=sort_key, reverse=True)

    # Select by quota
    selected = ai_pool[:ai_quota] + dev_pool[:dev_quota] + other_pool[:other_quota]

    # Backfill: if selected < total_target, fill from remaining candidates
    total_target = ai_quota + dev_quota + other_quota
    if len(selected) < total_target:
        selected_ids = {id(r) for r in selected}
        remaining = [r for r in candidates if id(r) not in selected_ids]
        remaining.sort(key=sort_key, reverse=True)
        for r in remaining:
            if len(selected) >= total_target:
                break
            selected.append(r)

    # Global re-sort by composite_score DESC
    selected.sort(key=sort_key, reverse=True)

    # Truncate to top_n
    return selected[:top_n]
