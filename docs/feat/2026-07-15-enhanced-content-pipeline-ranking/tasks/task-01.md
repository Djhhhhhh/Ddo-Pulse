# Task-01: 数据库 Migration

## 关联验收点
- G1: 数据库 Migration

## 目标
为 pipeline_jobs、job_sources、analyzed_items 三张表新增所有配置字段。

## 修改文件
- `services/backend/db/schema.sql`
- `services/backend/db/migrations/003_enhanced_pipeline_config.sql`（新建）

## 具体改动

### schema.sql
在 pipeline_jobs 表中新增：
```sql
pool_ranking_enabled INTEGER NOT NULL DEFAULT 0,
ai_quota INTEGER NOT NULL DEFAULT 6,
dev_quota INTEGER NOT NULL DEFAULT 4,
other_quota INTEGER NOT NULL DEFAULT 2,
relevance_weight REAL NOT NULL DEFAULT 0.6,
novelty_weight REAL NOT NULL DEFAULT 0.4,
ai_category_tags TEXT NOT NULL DEFAULT '["AI","机器学习","深度学习","LLM","大模型","NLP","CV","论文"]',
dev_category_tags TEXT NOT NULL DEFAULT '["开发","工程","架构","DevOps","工具","前端","后端","数据库"]'
```

在 job_sources 表中新增：
```sql
priority TEXT NOT NULL DEFAULT 'P1',
fetch_limit INTEGER
```

在 analyzed_items 表中新增：
```sql
relevance INTEGER,
novelty INTEGER,
composite_score REAL
```

### migration 脚本
创建 `003_enhanced_pipeline_config.sql`，使用 ALTER TABLE IF NOT EXISTS 确保幂等。

## 验证
运行 G1 的 3 个 cmd 测试项确认所有列存在。
