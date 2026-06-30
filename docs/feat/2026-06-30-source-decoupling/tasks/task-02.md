# Task-02: 数据迁移脚本

## 目标
编写迁移脚本，将现有 `sources.job_id` 数据迁移到 `job_sources` 关联表，确保升级后数据不丢失。

## 关联验收点
- G1: DB Schema 变更与数据迁移

## 变更文件
- `services/backend/db/ddo_pulse_db/repository.py`（新增迁移方法）

## 具体变更

在 `Database` 类中新增迁移方法 `_migrate_sources_to_job_sources()`：
1. 检查 `sources` 表是否存在 `job_id` 列（`PRAGMA table_info(sources)`）
2. 如果存在：
   - 确保 `job_sources` 表已创建
   - `INSERT OR IGNORE INTO job_sources (job_id, source_id, focus_config_json, enabled, created_at) SELECT job_id, id, '{}', enabled, created_at FROM sources WHERE job_id IS NOT NULL`
   - 使用 `ALTER TABLE sources DROP COLUMN job_id`（SQLite 3.35+ 支持）或重建表
3. 在 `conn` property 中调用此迁移方法（与现有迁移方法并列）

## 验收
- 从旧版 schema 升级后，sources 表无 job_id 列
- job_sources 表中包含原有关联数据
- raw_items 等下游数据不受影响
