# Ddo-Pulse Enhanced Content Pipeline Specification

> AI 基于用户原始需求与 context-summary.md 对需求的规约化理解。
> 仅描述 What / Why 与验收标准；技术方案见 plan.md。

---

## 1. 项目概述

### 1.1 项目名称
Ddo-Pulse Enhanced Content Pipeline

### 1.2 一句话定义
重构内容管线：引入源优先级分组、双维度评分、类别权重排名与推送配额均衡，同步更新后端分析流程与前端配置界面。

### 1.3 设计意图
- 当前管线仅按单一 score 降序取 top N，容易导致某一领域霸榜、遗漏其他领域高价值内容
- 引入源优先级分组（P0/P1/P2）可在抓取阶段就控制各源投入的分析资源
- 双维度评分（相关性 + 新颖度）比单一分数更能反映文章的综合价值
- 类别配额均衡确保每日推送覆盖多元领域
- **核心诉求：所有策略参数必须在前端定时任务配置界面可调**，用户无需改代码即可调整配额数、权重、抓取上限等数值，实现灵活的任务定制

---

## 2. 术语表（Glossary）

| 术语 | 定义 |
|---|---|
| 源优先级（Source Priority） | 将 RSS 源按重要性分为 P0（核心必读）、P1（高优）、P2（补充）三组 |
| 每源抓取上限（Per-Source Fetch Limit） | 每个源在单次运行中最多抓取的文章数（取最新 N 篇） |
| 相关性评分（Relevance Score） | LLM 对文章与读者兴趣匹配程度的评分，0~10 分 |
| 新颖度评分（Novelty Score） | LLM 对文章内容新颖程度的评分，0~10 分 |
| 综合得分（Composite Score） | 由相关性与新颖度加权计算得出的最终评分 |
| 类别配额（Category Quota） | 推送列表中各领域（AI、开发、综合）的固定篇数分配 |
| 分池排名（Pool-Based Ranking） | 先按类别分池、池内排序、再按配额截取的排名方式 |

---

## 3. 功能需求（Functional Requirements）

### 3.1 源优先级分组

- **FR-PRIO-1**：系统应支持为每个源关联（job_sources）配置优先级字段，取值范围为 P0、P1、P2
- **FR-PRIO-2**：每个优先级应可配置默认的每源抓取上限（P0=5, P1=4, P2=3），可通过 job 级配置覆盖
- **FR-PRIO-3**：分析阶段应优先处理高优先级源的文章，确保 P0 源的文章不会因全局 analyze_limit 而被截断
- **FR-PRIO-4**：前端定时任务配置界面应展示每个源的优先级，并支持编辑

### 3.2 每源抓取上限

- **FR-FETCH-1**：抓取阶段应根据源的优先级对应的抓取上限，仅保留最新的 N 篇文章（按 published_at 降序）
- **FR-FETCH-2**：当源的实际文章数少于抓取上限时，全部保留，不补零
- **FR-FETCH-3**：抓取上限可通过 job_sources.focus_config_json 中的 `fetch_limit` 字段按源覆盖

### 3.3 双维度评分

- **FR-SCORE-1**：LLM 分析输出应包含两个独立评分字段：`relevance`（相关性，0~10）和 `novelty`（新颖度，0~10）
- **FR-SCORE-2**：综合得分（composite_score）应由公式自动计算：`composite_score = relevance × relevance_weight + novelty × novelty_weight`
- **FR-SCORE-3**：权重默认值为 relevance_weight=0.6, novelty_weight=0.4，可通过 job 级配置调整
- **FR-SCORE-4**：原有的单一 `score` 字段保留向后兼容，当使用旧 prompt 模板时仍输出 `score`；新模板同时输出 `relevance` 和 `novelty`
- **FR-SCORE-5**：前端定时任务配置界面应支持调整权重值

### 3.4 类别配额与分池排名

- **FR-RANK-1**：推送选择应采用分池排名策略：先根据 LLM 输出的 `categories` 将合格文章分为 AI、开发、其他三个池
- **FR-RANK-2**：每个池应有可配置的配额（默认 AI=6, 开发=4, 其他=2），通过前端定时任务配置界面调整，配额总和即为推送数上限
- **FR-RANK-3**：池内排序应按综合得分（composite_score）降序
- **FR-RANK-4**：按配额从各池截取后，若某池文章不足，应从其他池的高分文章中补足，保持总推送数不变
- **FR-RANK-5**：最终推送列表应按综合得分全局降序重排
- **FR-RANK-6**：前端应支持配置各池的配额数量

