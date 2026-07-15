# Task-07: 前端类型定义与配置组件

## 关联验收点
- G8: 前端配置 — Pipeline Job API
- G9: 前端配置 — 源优先级

## 目标
新增前端类型定义和三个配置组件。

## 修改文件
- `services/web/frontend/src/api/client.ts`
- `services/web/frontend/src/components/SourcePrioritySelector.vue`（新建）
- `services/web/frontend/src/components/ScoringWeightEditor.vue`（新建）
- `services/web/frontend/src/components/CategoryQuotaEditor.vue`（新建）

## 具体改动

### client.ts
PipelineJob 类型新增：
```typescript
pool_ranking_enabled: number
ai_quota: number
dev_quota: number
other_quota: number
relevance_weight: number
novelty_weight: number
ai_category_tags: string
dev_category_tags: string
```

JobSource 类型新增：
```typescript
priority: string
fetch_limit: number | null
```

### SourcePrioritySelector.vue（新建）
- 展示当前 job 关联的所有源
- 每个源显示：名称、类型、当前优先级（P0/P1/P2 下拉选择）
- 支持编辑 fetch_limit（数字输入框，留空则用优先级默认值）
- 通过 emit 向父组件传递变更

### ScoringWeightEditor.vue（新建）
- 两个数字输入框：relevance_weight（step=0.1, 0~1）和 novelty_weight（step=0.1, 0~1）
- 显示 composite_score 公式预览
- 通过 emit 向父组件传递变更

### CategoryQuotaEditor.vue（新建）
- 三个数字输入框：AI 配额、开发配额、其他配额（step=1, 0~20）
- 显示配额总和
- 显示补足规则说明文字
- 分池排名开关（toggle）
- 通过 emit 向父组件传递变更

## 验证
运行 G8、G9 的 human 测试项。
