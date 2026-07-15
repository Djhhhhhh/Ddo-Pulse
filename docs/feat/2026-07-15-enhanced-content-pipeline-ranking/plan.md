# Ddo-Pulse Enhanced Content Pipeline Plan

> 基于已确认的 spec.md 做技术决策：定 schema、定通信方式、定运行时模型、定关键算法、定取舍。

---

## 1. 决策原则

| # | 原则 | 落地体现 |
|---|------|----------|
| P-1 | 配置优先 | 所有策略参数（配额、权重、抓取上限、分类标签映射）存入 pipeline_jobs 配置，前端可调，禁止硬编码 |
| P-2 | 向后兼容 | 旧的 `score` 字段保留；新字段通过 ALTER TABLE 添加；未配置新参数时走旧逻辑 |
| P-3 | 最小侵入 | 复用现有 `_fetch_sources`、`analyze_job_sources`、`build_and_push_digest` 函数签名，通过参数扩展而非重写 |
| P-4 | 物理存储评分 | relevance、novelty、composite_score 存为 analyzed_items 的物理列，避免查询时重复计算 |
| P-5 | 优先级即一等公民 | source 优先级存为 job_sources 表的独立列，不埋在 JSON 中 |

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Vue 3)                         │
│  SettingsView → Pipeline Job Editor                          │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────────────┐ │
│  │ 源优先级选择 │ │ 评分权重配置 │ │ 类别配额 + 分池开关  │ │
│  └──────┬──────┘ └──────┬───────┘ └───────────┬───────────┘ │
└─────────┼───────────────┼─────────────────────┼─────────────┘
          │               │                     │
          ▼               ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                          │
│  PUT /pipeline-jobs/{id}  →  存储所有新配置字段               │
│  PUT /pipeline-jobs/{id}/sources/{sid}  →  存储优先级         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Pipeline Runner                            │
│  1. Fetch: 按优先级排序源 → 每源截取 fetch_limit 篇          │
│  2. Analyze: LLM → {relevance, novelty, categories, ...}    │
│              composite_score = R×rw + N×nw                   │
│  3. Digest: 分池(ai/dev/other) → 池内排序 → 按配额截取       │
│             → 补足 → 全局重排 → 推送                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   SQLite Database                            │
│  pipeline_jobs: +ai/dev/other_quota, +relevance/novelty_wt  │
│  job_sources:   +priority, +fetch_limit                     │
│  analyzed_items:+relevance, +novelty, +composite_score      │
└─────────────────────────────────────────────────────────────┘
```

关键事实：
- 前后端通过 RESTful API 通信，配置变更通过 PUT 请求持久化
- pipeline_jobs 表存储所有策略参数（配额、权重、分类标签映射、分池开关）
- job_sources 表新增 priority 列和 fetch_limit 列
- analyzed_items 表新增 relevance、novelty、composite_score 列
- 分池排名逻辑在 Python 层实现，不依赖复杂 SQL

---

## 3. 目录与命名（最终定版）

```
services/backend/
├── db/
│   ├── schema.sql                           # 修改：新增列
│   └── migrations/
│       └── 003_enhanced_pipeline_config.sql  # 新增：migration 脚本
├── core/ddo_pulse_core/
│   ├── analyzer/
│   │   ├── models.py                        # 修改：新增 relevance, novelty 字段
│   │   ├── prompt.py                        # 修改：新增双维度评分 prompt 模板
│   │   └── runner.py                        # 修改：适配新字段存储
│   ├── digest/
│   │   ├── runner.py                        # 修改：新增分池排名逻辑
│   │   └── pool_ranker.py                   # 新增：分池排名算法
│   ├── fetchers/
│   │   └── rss.py                           # 不修改（fetcher 保持通用）
│   └── pipeline.py                          # 修改：fetch 阶段按优先级截取
├── db/ddo_pulse_db/
│   └── repository.py                        # 修改：新增查询方法、更新插入方法
└── api/ddo_pulse_api/
    └── routes/
        └── pipeline_jobs.py                 # 修改：API 支持新字段

services/web/frontend/src/
├── views/SettingsView.vue                   # 修改：新增配置区域
├── api/client.ts                            # 修改：新增类型定义
└── components/
    ├── SourcePrioritySelector.vue           # 新增：源优先级选择器
    ├── CategoryQuotaEditor.vue              # 新增：类别配额编辑器
    └── ScoringWeightEditor.vue              # 新增：评分权重编辑器
```

---

## 4. 核心 Schema

### 4.1 pipeline_jobs 表新增字段

```sql
-- 分池排名开关
pool_ranking_enabled INTEGER NOT NULL DEFAULT 0,

-- 类别配额
ai_quota INTEGER NOT NULL DEFAULT 6,
dev_quota INTEGER NOT NULL DEFAULT 4,
other_quota INTEGER NOT NULL DEFAULT 2,

