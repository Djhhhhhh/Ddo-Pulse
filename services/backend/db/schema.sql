-- Ddo-Pulse schema (see docs/mvp.md section 11)

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    url TEXT NOT NULL,
    config_json TEXT DEFAULT '{}',
    enabled INTEGER NOT NULL DEFAULT 1,
    fetch_cron TEXT,
    created_at TEXT NOT NULL
);

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
    score_threshold INTEGER NOT NULL DEFAULT 7,
    category_hints TEXT DEFAULT '[]',
    is_default INTEGER NOT NULL DEFAULT 0
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
    analyzed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS digests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    item_ids_json TEXT NOT NULL DEFAULT '[]',
    markdown_body TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
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
    error TEXT
);

CREATE INDEX IF NOT EXISTS idx_raw_items_source_id ON raw_items(source_id);
CREATE INDEX IF NOT EXISTS idx_sources_enabled ON sources(enabled);
