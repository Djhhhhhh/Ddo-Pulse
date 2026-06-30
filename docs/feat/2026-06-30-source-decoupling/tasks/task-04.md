# Task-04: CSV 全量覆盖同步 API

## 目标
新增 `POST /api/sources/sync-from-csv` 端点，读取 `docs/ddo_pulse_rss_seed_library.csv` 并全量同步到 sources 表。

## 关联验收点
- G2: CSV 全量覆盖同步 API

## 变更文件
- `services/backend/api/ddo_pulse_api/api_routes.py`（新增端点）

## 具体变更

### 新增端点 `POST /api/sources/sync-from-csv`

**逻辑：**
1. 读取 CSV 文件路径：`<project_root>/docs/ddo_pulse_rss_seed_library.csv`
2. 解析 CSV（使用 `csv.DictReader`），列映射：
   - `源名称` → `name`
   - `源类型` → `type`（需要映射：RSS → rss, 官方博客 → rss, 论文聚合 → rss, 等）
   - `rss_url` → `url`（跳过空 URL 的行）
   - 其他列 → `config_json`
3. 对 CSV 中每个有效源（url 非空）：
   - 调用 `db.upsert_source_by_url(url, name, type, config_json)`
4. 返回 JSON：`{ "added": N, "updated": M, "skipped": K, "total": T }`

**类型映射规则：**
- 包含 "RSS" 或 "rss" → `rss`
- 包含 "JSON" → `json_feed`
- 包含 "HTML" 或 "网页" → `html_list`
- 包含 "浏览器" → `browser_session`
- 默认 → `rss`

**错误处理：**
- CSV 文件不存在 → 400 错误
- CSV 格式错误 → 400 错误
- 源类型未知 → 跳过，计入 skipped

## 验收
- 运行 test-plan G2 中所有 cmd 检查项
