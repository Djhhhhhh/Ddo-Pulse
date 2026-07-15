-- Migration 003: Enhanced pipeline configuration
-- Adds source priority, dual-dimension scoring, pool-based ranking config
-- Idempotent: uses ALTER TABLE ... ADD COLUMN IF NOT EXISTS (SQLite 3.35+)

-- pipeline_jobs: pool ranking and quota configuration
ALTER TABLE pipeline_jobs ADD COLUMN pool_ranking_enabled INTEGER NOT NULL DEFAULT 0;
ALTER TABLE pipeline_jobs ADD COLUMN ai_quota INTEGER NOT NULL DEFAULT 6;
ALTER TABLE pipeline_jobs ADD COLUMN dev_quota INTEGER NOT NULL DEFAULT 4;
ALTER TABLE pipeline_jobs ADD COLUMN other_quota INTEGER NOT NULL DEFAULT 2;
ALTER TABLE pipeline_jobs ADD COLUMN relevance_weight REAL NOT NULL DEFAULT 0.6;
ALTER TABLE pipeline_jobs ADD COLUMN novelty_weight REAL NOT NULL DEFAULT 0.4;
ALTER TABLE pipeline_jobs ADD COLUMN ai_category_tags TEXT NOT NULL DEFAULT '["AI","机器学习","深度学习","LLM","大模型","NLP","CV","论文"]';
ALTER TABLE pipeline_jobs ADD COLUMN dev_category_tags TEXT NOT NULL DEFAULT '["开发","工程","架构","DevOps","工具","前端","后端","数据库"]';

-- job_sources: source priority and per-source fetch limit
ALTER TABLE job_sources ADD COLUMN priority TEXT NOT NULL DEFAULT 'P1';
ALTER TABLE job_sources ADD COLUMN fetch_limit INTEGER;

-- analyzed_items: dual-dimension scoring fields
ALTER TABLE analyzed_items ADD COLUMN relevance INTEGER;
ALTER TABLE analyzed_items ADD COLUMN novelty INTEGER;
ALTER TABLE analyzed_items ADD COLUMN composite_score REAL;
