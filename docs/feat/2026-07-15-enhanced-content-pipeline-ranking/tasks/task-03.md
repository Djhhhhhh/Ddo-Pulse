# Task-03: Fetch 阶段按优先级截取

## 关联验收点
- G5: Fetch 阶段 — 按优先级截取

## 目标
抓取阶段按源优先级排序，每源按 fetch_limit 截取最新 N 篇。

## 修改文件
- `services/backend/core/ddo_pulse_core/pipeline.py`

## 具体改动

### pipeline.py — `_fetch_sources()` 修改
1. 在函数签名中新增参数 `priority_map: dict[int, str] | None = None`
2. fetch 之后、upsert 之前加入截取逻辑：
   - 若 source 有 fetch_limit（从 focus_config_json 或优先级默认值），对 items 按 published_at 降序排序，取前 N 篇
   - 优先级默认值：P0=5, P1=4, P2=3

### pipeline.py — `run_pipeline_job()` 修改
1. 从 job_sources 的 focus_configs 中读取 priority 和 fetch_limit
2. 构建 `priority_map` 和 `fetch_limit_map`
3. 按优先级排序 sources 列表（P0 → P1 → P2）
4. 传递给 `_fetch_sources()`

## 验证
运行 G5 的 cmd 测试项。
