# Task-05: Digest Runner 集成分池排名

## 关联验收点
- G4: composite_score 计算
- G6: 分池排名算法
- G7: 分池排名开关
- G11: 向后兼容

## 目标
修改 digest/runner.py，根据 pool_ranking_enabled 开关选择排名策略。

## 修改文件
- `services/backend/core/ddo_pulse_core/digest/runner.py`
- `services/backend/core/ddo_pulse_core/pipeline.py`

## 具体改动

### digest/runner.py — `build_and_push_digest()` 修改
1. 函数签名新增参数：`pool_config: dict | None = None`
2. 当 `pool_config` 且 `pool_config.get("pool_ranking_enabled")` 为 True 时：
   - 调用 `pool_ranker.rank_with_pools()` 获取排序后的候选列表
   - 不再调用 `db.list_digest_candidates()`
3. 否则：走旧逻辑（`db.list_digest_candidates(score DESC)`）

### pipeline.py — `run_pipeline_job()` 修改
1. 从 job 配置读取 `pool_ranking_enabled`、`ai_quota`、`dev_quota`、`other_quota`、`ai_category_tags`、`dev_category_tags`
2. 构建 `pool_config` 字典传递给 `build_and_push_digest()`
3. 当分池排名开启时，先获取所有候选文章（不限 top_n），再交给 pool_ranker

### repository.py — 新增查询方法
新增 `list_all_digest_candidates()`：
- 与 `list_digest_candidates()` 类似，但不带 LIMIT
- 返回所有 `is_quality=1 AND composite_score >= threshold AND pushed_at IS NULL` 的文章
- ORDER BY composite_score DESC

## 验证
运行 G4、G6、G7、G11 的 cmd 测试项。