### 3.5 推送数量调整

- **FR-PUSH-1**：默认推送数量应从 8 篇调整为 12 篇（DEFAULT_TOP_N = 12）
- **FR-PUSH-2**：digest_top_n 配置项保留，用户可自定义

### 3.6 前端配置界面

- **FR-UI-1**：定时任务编辑页面应新增「源优先级」配置区域，支持为每个关联源设置 P0/P1/P2
- **FR-UI-2**：定时任务编辑页面应新增「评分权重」配置区域，含 relevance_weight 和 novelty_weight 两个数字输入框（步长 0.1，范围 0~1，自动归一化提示）
- **FR-UI-3**：定时任务编辑页面应新增「类别配额」配置区域，含 AI、开发、其他三个数字输入框（步长 1，范围 0~20），配额总和即为实际推送数上限
- **FR-UI-4**：定时任务编辑页面应新增「每源抓取上限」配置区域，按 P0/P1/P2 分组显示默认值（P0=5, P1=4, P2=3），每个优先级均可独立修改
- **FR-UI-5**：所有新配置项应有合理的默认值，确保开箱即用（不配置时与当前行为一致）
- **FR-UI-6**：所有数值型配置项（配额数、权重、抓取上限）修改后实时生效，保存到 pipeline_jobs 配置中，下次定时运行自动应用
- **FR-UI-7**：类别配额配置区域应附带说明文字，解释配额不足时的自动补足规则
- **FR-UI-8**：「分池排名」功能应可通过开关启用/禁用；禁用时回退到现有的纯 score 降序排名

---

## 4. 产物与目录结构（What gets created）

```
# 后端新增/修改文件（示意，具体路径待 plan 阶段确定）
services/backend/
├── db/
│   └── schema.sql                    # 新增字段
├── core/ddo_pulse_core/
│   ├── analyzer/
│   │   ├── models.py                 # 新增 relevance, novelty 字段
│   │   ├── prompt.py                 # 新增双维度评分 prompt 模板
│   │   └── runner.py                 # 分析流程适配
│   ├── digest/
│   │   └── runner.py                 # 分池排名逻辑
│   ├── fetchers/
│   │   └── base.py                   # 按优先级截取逻辑
│   └── pipeline.py                   # 编排适配
└── db/ddo_pulse_db/
    └── repository.py                 # 新查询方法

# 前端修改文件（示意）
services/web/frontend/src/
├── views/SettingsView.vue            # 新增配置区域
├── api/client.ts                     # 新增类型定义
└── components/
    ├── SourcePrioritySelector.vue    # 新组件
    └── CategoryQuotaEditor.vue       # 新组件
```

---

## 5. 关键流程

```
配置来源：所有标 ★ 的参数均从前端定时任务配置界面读取

抓取阶段：
  for each source (按 P0 → P1 → P2 顺序):
    fetch all entries from feed
    sort by published_at DESC
    keep only top N (N = ★ fetch_limit，按优先级默认 P0=5/P1=4/P2=3，可覆盖)
    upsert into raw_items

分析阶段：
  for each source (P0 优先):
    dequeue unanalyzed raw_items (respecting per-source cap)
    for each item:
      LLM → { relevance, novelty, categories, summary_zh, reason }
      composite_score = relevance × ★ relevance_weight + novelty × ★ novelty_weight
      store in analyzed_items

推送选择阶段（★ 分池排名开关开启时）：
  candidates = all analyzed_items where is_quality=true AND composite_score >= threshold AND pushed_at IS NULL

  ai_pool    = candidates where categories contains ★ ai_category_tags 中的任一标签
  dev_pool   = candidates where categories contains ★ dev_category_tags 中的任一标签
  other_pool = candidates not in ai_pool or dev_pool

  sort each pool by composite_score DESC

  selected = ai_pool[:★ ai_quota] + dev_pool[:★ dev_quota] + other_pool[:★ other_quota]

  # 补足逻辑（配额不足时自动从其他池补足）：
  total_target = ★ ai_quota + ★ dev_quota + ★ other_quota
  while len(selected) < total_target and remaining pools have articles:
    从剩余最高分文章中补入

  sort selected by composite_score DESC (全局重排)
  limit to ★ digest_top_n

推送选择阶段（★ 分池排名开关关闭时，向后兼容）：
  使用现有逻辑：score DESC 取 top_n

推送阶段：
  build digest markdown + Feishu payload
  push to webhook
  mark as pushed
```

