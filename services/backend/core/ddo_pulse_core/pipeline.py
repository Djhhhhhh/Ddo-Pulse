"""Pipeline orchestration."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from ddo_pulse_core.analyzer.runner import analyze_job_sources
from ddo_pulse_core.digest.runner import build_and_push_digest
from ddo_pulse_core.fetchers import BrowserSessionFetcher, HtmlListFetcher, RssFetcher
from ddo_pulse_core.models import normalize_url
from ddo_pulse_db.repository import Database

logger = logging.getLogger(__name__)

RSS_TYPES = frozenset({"rss", "json_feed"})
_fetchers = {
    "rss": RssFetcher(),
    "json_feed": RssFetcher(),
    "html_list": HtmlListFetcher(),
    "browser_session": BrowserSessionFetcher(),
}


def _get_fetcher(source_type: str):
    fetcher = _fetchers.get(source_type)
    if fetcher is None:
        raise ValueError(
            f"Unsupported source type: {source_type}. "
            f"Supported: {', '.join(sorted(_fetchers))}"
        )
    return fetcher


def fetch_source_preview(
    type_: str,
    url: str,
    config_json: str = "{}",
    *,
    max_items: int = 5,
) -> dict[str, Any]:
    """Fetch entries without writing to DB (for connection tests)."""
    fetcher = _get_fetcher(type_)
    items = fetcher.fetch(0, url, config_json or "{}")
    sample = [
        {"title": it.title, "url": it.url} for it in items[:max_items]
    ]
    return {"count": len(items), "sample": sample}


def _fetch_sources(
    database: Database, sources: list, stats: dict[str, int | str | None]
) -> None:
    for row in sources:
        source_id = int(row["id"])
        type_ = row["type"]
        url = row["url"]
        config_json = row["config_json"] or "{}"
        try:
            fetcher = _get_fetcher(type_)
            items = fetcher.fetch(source_id, url, config_json)
            stats["fetched_entries"] = int(stats["fetched_entries"]) + len(items)
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
                    stats["new_items"] = int(stats["new_items"]) + 1
            time.sleep(1.0)
        except Exception as exc:
            stats["errors"] = int(stats["errors"]) + 1
            logger.exception("Fetch failed for source %s (%s): %s", source_id, url, exc)


def _source_analyze_caps_from_rows(sources: list[Any]) -> dict[int, int | None]:
    """Per-source max rows to dequeue per run (from config_json.analyze_limit)."""
    out: dict[int, int | None] = {}
    for row in sources:
        sid = int(row["id"])
        cap: int | None = None
        try:
            cj = json.loads(row["config_json"] or "{}")
            if isinstance(cj, dict):
                v = cj.get("analyze_limit")
                if v is not None:
                    iv = int(v)
                    cap = iv if iv > 0 else None
        except (TypeError, ValueError, json.JSONDecodeError):
            cap = None
        out[sid] = cap
    return out


def _generate_local_reports(
    database: Database,
    job: dict[str, Any],
    source_ids: list[int],
    stats: dict[str, Any],
) -> None:
    """生成本地报告（MD、HTML、截图）"""
    try:
        from agents.reporter import ReporterAgent
        from tools.publishers.report_dir import create_report_dir, generate_timestamp
    except ImportError as exc:
        logger.warning("Reporter agent not available: %s", exc)
        return

    # sqlite3.Row 不支持 .get()，统一转为 dict
    job = dict(job)

    # 获取精选文章
    score_threshold = int(job.get("score_threshold", 7))
    top_n = int(job.get("digest_top_n", 8))
    logger.info(
        "Local report: fetching candidates (threshold=%d, top_n=%d, sources=%s)",
        score_threshold, top_n, source_ids,
    )
    rows = database.list_digest_candidates(
        score_threshold=score_threshold,
        limit=top_n,
        source_ids=source_ids if source_ids else None,
        exclude_pushed=False,
    )

    if not rows:
        logger.info("No articles for local report")
        stats["local_report"] = "no_articles"
        return

    logger.info("Local report: found %d articles", len(rows))

    # 构建 LLM profile
    profile_id = job.get("llm_profile_id")
    if profile_id:
        profile_row = database.get_llm_profile(int(profile_id))
    else:
        profile_row = database.get_default_llm_profile()

    if not profile_row:
        logger.warning("No LLM profile for deep analysis")
        profile = {}
    else:
        profile = dict(profile_row)

    # 转换文章格式（row 也是 sqlite3.Row，需转 dict）
    articles = []
    for row in rows:
        r = dict(row)
        articles.append({
            "id": r["id"],
            "title": r["title"],
            "url": r["url"],
            "score": r["score"],
            "categories": json.loads(r.get("categories_json", "[]")),
            "summary_zh": r.get("summary_zh", ""),
            "reason": r.get("reason", ""),
            "content_snippet": r.get("content_snippet", ""),
        })

    # 生成报告
    timestamp = generate_timestamp()
    report_dir = create_report_dir(timestamp)
    logger.info("Local report: writing to %s", report_dir)

    reporter = ReporterAgent(profile)
    result = reporter.run({
        "articles": articles,
        "timestamp": timestamp,
    })

    stats["local_report_dir"] = result.get("report_dir", str(report_dir))
    stats["local_report_timestamp"] = result.get("timestamp", timestamp)
    stats["local_report_generated"] = True
    stats["local_report_md"] = result.get("md_path")
    stats["local_report_html"] = result.get("html_path")
    stats["local_report_screenshots"] = len(result.get("screenshots", []))
    logger.info("Local reports generated: %s", result)


def _pipeline_terminal(run_id: int, database: Database, stats: dict[str, Any]) -> None:
    errs = int(stats.get("errors", 0) or 0)
    if errs > 0:
        msg: str | None = None
        if stats.get("analyze_skip_reason"):
            msg = str(stats["analyze_skip_reason"])
        elif stats.get("push_error"):
            msg = f"飞书推送失败: {stats['push_error']}"
        else:
            msg = f"运行累计错误数 {errs}（详见 result_json）"
        database.finish_job_run(
            run_id,
            "failed",
            error=msg[:4000],
            result_json=json.dumps(stats, ensure_ascii=False),
            digest_id=stats.get("digest_id"),
        )
    else:
        database.finish_job_run(
            run_id,
            "ok",
            result_json=json.dumps(stats, ensure_ascii=False),
            digest_id=stats.get("digest_id"),
        )


def build_effective_profile(db: Database, job_row: Any) -> tuple[dict[str, Any], int]:
    jid = job_row["llm_profile_id"]
    if jid is not None:
        base = db.get_llm_profile(int(jid))
    else:
        base = db.get_default_llm_profile()
    if base is None:
        raise ValueError("No LLM profile configured for this pipeline job")
    eff: dict[str, Any] = dict(base)
    if job_row["prompt_template"]:
        eff["prompt_template"] = job_row["prompt_template"]
    sp = job_row["system_prompt"]
    if sp:
        eff["system_prompt"] = sp
    rubric = job_row["scoring_rubric"]
    if rubric:
        eff["_job_scoring_rubric"] = rubric
    eff["_job_interest_keywords"] = json.loads(
        job_row["interest_keywords_json"] or "[]"
    )
    return eff, int(base["id"])


def run_pipeline_job(
    database: Database,
    job_id: int,
    *,
    trigger: str = "manual",
    analyze: bool = True,
    push: bool | None = None,
    skip_digest: bool = False,
    force_push: bool = False,
    analyze_limit_override: int | None = None,
) -> dict[str, Any]:
    """
    Run fetch → analyze (scoped to job sources) → digest for one pipeline job.
    Creates a job_runs row with pipeline_job_id set.
    """
    job = database.get_pipeline_job(job_id)
    if job is None:
        raise ValueError(f"Pipeline job {job_id} not found")
    if not job["enabled"]:
        raise ValueError(f"Pipeline job {job_id} is disabled")

    run_id = database.start_job_run(pipeline_job_id=job_id, trigger=trigger)
    stats: dict[str, Any] = {
        "pipeline_job_id": job_id,
        "sources": 0,
        "fetched_entries": 0,
        "new_items": 0,
        "errors": 0,
        "analyze_pending": 0,
        "analyzed": 0,
        "analyze_skipped": 0,
        "analyze_keyword_skipped": 0,
        "analyze_errors": 0,
        "analyze_skip_reason": None,
        "digest_items": 0,
        "push_items": 0,
        "digest_id": None,
        "pushed": False,
        "push_skipped": False,
        "push_skip_reason": None,
        "push_error": None,
    }

    try:
        job_sources = database.list_job_sources(job_id)
        # Convert job_sources rows to source-like rows for compatibility
        sources = []
        focus_configs: dict[int, dict] = {}
        for js in job_sources:
            sid = int(js["source_id"])
            sources.append({
                "id": sid,
                "name": js["name"],
                "type": js["type"],
                "url": js["url"],
                "config_json": js["config_json"],
                "enabled": js["source_enabled"],
            })
            try:
                fc = json.loads(js["focus_config_json"] or "{}")
                if isinstance(fc, dict):
                    focus_configs[sid] = fc
            except (json.JSONDecodeError, TypeError):
                focus_configs[sid] = {}

        source_ids = [int(s["id"]) for s in sources]
        stats["sources"] = len(sources)
        _fetch_sources(database, sources, stats)

        if analyze:
            # Per-source focus config overrides job-level config
            lim_src = job["analyze_limit"]
            if analyze_limit_override is not None:
                lim_src = analyze_limit_override
            limit = None if int(lim_src) <= 0 else int(lim_src)
            interest = json.loads(job["interest_keywords_json"] or "[]")
            try:
                eff, pid = build_effective_profile(database, job)
                caps = _source_analyze_caps_from_rows(sources)
                # Override caps with per-source focus config
                for sid, fc in focus_configs.items():
                    if "analyze_limit" in fc:
                        try:
                            al = int(fc["analyze_limit"])
                            caps[sid] = al if al > 0 else None
                        except (TypeError, ValueError):
                            pass
                # Per-source interest keywords override
                per_source_interest: dict[int, list[str]] = {}
                for sid, fc in focus_configs.items():
                    kw = fc.get("interest_keywords")
                    if isinstance(kw, list) and kw:
                        per_source_interest[sid] = [str(k) for k in kw]

                astats = analyze_job_sources(
                    database,
                    sources,
                    limit=limit,
                    effective_profile=eff,
                    profile_id=pid,
                    keyword_prefilter=bool(job["keyword_prefilter"]),
                    interest_keywords=interest,
                    source_analyze_cap=caps,
                    per_source_interest_keywords=per_source_interest if per_source_interest else None,
                )
            except ValueError as exc:
                astats = {
                    "pending": 0,
                    "analyzed": 0,
                    "skipped": 0,
                    "keyword_skipped": 0,
                    "errors": 1,
                    "skip_reason": str(exc),
                }
            stats["analyze_pending"] = astats.get("pending", 0)
            stats["analyzed"] = astats.get("analyzed", 0)
            stats["analyze_skipped"] = astats.get("skipped", 0)
            stats["analyze_keyword_skipped"] = astats.get("keyword_skipped", 0)
            stats["analyze_errors"] = astats.get("errors", 0)
            stats["analyze_skip_reason"] = astats.get("skip_reason")
            stats["errors"] = int(stats["errors"]) + int(astats.get("errors", 0))

        do_push = bool(job["push_digest"]) if push is None else push

        if not skip_digest:
            dstats = build_and_push_digest(
                database,
                job_id=job_id,
                top_n=int(job["digest_top_n"]),
                score_threshold=int(job["score_threshold"]),
                source_ids=source_ids,
                push=do_push,
                force_push=force_push,
                feishu_webhook_url=str(job["feishu_webhook_url"] or "").strip(),
            )
            stats["digest_items"] = dstats.get("digest_items", 0)
            stats["push_items"] = dstats.get("push_items", 0)
            stats["digest_id"] = dstats.get("digest_id")
            stats["pushed"] = dstats.get("pushed", False)
            stats["push_skipped"] = dstats.get("push_skipped", False)
            stats["push_skip_reason"] = dstats.get("push_skip_reason")
            stats["push_error"] = dstats.get("push_error")
            if dstats.get("push_error") and not dstats.get("pushed"):
                stats["errors"] = int(stats["errors"]) + 1

            # 生成本地报告（MD、HTML、截图）
            try:
                _generate_local_reports(database, job, source_ids, stats)
            except Exception as exc:
                logger.exception("Local report generation failed: %s", exc)
                stats["report_error"] = str(exc)
                stats["errors"] = int(stats["errors"]) + 1

        _pipeline_terminal(run_id, database, stats)
    except Exception as exc:
        database.finish_job_run(
            run_id,
            "failed",
            error=str(exc),
            result_json=json.dumps(stats, ensure_ascii=False),
        )
        raise

    return stats


def _merge_run_stats(aggregate: dict[str, Any], one: dict[str, Any]) -> None:
    for k in (
        "sources",
        "fetched_entries",
        "new_items",
        "errors",
        "analyze_pending",
        "analyzed",
        "analyze_skipped",
        "analyze_keyword_skipped",
        "analyze_errors",
        "digest_items",
    ):
        if k in one:
            aggregate[k] = int(aggregate.get(k, 0)) + int(one.get(k, 0) or 0)
    if one.get("digest_id") is not None:
        aggregate["digest_id"] = one.get("digest_id")
    aggregate["pushed"] = bool(aggregate.get("pushed")) or bool(one.get("pushed"))


def run_once(
    db: Database | None = None,
    *,
    pipeline_job_id: int | None = None,
    analyze: bool = True,
    analyze_limit: int | None = None,
    push: bool | None = None,
    force_push: bool = False,
    skip_digest: bool = False,
) -> dict[str, Any]:
    """
    Run all enabled pipeline jobs (or a single job). Each job records its own job_run.
    """
    own_db = db is None
    database = db or Database()
    aggregate: dict[str, Any] = {
        "jobs_run": 0,
        "sources": 0,
        "fetched_entries": 0,
        "new_items": 0,
        "errors": 0,
        "analyze_pending": 0,
        "analyzed": 0,
        "analyze_skipped": 0,
        "analyze_keyword_skipped": 0,
        "analyze_errors": 0,
        "digest_items": 0,
        "push_items": 0,
        "digest_id": None,
        "pushed": False,
    }
    try:
        if pipeline_job_id is not None:
            jobs = [database.get_pipeline_job(pipeline_job_id)]
            if jobs[0] is None:
                raise ValueError(f"Pipeline job {pipeline_job_id} not found")
        else:
            jobs = [
                j for j in database.list_pipeline_jobs() if j["enabled"]
            ]
        if not jobs:
            logger.warning("No enabled pipeline jobs to run")
            return aggregate

        last_exc: BaseException | None = None
        for job_row in jobs:
            jid = int(job_row["id"])
            try:
                one = run_pipeline_job(
                    database,
                    jid,
                    trigger="manual",
                    analyze=analyze,
                    push=push,
                    skip_digest=skip_digest,
                    force_push=force_push,
                    analyze_limit_override=analyze_limit,
                )
                aggregate["jobs_run"] = int(aggregate["jobs_run"]) + 1
                _merge_run_stats(aggregate, one)
            except Exception as exc:
                last_exc = exc
                aggregate["errors"] = int(aggregate["errors"]) + 1
                logger.exception("Pipeline job %s failed: %s", jid, exc)
        if last_exc is not None and aggregate["jobs_run"] == 0:
            raise last_exc
    finally:
        if own_db:
            database.close()

    return aggregate


def run_fetch(
    db: Database | None = None,
    *,
    source_id: int | None = None,
) -> dict[str, int | str | None]:
    """Fetch one or all enabled sources (no analyze/digest/push)."""
    own_db = db is None
    database = db or Database()
    stats: dict[str, int | str | None] = {
        "sources": 0,
        "fetched_entries": 0,
        "new_items": 0,
        "errors": 0,
        "source_id": source_id,
    }
    try:
        sources = database.list_sources(enabled_only=True)
        if source_id is not None:
            sources = [r for r in sources if int(r["id"]) == source_id]
            if not sources:
                row = database.get_source(source_id)
                if row is None:
                    raise ValueError(f"Source {source_id} not found")
                if not row["enabled"]:
                    raise ValueError(f"Source {source_id} is disabled")
                sources = [row]
        stats["sources"] = len(sources)
        _fetch_sources(database, sources, stats)
    finally:
        if own_db:
            database.close()
    return stats
