"""API request/response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class WebConfigOut(BaseModel):
    title: str
    api_base: str
    api_host: str
    api_port: int


class SourceOut(BaseModel):
    id: int
    name: str
    type: str
    url: str
    config_json: str
    enabled: bool
    analyze_limit: int | None = None


class SourceCreate(BaseModel):
    name: str
    type: str
    url: str
    config_json: str = "{}"
    enabled: bool = True
    analyze_limit: int | None = Field(default=None, ge=0, le=50000)


class SourceUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    url: str | None = None
    config_json: str | None = None
    enabled: bool | None = None
    analyze_limit: int | None = Field(default=None, ge=0, le=50000)


class JobSourceOut(BaseModel):
    job_source_id: int
    job_id: int
    source_id: int
    name: str
    type: str
    url: str
    config_json: str
    source_enabled: bool
    focus_config_json: str
    job_source_enabled: bool


class JobSourceCreate(BaseModel):
    source_id: int
    focus_config_json: str = "{}"
    enabled: bool = True


class JobSourceUpdate(BaseModel):
    focus_config_json: str | None = None
    enabled: bool | None = None


class SyncFromCsvResult(BaseModel):
    added: int
    updated: int
    skipped: int
    total: int


class SourceTestFetchRequest(BaseModel):
    type: str
    url: str
    config_json: str = "{}"


class SourceTestFetchOut(BaseModel):
    count: int
    sample: list[dict]


class ProfileOut(BaseModel):
    id: int
    name: str
    model: str
    is_default: bool
    score_threshold: int
    api_key_set: bool
    temperature: float = 0.3
    max_tokens: int = 1024
    prompt_template: str | None = None
    system_prompt: str | None = None
    category_hints: list[str] = Field(default_factory=list)


class ProfileUpdate(BaseModel):
    api_key: str | None = None
    model: str | None = None
    score_threshold: int | None = None
    is_default: bool | None = None
    prompt_template: str | None = None
    system_prompt: str | None = None
    category_hints: list[str] | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class SettingsOut(BaseModel):
    feishu_webhook_set: bool
    feishu_webhook_masked: str


class SettingsUpdate(BaseModel):
    feishu_webhook_url: str | None = None


class ArticleOut(BaseModel):
    id: int
    title: str
    url: str
    score: int | None
    is_quality: bool
    categories: list[str]
    summary_zh: str | None
    reason: str | None
    analyzed_at: str
    source_id: int
    published_at: str | None = None
    is_pushed: bool = False
    is_read: bool = False


class ArticleListResponse(BaseModel):
    items: list[ArticleOut]
    total: int
    limit: int
    offset: int


class ArticleCategoriesOut(BaseModel):
    categories: list[str]


class DashboardOut(BaseModel):
    sources_count: int
    enabled_sources_count: int
    raw_items_count: int
    analyzed_count: int
    read_count: int
    quality_count: int
    pending_analyze: int
    digest_job_id: int | None = None
    digest_date: str | None = None
    digest_items_count: int = 0
    digest_preview: str | None = None
    last_job_status: str | None = None
    last_job_started_at: str | None = None


class DigestTodayOut(BaseModel):
    date: str
    job_id: int | None = None
    markdown_body: str
    item_ids: list[int]


class DigestDetailOut(BaseModel):
    id: int
    job_id: int
    date: str
    markdown_body: str
    item_ids: list[int]


class PipelineJobOut(BaseModel):
    id: int
    name: str
    enabled: bool
    schedule_cron: str
    analyze_limit: int
    digest_top_n: int
    push_digest: bool
    score_threshold: int
    interest_keywords: list[str]
    keyword_prefilter: bool
    feishu_webhook_url: str = ""
    prompt_template: str | None = None
    scoring_rubric: str | None = None
    system_prompt: str | None = None
    llm_profile_id: int | None = None


class PipelineJobCreate(BaseModel):
    name: str
    schedule_cron: str = "0 8 * * *"
    enabled: bool = True
    analyze_limit: int = Field(50, ge=0)
    digest_top_n: int = Field(8, ge=1)
    push_digest: bool = False
    score_threshold: int = Field(7, ge=1, le=10)
    interest_keywords: list[str] = Field(default_factory=list)
    keyword_prefilter: bool = False
    feishu_webhook_url: str
    prompt_template: str | None = None
    scoring_rubric: str | None = None
    system_prompt: str | None = None
    llm_profile_id: int | None = None


class PipelineJobUpdate(BaseModel):
    name: str | None = None
    schedule_cron: str | None = None
    enabled: bool | None = None
    analyze_limit: int | None = Field(None, ge=0)
    digest_top_n: int | None = Field(None, ge=1)
    push_digest: bool | None = None
    score_threshold: int | None = Field(None, ge=1, le=10)
    interest_keywords: list[str] | None = None
    keyword_prefilter: bool | None = None
    feishu_webhook_url: str | None = None
    prompt_template: str | None = None
    scoring_rubric: str | None = None
    system_prompt: str | None = None
    llm_profile_id: int | None = None


class JobRunOut(BaseModel):
    id: int
    started_at: str
    finished_at: str | None = None
    status: str
    error: str | None = None
    pipeline_job_id: int | None = None
    pipeline_job_name: str | None = None
    trigger: str
    digest_id: int | None = None
    preview: str | None = None


class JobRunDetailOut(BaseModel):
    id: int
    started_at: str
    finished_at: str | None = None
    status: str
    error: str | None = None
    pipeline_job_id: int | None = None
    pipeline_job_name: str | None = None
    trigger: str
    digest_id: int | None = None
    preview: str | None = None
    result_json: str | None = None
    markdown_body: str | None = None


class RunOnceRequest(BaseModel):
    pipeline_job_id: int | None = None
    analyze_limit: int = Field(50, ge=0)
    skip_analyze: bool = False
    skip_digest: bool = False
    skip_push: bool = True


class RssSeedItem(BaseModel):
    category: str
    name: str
    type: str = "rss"
    url: str
    site: str = ""
    freq: str = ""
    desc: str = ""
    priority: str = ""


class RssSeedList(BaseModel):
    items: list[RssSeedItem]


class JobStatsOut(BaseModel):
    ok: bool
    stats: dict
