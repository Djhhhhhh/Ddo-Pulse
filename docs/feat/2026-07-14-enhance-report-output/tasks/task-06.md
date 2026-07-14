# Task 06: 数据库迁移（deep_analysis_json）

## 关联验收点
- G2: 深度解读功能

## 任务描述
为 `analyzed_items` 表添加 `deep_analysis_json` 字段。

## 具体步骤

1. 更新 `db/schema.sql`：
   - 添加 `deep_analysis_json TEXT` 字段

2. 更新 `db/ddo_pulse_db/repository.py`：
   - 添加迁移方法 `_migrate_analyzed_items_deep_analysis()`
   - 更新 `insert_analyzed_item()` 方法支持新字段

3. 更新 `tools/analyzers/llm_analyzer.py`：
   - 解析深度解读 JSON
   - 存储到 `deep_analysis_json`

## 输出文件
- 修改 `services/backend/db/schema.sql`
- 修改 `services/backend/db/ddo_pulse_db/repository.py`

## Schema 变更
```sql
ALTER TABLE analyzed_items ADD COLUMN deep_analysis_json TEXT;
```

## 验证命令
```bash
grep -q "deep_analysis_json" services/backend/db/schema.sql && echo "Field exists"
```
