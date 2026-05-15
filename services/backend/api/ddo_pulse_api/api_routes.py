"""REST API router (module name avoids conflict with a ``routes/`` package)."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from ddo_pulse_core.digest.builder import digest_date_today
from ddo_pulse_core.notifier.feishu import FEISHU_SETTING_KEY
from ddo_pulse_core.pipeline import fetch_source_preview, run_once, run_pipeline_job
from ddo_pulse_core.web_config import api_public_config
from ddo_pulse_db.repository import Database, _MISSING

from ddo_pulse_api.deps import get_db
from ddo_pulse_api.schemas import (
    ArticleCategoriesOut,
    ArticleListResponse,
    ArticleOut,
    DashboardOut,
    DigestDetailOut,
    DigestTodayOut,
    HealthResponse,
    JobRunDetailOut,
    JobRunOut,
    JobStatsOut,
    PipelineJobCreate,
    PipelineJobOut,
    PipelineJobUpdate,
    ProfileOut,
    ProfileUpdate,
    RunOnceRequest,
    SettingsOut,
    SettingsUpdate,
    SourceCreate,
    SourceOut,
    SourceTestFetchOut,
    SourceTestFetchRequest,
    SourceUpdate,
    WebConfigOut,
)
from ddo_pulse_api.scheduler import (
    reload_pipeline_jobs_schedule,
    scheduler,
    validate_cron_expression,
)

router = APIRouter()


def _mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "(set)" if value else ""
    return f"{value[:4]}...{value[-4:]}"


def _parse_source_config_dict(config_json: str | None) -> dict:
    try:
        d = json.loads(config_json or "{}")
        return d if isinstance(d, dict) else {}
    except json.JSONDecodeError:
        return {}


def _source_analyze_limit_from_config(config_json: str | None) -> int | None:
    v = _parse_source_config_dict(config_json).get("analyze_limit")
    try:
        if v is None:
            return None
        iv = int(v)
        return iv if iv > 0 else None
    except (TypeError, ValueError):
        return None


def _apply_analyze_limit_to_config_json(
    config_json: str, analyze_limit: int | None
) -> str:
    d = _parse_source_config_dict(config_json)
    if analyze_limit is None or int(analyze_limit) <= 0:
        d.pop("analyze_limit", None)
    else:
        d["analyze_limit"] = int(analyze_limit)
    return json.dumps(d, ensure_ascii=False)


def _article_from_row(row) -> ArticleOut:
    categories: list[str] = []
    try:
        categories = json.loads(row["categories_json"] or "[]")
    except json.JSONDecodeError:
        pass
    return ArticleOut(
        id=int(row["id"]),
        title=row["title"] or "",
        url=row["url"] or "",
        score=row["score"],
        is_quality=bool(row["is_quality"]),
        categories=categories,
        summary_zh=row["summary_zh"],
        reason=row["reason"],
        analyzed_at=row["analyzed_at"],
        source_id=int(row["source_id"]),
        published_at=row["published_at"],
    )


def _source_from_row(row) -> SourceOut:
    cj = row["config_json"] or "{}"
    return SourceOut(
        id=int(row["id"]),
        job_id=int(row["job_id"]),
        name=row["name"],
        type=row["type"],
        url=row["url"],
        config_json=cj,
        enabled=bool(row["enabled"]),
        analyze_limit=_source_analyze_limit_from_config(cj),
    )


def _hints_list(row) -> list[str]:
    try:
        raw = json.loads(row["category_hints"] or "[]")
        return [str(x) for x in raw] if isinstance(raw, list) else []
    except json.JSONDecodeError:
        return []


def _profile_from_row(row) -> ProfileOut:
    key = row["api_key"] or ""
    return ProfileOut(
        id=int(row["id"]),
        name=row["name"],
        model=row["model"],
        is_default=bool(row["is_default"]),
        score_threshold=int(row["score_threshold"]),
        api_key_set=bool(key.strip()),
        temperature=float(row["temperature"] or 0.3),
        max_tokens=int(row["max_tokens"] or 1024),
        prompt_template=row["prompt_template"],
        system_prompt=row["system_prompt"],
        category_hints=_hints_list(row),
    )


def _pipeline_job_from_row(row) -> PipelineJobOut:
    try:
        kw = json.loads(row["interest_keywords_json"] or "[]")
    except json.JSONDecodeError:
        kw = []
    if not isinstance(kw, list):
        kw = []
    try:
        wh_raw = str(row["feishu_webhook_url"] or "").strip()
    except (KeyError, IndexError):
        wh_raw = ""
    return PipelineJobOut(
        id=int(row["id"]),
        name=row["name"],
        enabled=bool(row["enabled"]),
        schedule_cron=row["schedule_cron"] or "0 8 * * *",
        analyze_limit=int(row["analyze_limit"]),
        digest_top_n=int(row["digest_top_n"]),
        push_digest=bool(row["push_digest"]),
        score_threshold=int(row["score_threshold"]),
        interest_keywords=[str(x) for x in kw],
        keyword_prefilter=bool(row["keyword_prefilter"]),
        feishu_webhook_url=wh_raw,
        prompt_template=row["prompt_template"],
        scoring_rubric=row["scoring_rubric"],
        system_prompt=row["system_prompt"],
        llm_profile_id=int(row["llm_profile_id"])
        if row["llm_profile_id"] is not None
        else None,
    )


def _merge_pipeline_webhook(row, body: PipelineJobUpdate, patch_keys: set[str]) -> str:
    if "feishu_webhook_url" in patch_keys:
        return (body.feishu_webhook_url or "").strip()
    try:
        return str(row["feishu_webhook_url"] or "").strip()
    except (KeyError, IndexError):
        return ""


def _effective_push_digest(row, body: PipelineJobUpdate, patch_keys: set[str]) -> bool:
    if "push_digest" in patch_keys:
        return bool(body.push_digest)
    return bool(row["push_digest"])


_PUSH_SKIP_LABELS = {
    "push_disabled": "任务未开启推送 Digest",
    "no_webhook": "未配置 Webhook",
    "already_pushed": "该 Digest 已成功推送过",
    "no_enabled_sources": "无已启用的订阅源",
}


def _preview_from_job_run(row) -> str | None:
    err = row["error"]
    if err:
        return f"错误：{err}"
    rj = row["result_json"]
    if not rj:
        return None
    try:
        data = json.loads(rj)
    except json.JSONDecodeError:
        return str(rj)[:400] + ("…" if len(str(rj)) > 400 else "")
    if not isinstance(data, dict):
        return str(rj)[:400] + ("…" if len(str(rj)) > 400 else "")

    parts: list[str] = []
    new_items = data.get("new_items")
    analyzed = data.get("analyzed")
    summary_bits: list[str] = []
    if new_items is not None:
        summary_bits.append(f"新条目 {new_items}")
    if analyzed is not None:
        summary_bits.append(f"分析 {analyzed}")
    if summary_bits:
        parts.append("，".join(summary_bits))

    perr = data.get("push_error")
    if perr:
        parts.append(f"飞书推送失败: {str(perr)[:200]}")
    elif data.get("pushed"):
        parts.append("飞书已推送")
    elif data.get("push_skipped"):
        reason = str(data.get("push_skip_reason") or "")
        label = _PUSH_SKIP_LABELS.get(reason, reason or "未知原因")
        parts.append(f"未推送飞书：{label}")

    digest_n = data.get("digest_items")
    if digest_n is not None and not parts:
        parts.append(f"Digest 条目 {digest_n}")

    if not parts:
        return str(rj)[:400] + ("…" if len(str(rj)) > 400 else "")
    out = "；".join(parts)
    return out[:500] + ("…" if len(out) > 500 else "")


def _job_run_list_out(row) -> JobRunOut:
    return JobRunOut(
        id=int(row["id"]),
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        status=row["status"],
        error=row["error"],
        pipeline_job_id=int(row["pipeline_job_id"])
        if row["pipeline_job_id"] is not None
        else None,
        pipeline_job_name=row["pipeline_job_name"]
        if "pipeline_job_name" in row.keys() and row["pipeline_job_name"]
        else None,
        trigger=row["trigger"] or "manual",
        digest_id=int(row["digest_id"]) if row["digest_id"] is not None else None,
        preview=_preview_from_job_run(row),
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.get("/web-config", response_model=WebConfigOut)
def web_config() -> WebConfigOut:
    return WebConfigOut(**api_public_config())


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    db: Annotated[Database, Depends(get_db)],
    digest_job_id: int | None = None,
) -> DashboardOut:
    today = digest_date_today()
    jid = digest_job_id
    if jid is None:
        jid = db.get_first_pipeline_job_id()
    digest = None
    preview = None
    items_count = 0
    if jid is not None:
        digest = db.get_digest_by_date_and_job(today, jid)
        if digest:
            body = digest["markdown_body"] or ""
            items_count = len(json.loads(digest["item_ids_json"] or "[]"))
            preview = body[:400] + ("…" if len(body) > 400 else "")
    job = db.get_last_job_run()
    prof = db.get_default_llm_profile()
    qthresh = int(prof["score_threshold"]) if prof else 7
    return DashboardOut(
        sources_count=db.count_sources(),
        enabled_sources_count=db.count_sources(enabled_only=True),
        raw_items_count=db.count_raw_items(),
        analyzed_count=db.count_analyzed_items(),
        quality_count=db.count_quality_items(score_threshold=qthresh),
        pending_analyze=db.count_unanalyzed_raw_items(),
        digest_job_id=jid,
        digest_date=today if digest else None,
        digest_items_count=items_count,
        digest_preview=preview,
        last_job_status=job["status"] if job else None,
        last_job_started_at=job["started_at"] if job else None,
    )


@router.get("/digests/today", response_model=DigestTodayOut)
def digest_today(
    db: Annotated[Database, Depends(get_db)],
    job_id: int | None = None,
) -> DigestTodayOut:
    today = digest_date_today()
    jid = job_id if job_id is not None else db.get_first_pipeline_job_id()
    if jid is None:
        return DigestTodayOut(date=today, job_id=None, markdown_body="", item_ids=[])
    row = db.get_digest_by_date_and_job(today, jid)
    if not row:
        return DigestTodayOut(
            date=today, job_id=jid, markdown_body="", item_ids=[]
        )
    return DigestTodayOut(
        date=today,
        job_id=jid,
        markdown_body=row["markdown_body"] or "",
        item_ids=json.loads(row["item_ids_json"] or "[]"),
    )


@router.get("/digests/{digest_id}", response_model=DigestDetailOut)
def get_digest_detail(
    digest_id: int, db: Annotated[Database, Depends(get_db)]
) -> DigestDetailOut:
    row = db.get_digest_by_id(digest_id)
    if not row:
        raise HTTPException(404, "Digest not found")
    return DigestDetailOut(
        id=int(row["id"]),
        job_id=int(row["job_id"]),
        date=row["date"],
        markdown_body=row["markdown_body"] or "",
        item_ids=json.loads(row["item_ids_json"] or "[]"),
    )


@router.get("/articles", response_model=ArticleListResponse)
def list_articles(
    db: Annotated[Database, Depends(get_db)],
    days: int = Query(30, ge=1, le=365),
    min_score: int | None = Query(None, ge=1, le=10),
    source_id: int | None = None,
    category: str | None = None,
    q: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ArticleListResponse:
    rows, total = db.list_analyzed_items_page(
        days=days,
        min_score=min_score,
        source_id=source_id,
        category=category,
        title_q=q,
        limit=limit,
        offset=offset,
    )
    return ArticleListResponse(
        items=[_article_from_row(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/articles/categories", response_model=ArticleCategoriesOut)
def article_categories(
    db: Annotated[Database, Depends(get_db)],
    days: int = Query(365, ge=1, le=3650),
) -> ArticleCategoriesOut:
    return ArticleCategoriesOut(categories=db.list_article_categories(days=days))


@router.get("/articles/{article_id}", response_model=ArticleOut)
def get_article(
    article_id: int, db: Annotated[Database, Depends(get_db)]
) -> ArticleOut:
    row = db.get_analyzed_item(article_id)
    if not row:
        raise HTTPException(404, "Article not found")
    return _article_from_row(row)


@router.get("/sources", response_model=list[SourceOut])
def list_sources(
    db: Annotated[Database, Depends(get_db)],
    job_id: int | None = None,
) -> list[SourceOut]:
    return [_source_from_row(r) for r in db.list_sources(job_id=job_id)]


@router.post("/sources/test-fetch", response_model=SourceTestFetchOut)
def test_source_fetch(body: SourceTestFetchRequest) -> SourceTestFetchOut:
    try:
        data = fetch_source_preview(
            body.type, body.url, body.config_json or "{}", max_items=8
        )
        return SourceTestFetchOut(**data)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/sources", response_model=SourceOut, status_code=201)
def create_source(
    body: SourceCreate, db: Annotated[Database, Depends(get_db)]
) -> SourceOut:
    if not db.get_pipeline_job(body.job_id):
        raise HTTPException(404, "Pipeline job not found")
    cj = body.config_json if body.config_json else "{}"
    patch = body.model_dump(exclude_unset=True)
    if "analyze_limit" in patch:
        cj = _apply_analyze_limit_to_config_json(cj, patch["analyze_limit"])
    sid = db.add_source(
        job_id=body.job_id,
        name=body.name,
        type_=body.type,
        url=body.url,
        config_json=cj,
        enabled=body.enabled,
    )
    row = db.get_source(sid)
    assert row is not None
    return _source_from_row(row)


@router.patch("/sources/{source_id}", response_model=SourceOut)
def update_source(
    source_id: int,
    body: SourceUpdate,
    db: Annotated[Database, Depends(get_db)],
) -> SourceOut:
    row = db.get_source(source_id)
    if not row:
        raise HTTPException(404, "Source not found")
    if body.job_id is not None and not db.get_pipeline_job(body.job_id):
        raise HTTPException(404, "Pipeline job not found")
    patch = body.model_dump(exclude_unset=True)
    cj_out = row["config_json"] or "{}"
    if "config_json" in patch:
        cj_out = patch["config_json"] or "{}"
    if "analyze_limit" in patch:
        cj_out = _apply_analyze_limit_to_config_json(cj_out, patch["analyze_limit"])
    cfg_touch = "config_json" in patch or "analyze_limit" in patch
    ok = db.update_source(
        source_id,
        job_id=patch.get("job_id"),
        name=patch.get("name"),
        type_=patch.get("type"),
        url=patch.get("url"),
        config_json=cj_out if cfg_touch else None,
        enabled=patch.get("enabled"),
    )
    if not ok:
        raise HTTPException(404, "Source not found")
    row = db.get_source(source_id)
    assert row is not None
    return _source_from_row(row)


@router.delete("/sources/{source_id}", status_code=204)
def delete_source(
    source_id: int, db: Annotated[Database, Depends(get_db)]
) -> None:
    if not db.delete_source(source_id):
        raise HTTPException(404, "Source not found")


@router.get("/profiles", response_model=list[ProfileOut])
def list_profiles(db: Annotated[Database, Depends(get_db)]) -> list[ProfileOut]:
    return [_profile_from_row(r) for r in db.list_llm_profiles()]


@router.patch("/profiles/{profile_id}", response_model=ProfileOut)
def update_profile(
    profile_id: int,
    body: ProfileUpdate,
    db: Annotated[Database, Depends(get_db)],
) -> ProfileOut:
    if body.is_default:
        db.set_default_llm_profile(profile_id)
    hints_arg = body.category_hints
    ok = db.update_llm_profile(
        profile_id,
        api_key=body.api_key,
        model=body.model,
        score_threshold=body.score_threshold,
        prompt_template=body.prompt_template,
        system_prompt=body.system_prompt,
        category_hints=hints_arg,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
    )
    if not ok:
        raise HTTPException(404, "Profile not found")
    row = db.get_llm_profile(profile_id)
    if not row:
        raise HTTPException(404, "Profile not found")
    return _profile_from_row(row)


@router.get("/settings", response_model=SettingsOut)
def get_settings(db: Annotated[Database, Depends(get_db)]) -> SettingsOut:
    webhook = db.get_app_setting(FEISHU_SETTING_KEY) or ""
    return SettingsOut(
        feishu_webhook_set=bool(webhook.strip()),
        feishu_webhook_masked=_mask_secret(webhook),
    )


@router.patch("/settings", response_model=SettingsOut)
def update_settings(
    body: SettingsUpdate, db: Annotated[Database, Depends(get_db)]
) -> SettingsOut:
    if body.feishu_webhook_url is not None:
        db.set_app_setting(FEISHU_SETTING_KEY, body.feishu_webhook_url)
    return get_settings(db)


@router.get("/pipeline-jobs", response_model=list[PipelineJobOut])
def list_pipeline_jobs(
    db: Annotated[Database, Depends(get_db)],
) -> list[PipelineJobOut]:
    return [_pipeline_job_from_row(r) for r in db.list_pipeline_jobs()]


@router.post("/pipeline-jobs", response_model=PipelineJobOut, status_code=201)
def create_pipeline_job(
    body: PipelineJobCreate, db: Annotated[Database, Depends(get_db)]
) -> PipelineJobOut:
    try:
        validate_cron_expression(body.schedule_cron)
    except Exception as exc:
        raise HTTPException(400, f"Invalid cron: {exc}") from exc
    if body.llm_profile_id is not None and not db.get_llm_profile(
        body.llm_profile_id
    ):
        raise HTTPException(404, "LLM profile not found")
    kw_json = json.dumps(body.interest_keywords, ensure_ascii=False)
    wh = (body.feishu_webhook_url or "").strip()
    if not wh:
        raise HTTPException(400, "每个定时任务必须填写飞书 Webhook URL")
    jid = db.add_pipeline_job(
        body.name,
        schedule_cron=body.schedule_cron.strip(),
        enabled=body.enabled,
        analyze_limit=body.analyze_limit,
        digest_top_n=body.digest_top_n,
        push_digest=body.push_digest,
        score_threshold=body.score_threshold,
        interest_keywords_json=kw_json,
        keyword_prefilter=body.keyword_prefilter,
        prompt_template=body.prompt_template,
        scoring_rubric=body.scoring_rubric,
        system_prompt=body.system_prompt,
        llm_profile_id=body.llm_profile_id,
        feishu_webhook_url=wh,
    )
    reload_pipeline_jobs_schedule(scheduler)
    row = db.get_pipeline_job(jid)
    assert row is not None
    return _pipeline_job_from_row(row)


@router.get("/pipeline-jobs/{job_id}", response_model=PipelineJobOut)
def get_pipeline_job_api(
    job_id: int, db: Annotated[Database, Depends(get_db)]
) -> PipelineJobOut:
    row = db.get_pipeline_job(job_id)
    if not row:
        raise HTTPException(404, "Pipeline job not found")
    return _pipeline_job_from_row(row)


@router.patch("/pipeline-jobs/{job_id}", response_model=PipelineJobOut)
def update_pipeline_job_api(
    job_id: int,
    body: PipelineJobUpdate,
    db: Annotated[Database, Depends(get_db)],
) -> PipelineJobOut:
    row = db.get_pipeline_job(job_id)
    if not row:
        raise HTTPException(404, "Pipeline job not found")
    patch_keys = set(body.model_dump(exclude_unset=True).keys())

    merged_wh = _merge_pipeline_webhook(row, body, patch_keys)
    merged_push = _effective_push_digest(row, body, patch_keys)
    if merged_push and not merged_wh:
        raise HTTPException(
            400, "已开启「完成后推送 Digest」时，必须为该任务配置飞书 Webhook URL"
        )

    if "schedule_cron" in patch_keys:
        try:
            validate_cron_expression(body.schedule_cron or "")
        except Exception as exc:
            raise HTTPException(400, f"Invalid cron: {exc}") from exc
    if (
        "llm_profile_id" in patch_keys
        and body.llm_profile_id is not None
        and not db.get_llm_profile(body.llm_profile_id)
    ):
        raise HTTPException(404, "LLM profile not found")

    def _f(name: str):
        if name not in patch_keys:
            return _MISSING
        return getattr(body, name)

    def _cron_val():
        if "schedule_cron" not in patch_keys:
            return _MISSING
        v = body.schedule_cron or ""
        return v.strip()

    def _interest_json():
        if "interest_keywords" not in patch_keys:
            return _MISSING
        kws = body.interest_keywords or []
        return json.dumps(list(kws), ensure_ascii=False)

    def _wh():
        if "feishu_webhook_url" not in patch_keys:
            return _MISSING
        return (body.feishu_webhook_url or "").strip()

    ok = db.update_pipeline_job(
        job_id,
        name=_f("name"),
        schedule_cron=_cron_val(),
        enabled=_f("enabled"),
        analyze_limit=_f("analyze_limit"),
        digest_top_n=_f("digest_top_n"),
        push_digest=_f("push_digest"),
        score_threshold=_f("score_threshold"),
        interest_keywords_json=_interest_json(),
        keyword_prefilter=_f("keyword_prefilter"),
        prompt_template=_f("prompt_template"),
        scoring_rubric=_f("scoring_rubric"),
        system_prompt=_f("system_prompt"),
        llm_profile_id=_f("llm_profile_id"),
        feishu_webhook_url=_wh(),
    )
    if not ok:
        raise HTTPException(404, "Pipeline job not found")
    reload_pipeline_jobs_schedule(scheduler)
    row2 = db.get_pipeline_job(job_id)
    assert row2 is not None
    return _pipeline_job_from_row(row2)


@router.delete("/pipeline-jobs/{job_id}", status_code=204)
def delete_pipeline_job_api(
    job_id: int, db: Annotated[Database, Depends(get_db)]
) -> None:
    if not db.delete_pipeline_job(job_id):
        raise HTTPException(404, "Pipeline job not found")
    reload_pipeline_jobs_schedule(scheduler)


@router.post("/pipeline-jobs/reload-scheduler", status_code=204)
def reload_scheduler() -> None:
    reload_pipeline_jobs_schedule(scheduler)


@router.post("/pipeline-jobs/{job_id}/run", response_model=JobStatsOut)
def run_pipeline_job_manual(
    job_id: int,
    db: Annotated[Database, Depends(get_db)],
    skip_analyze: bool = False,
    skip_digest: bool = False,
    skip_push: bool = Query(False),
    analyze_limit: int = Query(50, ge=0),
) -> JobStatsOut:
    if not db.get_pipeline_job(job_id):
        raise HTTPException(404, "Pipeline job not found")
    try:
        lim = analyze_limit if analyze_limit > 0 else None
        stats = run_pipeline_job(
            db,
            job_id,
            trigger="manual",
            analyze=not skip_analyze,
            push=False if skip_push else None,
            skip_digest=skip_digest,
            analyze_limit_override=lim,
        )
        return JobStatsOut(ok=int(stats.get("errors", 0) or 0) == 0, stats=stats)
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


@router.get("/job-runs", response_model=list[JobRunOut])
def list_job_runs_api(
    db: Annotated[Database, Depends(get_db)],
    limit: int = Query(40, ge=1, le=200),
    job_id: int | None = None,
) -> list[JobRunOut]:
    return [
        _job_run_list_out(r)
        for r in db.list_job_runs(limit=limit, pipeline_job_id=job_id)
    ]


@router.get("/job-runs/{run_id}", response_model=JobRunDetailOut)
def get_job_run_api(
    run_id: int, db: Annotated[Database, Depends(get_db)]
) -> JobRunDetailOut:
    row = db.get_job_run(run_id)
    if not row:
        raise HTTPException(404, "Job run not found")
    md = None
    if row["digest_id"]:
        dg = db.get_digest_by_id(int(row["digest_id"]))
        if dg:
            md = dg["markdown_body"]
    return JobRunDetailOut(
        id=int(row["id"]),
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        status=row["status"],
        error=row["error"],
        pipeline_job_id=int(row["pipeline_job_id"])
        if row["pipeline_job_id"] is not None
        else None,
        pipeline_job_name=row["pipeline_job_name"]
        if "pipeline_job_name" in row.keys()
        else None,
        trigger=row["trigger"] or "manual",
        digest_id=int(row["digest_id"]) if row["digest_id"] is not None else None,
        result_json=row["result_json"],
        markdown_body=md,
    )


@router.post("/jobs/run-once", response_model=JobStatsOut)
def jobs_run_once(
    body: RunOnceRequest, db: Annotated[Database, Depends(get_db)]
) -> JobStatsOut:
    try:
        push_arg = False if body.skip_push else None
        stats = run_once(
            db,
            pipeline_job_id=body.pipeline_job_id,
            analyze=not body.skip_analyze,
            analyze_limit=body.analyze_limit,
            push=push_arg,
            skip_digest=body.skip_digest,
        )
        return JobStatsOut(ok=int(stats.get("errors", 0) or 0) == 0, stats=stats)
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc
