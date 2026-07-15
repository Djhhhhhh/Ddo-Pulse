# Task-06: Repository + API 扩展

## 关联验收点
- G8: 前端配置 — Pipeline Job API

## 目标
扩展 Repository 和 API 层，支持新字段的 CRUD。

## 修改文件
- `services/backend/db/ddo_pulse_db/repository.py`
- `services/backend/api/ddo_pulse_api/routes/pipeline_jobs.py`
- `services/backend/api/ddo_pulse_api/schemas.py`

## 具体改动

### repository.py
1. `create_pipeline_job()` / `update_pipeline_job()` 支持新字段：
   - pool_ranking_enabled, ai_quota, dev_quota, other_quota
   - relevance_weight, novelty_weight
   - ai_category_tags, dev_category_tags
2. `create_job_source()` / `update_job_source()` 支持 priority 和 fetch_limit
3. `insert_analyzed_item()` 支持 relevance, novelty, composite_score
4. `list_digest_candidates()` 修改：当使用 composite_score 时按 composite_score DESC 排序

### schemas.py
PipelineJobCreate / PipelineJobUpdate 新增字段：
```python
pool_ranking_enabled: int = 0
ai_quota: int = 6
dev_quota: int = 4
other_quota: int = 2
relevance_weight: float = 0.6
novelty_weight: float = 0.4
ai_category_tags: str = '["AI","机器学习",...]'
dev_category_tags: str = '["开发","工程",...]'
```

JobSourceCreate / JobSourceUpdate 新增字段：
```python
priority: str = "P1"
fetch_limit: int | None = None
```

### routes/pipeline_jobs.py
确保 PUT /pipeline_jobs/{id} 和 PUT /pipeline_jobs/{id}/sources/{sid} 正确传递新字段。

## 验证
运行 G8 的 cmd 测试项。
