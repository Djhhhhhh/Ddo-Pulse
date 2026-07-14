-- Ddo-Pulse schema (pipeline jobs + per-job sources/digests)

CREATE TABLE IF NOT EXISTS llm_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL DEFAULT 'openrouter',
    base_url TEXT NOT NULL DEFAULT 'https://openrouter.ai/api/v1',
    model TEXT NOT NULL,
    api_key TEXT DEFAULT '',
    site_url TEXT,
    app_title TEXT,
    temperature REAL NOT NULL DEFAULT 0.3,
    max_tokens INTEGER NOT NULL DEFAULT 1024,
    prompt_template TEXT,
    system_prompt TEXT,
    score_threshold INTEGER NOT NULL DEFAULT 7,
    category_hints TEXT DEFAULT '[]',
    is_default INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pipeline_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    schedule_cron TEXT NOT NULL DEFAULT '0 8 * * *',
    analyze_limit INTEGER NOT NULL DEFAULT 50,
    digest_top_n INTEGER NOT NULL DEFAULT 8,
    push_digest INTEGER NOT NULL DEFAULT 0,
    score_threshold INTEGER NOT NULL DEFAULT 7,
    interest_keywords_json TEXT NOT NULL DEFAULT '[]',
    keyword_prefilter INTEGER NOT NULL DEFAULT 0,
    prompt_template TEXT,
    scoring_rubric TEXT,
    system_prompt TEXT,
    llm_profile_id INTEGER REFERENCES llm_profiles(id) ON DELETE SET NULL,
    feishu_webhook_url TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    config_json TEXT DEFAULT '{}',
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES pipeline_jobs(id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    focus_config_json TEXT NOT NULL DEFAULT '{}',
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    UNIQUE(job_id, source_id)
);

CREATE TABLE IF NOT EXISTS raw_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL DEFAULT '',
    published_at TEXT,
    content_snippet TEXT DEFAULT '',
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analyzed_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_item_id INTEGER NOT NULL UNIQUE REFERENCES raw_items(id) ON DELETE CASCADE,
    profile_id INTEGER NOT NULL REFERENCES llm_profiles(id),
    is_quality INTEGER NOT NULL DEFAULT 0,
    score INTEGER,
    categories_json TEXT DEFAULT '[]',
    summary_zh TEXT,
    reason TEXT,
    deep_analysis_json TEXT,
    analyzed_at TEXT NOT NULL,
    pushed_at TEXT,
    read_at TEXT
);

CREATE TABLE IF NOT EXISTS digests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES pipeline_jobs(id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    item_ids_json TEXT NOT NULL DEFAULT '[]',
    markdown_body TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    UNIQUE(date, job_id)
);

CREATE TABLE IF NOT EXISTS push_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    digest_id INTEGER NOT NULL REFERENCES digests(id) ON DELETE CASCADE,
    channel TEXT NOT NULL DEFAULT 'feishu',
    status TEXT NOT NULL,
    response TEXT,
    pushed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    error TEXT,
    pipeline_job_id INTEGER REFERENCES pipeline_jobs(id) ON DELETE SET NULL,
    trigger TEXT NOT NULL DEFAULT 'manual',
    result_json TEXT,
    digest_id INTEGER REFERENCES digests(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_items_source_id ON raw_items(source_id);
CREATE INDEX IF NOT EXISTS idx_sources_enabled ON sources(enabled);
CREATE INDEX IF NOT EXISTS idx_job_sources_job_id ON job_sources(job_id);
CREATE INDEX IF NOT EXISTS idx_job_sources_source_id ON job_sources(source_id);
CREATE INDEX IF NOT EXISTS idx_job_runs_pipeline_job ON job_runs(pipeline_job_id);
CREATE INDEX IF NOT EXISTS idx_digests_job_date ON digests(job_id, date);
