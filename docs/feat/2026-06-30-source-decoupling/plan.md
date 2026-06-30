# Ddo-Pulse 信息源逻辑重构 Plan

> 基于已确认的 spec.md 做技术决策。

---

## 1. 决策原则

| # | 原则 | 落地体现 |
|---|------|----------|
| P-1 | 最小侵入 | 复用现有 repository 方法（如 `get_source_by_url`），减少新增代码 |
| P-2 | URL 作为信息源唯一标识 | CSV 中每行的 `rss_url` 即为 source 的唯一键，全量覆盖时按 URL 匹配 |
| P-3 | 关注点配置与源基础信息分离 | 源的基础信息（名称、URL、类型）来自 CSV；关注点配置在 `job_sources` 关联表中维护 |
| P-4 | 向后兼容 | 保留 `raw_items`、`analyzed_items` 等历史数据，source_id 不变 |

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────┐
│  docs/ddo_pulse_rss_seed_library.csv                    │
│  (用户手动维护的信息源权威来源)                               │
└────────────────────┬────────────────────────────────────┘
                     │ 前端「全量覆盖」按钮
                     ▼
┌─────────────────────────────────────────────────────────┐
│  POST /api/sources/sync-from-csv                        │
│  ┌─────────────┐    ┌──────────────┐                    │
│  │ 解析 CSV     │───▶│ 全量同步 sources 表               │
│  │ 按 URL 匹配  │    │ (upsert by url)                  │
│  └─────────────┘    └──────────────┘                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  sources 表 (全局实体，无 job_id)                          │
│  ┌──────────────────────────────────┐                   │
│  │ id | name | type | url | ...     │                   │
│  └──────────────────────────────────┘                   │
└────────────────────┬────────────────────────────────────┘
                     │ N:N 关联
                     ▼
┌─────────────────────────────────────────────────────────┐
│  job_sources 关联表 (含 per-source 关注点配置)              │
│  ┌──────────────────────────────────────────┐           │
│  │ job_id | source_id | focus_config_json   │           │
│  └──────────────────────────────────────────┘           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  pipeline_jobs 表 (定时任务，不变)                          │
│  ┌──────────────────────────────────┐                   │
│  │ id | name | schedule_cron | ...  │                   │
│  └──────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

**关键事实：**
- sources 表移除 `job_id` 外键，成为全局独立实体
- 新增 `job_sources` 关联表实现 pipeline_jobs ↔ sources 多对多关系
- `job_sources.focus_config_json` 存储 per-source 的关注点配置
- CSV 全量覆盖按 `url` 字段匹配，幂等操作

---

## 3. 核 Schema

### 3.1 sources 表（变更）

```sql
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,          -- 新增 UNIQUE 约束
    config_json TEXT DEFAULT '{}',
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
-- 移除 job_id 列及其索引
-- 新增 UNIQUE 约束于 url
```

**字段语义约束：**
- `url`：信息源的入口 URL，作为全局唯一标识。CSV 同步时按此字段匹配。
- `config_json`：源级别的通用配置（如 CSS 选择器、浏览器 Profile 等），来自 CSV 中可解析的字段。
- `enabled`：源级别的全局启用状态。CSV 同步时默认启用。

### 3.2 job_sources 关联表（新增）

```sql
CREATE TABLE IF NOT EXISTS job_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES pipeline_jobs(id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    focus_config_json TEXT NOT NULL DEFAULT '{}',
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    UNIQUE(job_id, source_id)
);
```

**字段语义约束：**
- `job_id`：关联的定时任务 ID。
- `source_id`：关联的信息源 ID。
- `focus_config_json`：per-source 的关注点配置 JSON，结构如下：

```jsonc
{
  "interest_keywords": ["AI", "LLM"],    // 该源关注的关键词（覆盖 job 级别）
  "need_llm_analysis": true,              // 是否需要 LLM 分析
  "need_content_extraction": false,       // 是否需要网页正文提取
  "analyze_limit": 50,                    // 该源的分析条数限制
  "custom_prompt_hint": "关注模型发布"      // 自定义 prompt 提示（可选）
}
```

- `enabled`：该关联是否启用（禁用后 job 执行时跳过此源，但不删除关联）。

### 3.3 校验

- `job_sources` 表的 `(job_id, source_id)` 唯一约束防止重复关联
- `sources.url` 唯一约束确保 CSV 同步时的幂等性
- 删除 source 时 CASCADE 删除 `job_sources` 和 `raw_items`
- 删除 pipeline_job 时 CASCADE 删除 `job_sources`（但不删除 source）

---

## 4. 关键算法 / 流程

### 4.1 CSV 全量覆盖同步

**触发**：前端点击「全量覆盖信息源」→ `POST /api/sources/sync-from-csv`

**步骤：**
1. 读取 `docs/ddo_pulse_rss_seed_library.csv` 文件
2. 解析每行为 source 记录：`name` ← 源名称, `type` ← 源类型, `url` ← rss_url
3. 对 CSV 中每个源：
   - 按 `url` 查询 `sources` 表
   - 存在 → 更新 `name`, `type`, `config_json`（保留 `enabled` 和 `created_at`）
   - 不存在 → 插入新记录
