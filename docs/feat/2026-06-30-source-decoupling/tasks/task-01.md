# Task-01: DB Schema 变更

## 目标
修改 `schema.sql`，将 `sources` 从 `pipeline_jobs` 的子表变为全局独立实体，并新增 `job_sources` 关联表。

## 关联验收点
- G1: DB Schema 变更与数据迁移

## 变更文件
- `services/backend/db/schema.sql`

## 具体变更

### sources 表
1. 移除 `job_id INTEGER NOT NULL REFERENCES pipeline_jobs(id) ON DELETE CASCADE` 列
2. 为 `url` 添加 `UNIQUE` 约束
3. 移除 `idx_sources_job_id` 索引

### job_sources 表（新增）
```sql
CREATE TABLE IF NOT EXISTS job_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES pipeline_jobs(id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    focus_config_json TEXT NOT NULL DEFAULT '{}',
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    UNIQUE(job_id, source_id)
);
CREATE INDEX IF NOT EXISTS idx_job_sources_job_id ON job_sources(job_id);
CREATE INDEX IF NOT EXISTS idx_job_sources_source_id ON job_sources(source_id);
```

## 验收
- 运行 test-plan G1 中所有 cmd 检查项
