# Task-05: Pipeline 执行适配

## 目标
修改 `pipeline.py`，通过 `job_sources` 关联表加载 sources，读取 `focus_config_json` 进行差异化处理。

## 关联验收点
- G7: Pipeline 执行适配

## 变更文件
- `services/backend/core/ddo_pulse_core/pipeline.py`

## 具体变更

### 修改 `run_pipeline_job()` 函数
1. 将 `database.list_sources(enabled_only=True, job_id=job_id)` 替换为 `database.list_job_sources(job_id)`
2. 返回结果包含 source 基础信息 + `focus_config_json`
3. 解析 `focus_config_json`，覆盖 job 级别配置：
   - `need_llm_analysis: false` → 跳过 LLM 分析
   - `analyze_limit` → 覆盖 job 的 `analyze_limit`
   - `interest_keywords` → 覆盖 job 的 `interest_keywords_json`
   - `need_content_extraction: true` → 启用正文抓取
4. 按 `focus_config_json` 中的配置差异化处理每个 source

### 修改 `_fetch_sources()` 函数
- 接收参数增加 `focus_configs: dict[int, dict]`（source_id → focus_config）
- 传递给后续分析步骤

### 修改 `_analyze_items()` 函数
- 读取 per-source 的 `need_llm_analysis` 和 `analyze_limit`
- 跳过 `need_llm_analysis: false` 的源
- 使用 per-source `analyze_limit` 覆盖全局限制

## 验收
- 运行 test-plan G7 中所有 cmd 检查项
