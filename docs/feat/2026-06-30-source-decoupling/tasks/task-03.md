# Task-03: Repository 层适配

## 目标
修改 `repository.py`，适配新的表结构，新增 `job_sources` 相关的 CRUD 方法，修改现有 source 方法移除 job_id 依赖。

## 关联验收点
- G1: DB Schema 变更与数据迁移
- G3: 信息源与定时任务解耦
- G4: Per-Source 关注点配置

## 变更文件
- `services/backend/db/ddo_pulse_db/repository.py`

## 具体变更

### 修改现有方法
1. `add_source()` — 移除 `job_id` 参数
2. `list_sources()` — 移除 `job_id` 过滤参数
3. `update_source()` — 移除 `job_id` 参数
4. `upsert_source_by_url()` — 移除 `job_id` 参数
5. `delete_all_sources()` — 移除 `job_id` 参数
6. `import_sources_from_yaml()` — 移除 job_id 逻辑
7. `get_first_pipeline_job_id()` — 可移除（不再需要）

### 新增 job_sources 方法
1. `add_job_source(job_id, source_id, focus_config_json='{}', enabled=True)` — 关联源到 job
2. `remove_job_source(job_id, source_id)` — 取消关联
3. `list_job_sources(job_id)` — 列出 job 关联的 sources（JOIN 查询）
4. `update_job_source_focus(job_id, source_id, focus_config_json)` — 更新关注点配置
5. `set_job_source_enabled(job_id, source_id, enabled)` — 启用/禁用关联
6. `get_job_source(job_id, source_id)` — 获取单个关联记录

## 验收
- 所有现有 source 操作不再依赖 job_id
- job_sources CRUD 方法可正常工作
- Pipeline 执行可通过 `list_job_sources(job_id)` 获取关联源及关注点配置