---

## 6. 约束与原则

- **C-1**：向后兼容——旧的 `score` 字段和 `is_quality` 逻辑不删除，仅在新 prompt 模式下使用双维度评分
- **C-2**：新字段（relevance, novelty, composite_score）应通过数据库 migration 添加，不影响已有数据
- **C-3**：分池排名逻辑应在后端 Python 中实现，不依赖 SQL 层面的复杂查询
- **C-4**：前端配置应有合理默认值，未配置时行为与当前版本一致（fallback 到单 score 排名）
- **C-5**：类别配额的"AI"和"开发"分类映射应可配置（即哪些 categories 标签归入 AI 池、开发池）
- **C-6**：所有策略参数（配额数、权重、抓取上限、分类标签映射）必须存储在 pipeline_jobs 配置中，通过前端修改，运行时读取——禁止硬编码

---

## 7. 验收标准（Acceptance Criteria）

- **AC-1**：配置 P0/P1/P2 优先级后，抓取阶段能正确按优先级截取文章数量
- **AC-2**：LLM 分析输出包含 relevance 和 novelty 两个独立评分字段
- **AC-3**：composite_score 按前端配置的权重自动计算；修改权重后下次运行即生效
- **AC-4**：推送列表按前端配置的类别配额均衡分配（默认 AI=6, 开发=4, 其他=2）
- **AC-5**：某池不足时，从其他池高分文章补足，总推送数不变
- **AC-6**：前端定时任务配置界面可独立修改以下所有参数：源优先级、每源抓取上限、评分权重、类别配额、分池排名开关
- **AC-7**：未配置新参数时，系统行为与当前版本一致（向后兼容）
- **AC-8**：修改配额数（如 AI 从 6 改为 8）后保存，下次定时运行自动按新配额执行

---

## 8. 非功能需求（Non-Functional）

- **NFR-1**：分池排名算法的额外延迟应不超过 100ms（在 100 篇文章规模下）
- **NFR-2**：数据库 migration 应可安全重复执行（幂等）
- **NFR-3**：前端新配置区域应响应式布局，适配移动端

---

## 9. 范围说明（In / Out of Scope）

### In Scope
- 后端：数据库 schema 变更、分析器双维度评分、分池排名算法、抓取阶段按优先级截取
- 前端：定时任务配置界面新增源优先级、评分权重、类别配额、每源抓取上限的配置 UI
- API：pipeline_jobs 和 job_sources 的 CRUD 接口扩展

### Out of Scope
- 飞书推送格式变更（当前格式保持不变）
- 已推送文章的重新排名或回溯
- 多 job 之间的源优先级共享（每个 job 独立配置）
- 移动端原生 App 适配

---

## 10. 开放问题（Open Questions，待 Plan 阶段决策）

- **Q-1**：分池时，"AI 相关"的 categories 标签集合应该如何定义？是硬编码还是通过配置项（如 `ai_category_tags`）指定？
- **Q-2**：relevance 和 novelty 是否需要存储为 analyzed_items 表的新列，还是存储在 deep_analysis_json 中？
- **Q-3**：composite_score 是存储为物理列还是查询时计算？
- **Q-4**：源优先级是存储在 job_sources.focus_config_json 中，还是在 job_sources 表上新增 `priority` 列？
- **Q-5**：前端的评分权重配置使用滑块（slider）还是数字输入框？
- **Q-6**：抓取阶段的截取逻辑是在 fetcher 层实现还是在 pipeline 层 post-filter？

---

## 11. 用户确认

请确认以下任一选项：

- ✅ **同意**：本 spec 符合预期，可进入 **Planning** 阶段生成 `plan.md`。
- ❌ **修改**：请在下方/对话中列出需要调整的条款编号与意见，AI 将基于反馈重新生成本文档。
