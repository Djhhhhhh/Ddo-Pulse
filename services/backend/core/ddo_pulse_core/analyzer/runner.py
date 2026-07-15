"""Analyze unprocessed raw_items."""

from __future__ import annotations

import json
import logging
from typing import Any

from ddo_pulse_core.analyzer.openrouter import OpenRouterAnalyzer
from ddo_pulse_db.repository import Database

logger = logging.getLogger(__name__)


def _row_to_profile(row: Any) -> dict[str, Any]:
    return dict(row)


def _keyword_match(title: str, content: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    blob = f"{title}\n{content}".lower()
    return any(str(k).strip().lower() in blob for k in keywords if str(k).strip())


def _merge_analyze_stats(acc: dict[str, Any], one: dict[str, Any]) -> None:
    acc["pending"] = int(acc.get("pending", 0)) + int(one.get("pending", 0) or 0)
    acc["analyzed"] = int(acc.get("analyzed", 0)) + int(one.get("analyzed", 0) or 0)
    acc["skipped"] = int(acc.get("skipped", 0)) + int(one.get("skipped", 0) or 0)
    acc["keyword_skipped"] = int(acc.get("keyword_skipped", 0)) + int(
        one.get("keyword_skipped", 0) or 0
    )
    acc["errors"] = int(acc.get("errors", 0)) + int(one.get("errors", 0) or 0)
    sr = one.get("skip_reason")
    if sr and acc.get("skip_reason") is None:
        acc["skip_reason"] = sr


def _compute_composite_score(
    result: Any,
    relevance_weight: float,
    novelty_weight: float,
) -> float | None:
    """Compute composite_score from relevance and novelty; fallback to score."""
    r = getattr(result, "relevance", None)
    n = getattr(result, "novelty", None)
    if r is not None and n is not None:
        return float(r) * relevance_weight + float(n) * novelty_weight
    return float(result.score) if result.score is not None else None


def analyze_pending_chunk(
    db: Database,
    rows: list[Any],
    *,
    effective_profile: dict[str, Any],
    profile_id: int,
    keyword_prefilter: bool = False,
    interest_keywords: list[str] | None = None,
    relevance_weight: float = 0.6,
    novelty_weight: float = 0.4,
) -> dict[str, int | str | None]:
    """
    Analyze exactly the given raw_items rows (caller bounds count / sources).
    """
    stats: dict[str, int | str | None] = {
        "pending": len(rows),
        "analyzed": 0,
        "skipped": 0,
        "keyword_skipped": 0,
        "errors": 0,
        "skip_reason": None,
    }

    api_key = (effective_profile.get("api_key") or "").strip()
    if not api_key:
        stats["skipped"] = len(rows)
        stats["skip_reason"] = "no_api_key"
        if len(rows) > 0:
            stats["errors"] = 1
        return stats

    try:
        analyzer = OpenRouterAnalyzer(effective_profile)
    except ValueError as exc:
        stats["skipped"] = len(rows)
        stats["skip_reason"] = str(exc)
        if len(rows) > 0:
            stats["errors"] = 1
        return stats

    kws = interest_keywords or []

    for row in rows:
        raw_id = int(row["id"])
        title = row["title"] or ""
        content = row["content_snippet"] or ""
        if keyword_prefilter and kws and not _keyword_match(title, content, kws):
            stats["keyword_skipped"] = int(stats["keyword_skipped"]) + 1
            continue
        try:
            result = analyzer.analyze(title, content)
            composite_score = _compute_composite_score(result, relevance_weight, novelty_weight)
            db.insert_analyzed_item(
                raw_item_id=raw_id,
                profile_id=profile_id,
                is_quality=result.is_quality,
                score=result.score,
                categories_json=json.dumps(result.categories, ensure_ascii=False),
                summary_zh=result.summary_zh,
                reason=result.reason,
                relevance=getattr(result, "relevance", None),
                novelty=getattr(result, "novelty", None),
                composite_score=composite_score,
            )
            stats["analyzed"] = int(stats["analyzed"]) + 1
        except Exception as exc:
            stats["errors"] = int(stats["errors"]) + 1
            logger.exception("Analyze failed for raw_item %s: %s", raw_id, exc)

    return stats


def analyze_job_sources(
    db: Database,
    sources: list[Any],
    *,
    limit: int | None = 50,
    effective_profile: dict[str, Any],
    profile_id: int,
    keyword_prefilter: bool = False,
    interest_keywords: list[str] | None = None,
    source_analyze_cap: dict[int, int | None] | None = None,
    per_source_interest_keywords: dict[int, list[str]] | None = None,
    relevance_weight: float = 0.6,
    novelty_weight: float = 0.4,
) -> dict[str, int | str | None]:
    """
    Analyze pending items for enabled sources of one job.

    *limit*: global max raw rows to dequeue this run (None = unlimited).
    *source_analyze_cap*: optional per-source_id max rows (None value = no extra cap).
    *per_source_interest_keywords*: optional per-source_id keyword overrides.
    *relevance_weight* / *novelty_weight*: weights for composite_score calculation.
    """
    merged: dict[str, int | str | None] = {
        "pending": 0,
        "analyzed": 0,
        "skipped": 0,
        "keyword_skipped": 0,
        "errors": 0,
        "skip_reason": None,
    }
    caps = source_analyze_cap or {}
    remaining: int | None = limit

    for row in sources:
        sid = int(row["id"])
        cap = caps.get(sid)
        if remaining is not None and remaining <= 0:
            break
        take: int | None = remaining
        if cap is not None:
            take = cap if take is None else min(int(take), int(cap))
        # Per-source keywords override job-level keywords
        src_kws = interest_keywords
        if per_source_interest_keywords and sid in per_source_interest_keywords:
            src_kws = per_source_interest_keywords[sid]
        chunk = db.list_unanalyzed_raw_items(limit=take, source_ids=[sid])
        astats = analyze_pending_chunk(
            db,
            chunk,
            effective_profile=effective_profile,
            profile_id=profile_id,
            keyword_prefilter=keyword_prefilter,
            interest_keywords=src_kws,
            relevance_weight=relevance_weight,
            novelty_weight=novelty_weight,
        )
        _merge_analyze_stats(merged, astats)
        if remaining is not None:
            remaining -= len(chunk)

    return merged


def analyze_pending(
    db: Database,
    *,
    limit: int | None = 50,
    source_ids: list[int] | None = None,
    effective_profile: dict[str, Any],
    profile_id: int,
    keyword_prefilter: bool = False,
    interest_keywords: list[str] | None = None,
) -> dict[str, int | str | None]:
    """
    Analyze raw_items that have no analyzed_items row yet.

    limit: max items to process this run; None means all pending (oldest first).
    """
    pending = db.list_unanalyzed_raw_items(limit=limit, source_ids=source_ids)
    return analyze_pending_chunk(
        db,
        pending,
        effective_profile=effective_profile,
        profile_id=profile_id,
        keyword_prefilter=keyword_prefilter,
        interest_keywords=interest_keywords,
    )


def analyze_pending_default_profile(
    db: Database, *, limit: int | None = 50
) -> dict[str, int | str | None]:
    """Analyze all pending items using the default LLM profile (no source filter)."""
    profile_row = db.get_default_llm_profile()
    if profile_row is None:
        pending = db.list_unanalyzed_raw_items(limit=limit)
        return {
            "pending": len(pending),
            "analyzed": 0,
            "skipped": len(pending),
            "keyword_skipped": 0,
            "errors": 1 if len(pending) > 0 else 0,
            "skip_reason": "no_profile",
        }
    profile = _row_to_profile(profile_row)
    profile_id = int(profile_row["id"])
    return analyze_pending(
        db,
        limit=limit,
        source_ids=None,
        effective_profile=profile,
        profile_id=profile_id,
        keyword_prefilter=False,
        interest_keywords=None,
    )