4. CSV 中不存在的已有源：**保留不动**（Q-1 决策）
5. 返回同步结果（新增数、更新数、跳过数）

**幂等性保证**：多次执行结果一致（upsert by url）。

### 4.2 Pipeline Job 执行（适配后）

**变更点**：`run_pipeline_job()` 中加载 sources 的逻辑从 `WHERE job_id = ?` 改为通过 `job_sources` 关联表查询。

**步骤：**
1. 加载 job 配置（不变）
2. 查询 `job_sources JOIN sources` 获取该 job 关联的 enabled sources 及其 `focus_config_json`
3. 对每个 source：
   - 读取 `focus_config_json` 覆盖 job 级别配置
   - 使用 fetcher 抓取（不变）
   - 按 `focus_config_json.need_llm_analysis` 决定是否 LLM 分析
   - 按 `focus_config_json.analyze_limit` 限制分析条数
   - 按 `focus_config_json.interest_keywords` 做关键词预过滤（若启用）
4. 聚合 digest → 推送（不变）

---

## 5. 错误处理与回退

| 触发条件 | 行为 |
|---------|------|
| CSV 文件不存在 | 返回 400 错误，提示用户先创建文件 |
| CSV 格式错误（缺少必要列） | 返回 400 错误，提示缺少的列名 |
| CSV 中有重复 URL | 取最后一条（按行号覆盖） |
| CSV 中 source 类型不在已知枚举中 | 跳过该行，记录 warning |
| 同步过程中 DB 错误 | 事务回滚，返回 500 错误 |

---

## 6. 风险与权衡

| # | 风险 | 描述 | 处置 |
|---|------|------|------|
| R-1 | 历史数据迁移 | 移除 sources.job_id 后，现有 source 的关联关系丢失 | 迁移脚本：将现有 `sources.job_id` 写入 `job_sources` 表 |
| R-2 | raw_items 外键 | `raw_items.source_id` 引用 sources(id)，解耦后 source 可能被删除 | 保持 CASCADE 删除行为；CSV 同步不删除源 |
| R-3 | 前端 UI 变化大 | Settings 页面需要重构源管理逻辑 | 渐进式：先实现 CSV 同步按钮，再优化 per-source 配置 UI |
| R-4 | CSV 列名与 DB 字段映射 | CSV 中的列名（中文）与 DB 字段名不一致 | API 层做映射转换 |

---

## 7. 实施次序（高层路线，供 Tasking 拆分参考）

1. **Phase 1 — DB Schema 变更**
   - 修改 `schema.sql`：移除 `sources.job_id`，新增 `job_sources` 表
   - 编写迁移脚本：将现有 `sources.job_id` 数据迁移到 `job_sources`
   - 修改 `repository.py`：适配新的表结构

2. **Phase 2 — CSV 同步 API**
   - 新增 `POST /api/sources/sync-from-csv` 端点
   - 实现 CSV 解析和全量覆盖逻辑
   - 复用现有 CSV 文件路径

3. **Phase 3 — Pipeline 适配**
   - 修改 `pipeline.py`：通过 `job_sources` 关联表加载 sources
   - 读取 `focus_config_json` 覆盖 job 级别配置
   - 修改 `scheduler.py`：无需变更（scheduler 只关心 pipeline_jobs）

4. **Phase 4 — 前端 UI**
   - 添加「全量覆盖信息源」按钮
   - 修改源列表展示：显示 per-source 关注点配置入口
   - 添加 per-source 关注点编辑对话框

5. **Phase 5 — API 端点补全**
   - `POST /api/pipeline-jobs/{job_id}/sources` — 关联源到 job
   - `PATCH /api/pipeline-jobs/{job_id}/sources/{source_id}` — 更新关注点配置
   - `DELETE /api/pipeline-jobs/{job_id}/sources/{source_id}` — 取消关联

---

## 8. 与 spec 的开放问题对应表

| spec Open Question | plan 中的落地 |
|---|---|
| Q-1：CSV 中不存在但 DB 中已有的源如何处理？ | 第 4.1 节：保留不动。源是全局实体，可能被多个 job 引用，不应因 CSV 变化而删除。 |
| Q-2：信息源匹配标识用什么字段？ | 第 3.1 节：URL 唯一。`sources.url` 加 UNIQUE 约束，CSV 同步按 url 匹配。 |
| Q-3：关注点配置的具体字段清单？ | 第 3.2 节：`focus_config_json` 包含 `interest_keywords`、`need_llm_analysis`、`need_content_extraction`、`analyze_limit`、`custom_prompt_hint`。 |
| Q-4：现有 CSV 是否直接复用？ | 第 4.1 节：直接复用 `docs/ddo_pulse_rss_seed_library.csv`。 |
| Q-5：历史数据迁移方案？ | 第 6 节 R-1：迁移脚本将现有 `sources.job_id` 写入 `job_sources` 表，source_id 保持不变。 |

---

## 9. 用户确认

请确认以下任一选项：

- ✅ **同意**：本 plan 符合预期，可进入 **Test-Planning** 阶段生成 `test-plan.md`。
- ❌ **修改**：请在下方/对话中列出需要调整的章节与意见，AI 将基于反馈重新生成本文档。