-- 评分权重（存储为 REAL，0.0~1.0）
relevance_weight REAL NOT NULL DEFAULT 0.6,
novelty_weight REAL NOT NULL DEFAULT 0.4,

-- 分类标签映射（JSON 数组）
ai_category_tags TEXT NOT NULL DEFAULT '["AI","机器学习","深度学习","LLM","大模型","NLP","CV","论文"]',
dev_category_tags TEXT NOT NULL DEFAULT '["开发","工程","架构","DevOps","工具","前端","后端","数据库"]'
```

字段语义约束：
- `pool_ranking_enabled`：0=禁用（回退到纯 score 排名），1=启用分池排名
- `ai_quota` / `dev_quota` / `other_quota`：各池推送篇数上限，总和即为实际推送数上限
- `relevance_weight` / `novelty_weight`：加权评分权重，不要求和为 1.0（composite_score 是加权和而非加权平均）
- `ai_category_tags` / `dev_category_tags`：JSON 数组，LLM 输出的 categories 命中任一标签即归入对应池

校验：
- quota 值 >= 0
- weight 值 >= 0.0
- tags 为合法 JSON 数组

### 4.2 job_sources 表新增字段

```sql
priority TEXT NOT NULL DEFAULT 'P1',
fetch_limit INTEGER
```

字段语义约束：
- `priority`：'P0' / 'P1' / 'P2'，决定抓取阶段的处理顺序和默认 fetch_limit
- `fetch_limit`：每源抓取上限，NULL 时使用优先级默认值（P0=5, P1=4, P2=3）

校验：
- priority IN ('P0', 'P1', 'P2')
- fetch_limit > 0 OR fetch_limit IS NULL

### 4.3 analyzed_items 表新增字段

```sql
relevance INTEGER,
novelty INTEGER,
composite_score REAL
```

字段语义约束：
- `relevance`：相关性评分 0~10，由 LLM 输出
- `novelty`：新颖度评分 0~10，由 LLM 输出
- `composite_score`：由 `relevance × relevance_weight + novelty × novelty_weight` 计算得出，写入时按 job 配置的权重计算后存储

校验：
- relevance BETWEEN 0 AND 10 (or NULL)
- novelty BETWEEN 0 AND 10 (or NULL)

---

## 5. 关键算法 / 流程

### 5.1 Fetch 阶段：按优先级截取

```
输入：sources 列表（每项含 priority, fetch_limit）
输出：截取后的 items 写入 raw_items

步骤：
1. 按优先级排序：P0 源先处理，其次 P1，最后 P2
2. 对每个源：
   a. fetcher.fetch() 获取所有条目
   b. 按 published_at 降序排序
   c. 截取前 N 篇（N = fetch_limit，若为 NULL 则用优先级默认值）
   d. upsert 到 raw_items
```

实现位置：在 `_fetch_sources()` 函数中，fetch 之后、upsert 之前加入截取逻辑。不修改 fetcher 本身。

### 5.2 Analyze 阶段：双维度评分

```
输入：raw_item (title, content)
输出：AnalysisOutput { is_quality, relevance, novelty, categories, summary_zh, reason }

prompt 模板变更：
- 新增 DUAL_SCORE_PROMPT_TEMPLATE，要求 LLM 输出 relevance 和 novelty 两个字段
- 保留旧的 DEFAULT_PROMPT_TEMPLATE 作为 fallback

composite_score 计算：
  composite_score = relevance × relevance_weight + novelty × novelty_weight
  其中 relevance_weight 和 novelty_weight 从 job 配置读取
```

实现位置：
- `analyzer/prompt.py`：新增 `DUAL_SCORE_PROMPT_TEMPLATE`
- `analyzer/models.py`：新增可选字段 relevance、novelty
- `analyzer/runner.py`：分析完成后计算 composite_score 并存储

### 5.3 Digest 阶段：分池排名

```
输入：candidates（所有 is_quality=true, composite_score >= threshold, pushed_at IS NULL 的文章）
输出：最终推送列表（top_n 篇）

步骤：
1. 若 pool_ranking_enabled = 0：走旧逻辑（score DESC 取 top_n）
2. 若 pool_ranking_enabled = 1：
   a. 分池：
      ai_pool = candidates where any(category ∈ ai_category_tags)
      dev_pool = candidates where any(category ∈ dev_category_tags)
      other_pool = candidates not in ai_pool or dev_pool

   b. 池内排序：每池按 composite_score DESC

   c. 按配额截取：
      selected = ai_pool[:ai_quota] + dev_pool[:dev_quota] + other_pool[:other_quota]

   d. 补足逻辑：
      total_target = ai_quota + dev_quota + other_quota
      remaining = 所有未选中的候选文章，按 composite_score DESC 排序
      while len(selected) < total_target and remaining:
          selected.append(remaining.pop(0))

   e. 全局重排：selected 按 composite_score DESC
   f. 截取：selected[:top_n]
```

实现位置：新建 `digest/pool_ranker.py`，`digest/runner.py` 调用它。

### 5.4 LLM Prompt 模板：双维度评分

新增 `DUAL_SCORE_PROMPT_TEMPLATE`，与现有模板结构一致，但输出字段变为 relevance 和 novelty：

```
输出 JSON 格式：
{
  "is_quality": true,
  "relevance": 8,
  "novelty": 7,
  "categories": ["AI"],
  "summary_zh": "50-120 字中文摘要",
  "reason": "一句话说明评分理由"
}

评分标准：
- relevance（相关性）：0-10 分，衡量文章与读者兴趣领域的匹配程度
- novelty（新颖度）：0-10 分，衡量文章内容的新鲜程度和创新性
- is_quality 为 true 表示 relevance >= 7 或 novelty >= 7
```

---

## 6. 错误处理与回退

| 触发条件 | 行为 |
|---|---|
| LLM 输出缺少 relevance 或 novelty 字段 | 尝试用 `_salvage_analysis_json` 提取；若仍缺失，fallback 到旧 score 字段，composite_score = score |
| composite_score 计算结果为 NULL（两个维度都缺失） | 使用旧 score 作为 composite_score 的近似值 |
| 分池时某池为空 | 该池配额跳过，从其他池补足 |
| 所有池都为空 | 回退到旧逻辑：按 score DESC 取 top_n |
| ai_category_tags 或 dev_category_tags 为空数组 | 对应池永远为空，所有文章归入 other_pool |
| fetch_limit 为 NULL 且 priority 无效 | 使用全局默认值 P1=4 |
| 数据库 migration 重复执行 | ALTER TABLE IF NOT EXISTS，幂等安全 |

---

## 7. 风险与权衡

| # | 风险 | 描述 | 处置 |
|---|------|------|------|
| R-1 | LLM 不稳定输出双维度评分 | 旧模型可能不输出 relevance/novelty 字段 | 保留旧 prompt 模板作为 fallback；缺失字段时用 score 近似 |
| R-2 | 分池导致推送数不足 | 某池文章太少，配额用不完 | 自动补足逻辑确保总推送数不变 |
| R-3 | 分类标签映射不准确 | LLM 输出的 categories 标签可能不在 ai/dev 标签集合中 | 归入 other_pool；用户可通过前端调整标签集合 |
| R-4 | 物理存储 composite_score 的一致性 | 修改权重后，已存储的 composite_score 与新权重不一致 | 仅影响未推送文章；已推送文章不受影响（pushed_at IS NULL 过滤） |
| R-5 | 前端配置项过多 | 新增 6+ 个配置区域，界面复杂度上升 | 分组展示（评分策略 / 推送配额 / 源管理），默认值开箱即用 |

---

## 8. 实施次序（高层路线，供 Tasking 拆分参考）

1. **数据库 Migration**：ALTER TABLE 新增列（pipeline_jobs、job_sources、analyzed_items）
2. **后端 - 分析器**：models.py 新增字段、prompt.py 新增双维度模板、runner.py 适配
3. **后端 - Pipeline**：_fetch_sources 按优先级截取、run_pipeline_job 读取新配置
4. **后端 - 分池排名**：新建 pool_ranker.py、修改 digest/runner.py
5. **后端 - API/Repository**：CRUD 支持新字段、新增查询方法
6. **前端 - 类型定义**：client.ts 新增字段类型
7. **前端 - 配置组件**：源优先级选择器、评分权重编辑器、类别配额编辑器
8. **前端 - SettingsView**：集成新组件到定时任务编辑页面

---

## 9. 与 spec 的开放问题对应表

| spec Open Question | plan 中的落地 |
|---|---|
| Q-1: 分池时 AI/开发的 categories 标签集合如何定义？ | §4.1：pipeline_jobs 新增 `ai_category_tags` 和 `dev_category_tags` JSON 数组字段，前端可配置，默认值覆盖常见标签 |
| Q-2: relevance 和 novelty 存新列还是 JSON？ | §4.3：analyzed_items 新增 `relevance` 和 `novelty` 物理列，便于查询和排序 |
| Q-3: composite_score 物理存储还是计算字段？ | §4.3：物理列为 `composite_score REAL`，写入时按 job 配置的权重计算后存储 |
| Q-4: 源优先级存 focus_config_json 还是新列？ | §4.2：job_sources 新增 `priority TEXT` 和 `fetch_limit INTEGER` 独立列 |
| Q-5: 前端权重用滑块还是输入框？ | §3：使用数字输入框（step=0.1），精确可控 |
| Q-6: 截取逻辑在 fetcher 层还是 pipeline 层？ | §5.1：在 pipeline 层的 `_fetch_sources()` 中 post-filter，不修改 fetcher |

---

## 10. 用户确认

请确认以下任一选项：

- ✅ **同意**：本 plan 符合预期，可进入 **Test-Planning** 阶段生成 `test-plan.md`。
- ❌ **修改**：请在下方/对话中列出需要调整的章节与意见，AI 将基于反馈重新生成本文档。
