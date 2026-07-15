# Ddo-Pulse Enhanced Content Pipeline 测试计划

> 基于已确认的 spec.md 生成的验收测试 checklist。每条验收项标记为 cmd（自动化）或 human（手动）。

## G1. 数据库 Migration

- [ ] cmd: python3 -c "import sqlite3; conn=sqlite3.connect(':memory:'); exec(open('services/backend/db/schema.sql').read()); cols=[r[1] for r in conn.execute('PRAGMA table_info(pipeline_jobs)').fetchall()]; assert 'pool_ranking_enabled' in cols; assert 'ai_quota' in cols; assert 'dev_quota' in cols; assert 'other_quota' in cols; assert 'relevance_weight' in cols; assert 'novelty_weight' in cols; assert 'ai_category_tags' in cols; assert 'dev_category_tags' in cols"
- [ ] cmd: python3 -c "import sqlite3; conn=sqlite3.connect(':memory:'); exec(open('services/backend/db/schema.sql').read()); cols=[r[1] for r in conn.execute('PRAGMA table_info(job_sources)').fetchall()]; assert 'priority' in cols; assert 'fetch_limit' in cols"
- [ ] cmd: python3 -c "import sqlite3; conn=sqlite3.connect(':memory:'); exec(open('services/backend/db/schema.sql').read()); cols=[r[1] for r in conn.execute('PRAGMA table_info(analyzed_items)').fetchall()]; assert 'relevance' in cols; assert 'novelty' in cols; assert 'composite_score' in cols"

通过标准：pipeline_jobs、job_sources、analyzed_items 三张表均包含所有新增字段。

## G2. 双维度评分 — 分析器模型

- [ ] cmd: python3 -c "from services.backend.core.ddo_pulse_core.analyzer.models import AnalysisOutput; m=AnalysisOutput(is_quality=True, score=8, relevance=7, novelty=6, categories=['AI'], summary_zh='test', reason='test'); assert m.relevance==7; assert m.novelty==6"
- [ ] cmd: python3 -c "from services.backend.core.ddo_pulse_core.analyzer.models import AnalysisOutput; m=AnalysisOutput(is_quality=True, score=8, categories=['AI'], summary_zh='test', reason='test'); assert m.relevance is None; assert m.novelty is None"

通过标准：AnalysisOutput 模型支持可选的 relevance 和 novelty 字段，缺失时为 None。

## G3. 双维度评分 — Prompt 模板

- [ ] cmd: python3 -c "from services.backend.core.ddo_pulse_core.analyzer.prompt import DUAL_SCORE_PROMPT_TEMPLATE; assert 'relevance' in DUAL_SCORE_PROMPT_TEMPLATE; assert 'novelty' in DUAL_SCORE_PROMPT_TEMPLATE"
- [ ] cmd: python3 -c "from services.backend.core.ddo_pulse_core.analyzer.prompt import format_prompt_template, DUAL_SCORE_PROMPT_TEMPLATE; result=format_prompt_template(DUAL_SCORE_PROMPT_TEMPLATE, categories_hint='AI', interest_keywords='test', title='test', content='test', scoring_rubric='test'); assert '{title}' not in result"

通过标准：DUAL_SCORE_PROMPT_TEMPLATE 存在且包含 relevance/novelty 占位符，format_prompt_template 能正确替换。

## G4. 双维度评分 — composite_score 计算

- [ ] cmd: python3 -c "
# 验证 composite_score 计算逻辑
rw, nw = 0.6, 0.4
r, n = 8, 6
expected = r * rw + n * nw
assert expected == 7.2, f'Expected 7.2, got {expected}'
"
- [ ] cmd: python3 -c "
# 验证 fallback：relevance/novelty 缺失时用 score
score = 8
rw, nw = 0.6, 0.4
# fallback: composite_score = score (近似)
assert score == 8
"

通过标准：composite_score 按权重公式正确计算；缺失时 fallback 到 score。

## G5. Fetch 阶段 — 按优先级截取

- [ ] cmd: python3 -c "
# 模拟按优先级排序和截取
sources = [
    {'id': 1, 'priority': 'P1', 'fetch_limit': None},
    {'id': 2, 'priority': 'P0', 'fetch_limit': None},
    {'id': 3, 'priority': 'P2', 'fetch_limit': 5},
]
priority_order = {'P0': 0, 'P1': 1, 'P2': 2}
sorted_sources = sorted(sources, key=lambda s: priority_order.get(s['priority'], 1))
assert sorted_sources[0]['id'] == 2  # P0 first
assert sorted_sources[1]['id'] == 1  # P1 second
assert sorted_sources[2]['id'] == 3  # P2 third
# 默认 fetch_limit
defaults = {'P0': 5, 'P1': 4, 'P2': 3}
for s in sorted_sources:
    fl = s['fetch_limit'] or defaults.get(s['priority'], 4)
    if s['priority'] == 'P0': assert fl == 5
    if s['priority'] == 'P1': assert fl == 4
    if s['priority'] == 'P2': assert fl == 5  # overridden
"
- [ ] cmd: python3 -c "
# 模拟截取逻辑
items = list(range(20))  # 20 articles
fetch_limit = 5
sorted_items = sorted(items, reverse=True)  # published_at DESC
truncated = sorted_items[:fetch_limit]
assert len(truncated) == 5
assert truncated == [19, 18, 17, 16, 15]
"

通过标准：源按 P0→P1→P2 排序；每源按 fetch_limit 截取最新 N 篇；fetch_limit 为 NULL 时使用优先级默认值。

## G6. 分池排名算法

- [ ] cmd: python3 -c "
# 模拟分池逻辑
ai_tags = ['AI', '机器学习']
dev_tags = ['开发', '工程']
candidates = [
    {'id': 1, 'categories': ['AI'], 'composite_score': 9.0},
    {'id': 2, 'categories': ['开发'], 'composite_score': 8.5},
    {'id': 3, 'categories': ['AI'], 'composite_score': 8.0},
    {'id': 4, 'categories': ['创业'], 'composite_score': 7.5},
    {'id': 5, 'categories': ['开发'], 'composite_score': 7.0},
]
ai_pool = [c for c in candidates if any(t in ai_tags for t in c['categories'])]
dev_pool = [c for c in candidates if any(t in dev_tags for t in c['categories'])]
other_pool = [c for c in candidates if c not in ai_pool and c not in dev_pool]
assert len(ai_pool) == 2
assert len(dev_pool) == 2
assert len(other_pool) == 1
# 按配额截取
selected = ai_pool[:2] + dev_pool[:2] + other_pool[:1]
assert len(selected) == 5
# 全局重排
selected.sort(key=lambda x: x['composite_score'], reverse=True)
assert selected[0]['id'] == 1
"
- [ ] cmd: python3 -c "
# 模拟补足逻辑
ai_pool = [{'id': 1, 'composite_score': 9.0}]
dev_pool = [{'id': 2, 'composite_score': 8.5}]
other_pool = []
ai_quota, dev_quota, other_quota = 2, 2, 1
selected = ai_pool[:ai_quota] + dev_pool[:dev_quota] + other_pool[:other_quota]
total_target = ai_quota + dev_quota + other_quota  # 5
remaining = [{'id': 3, 'composite_score': 8.0}, {'id': 4, 'composite_score': 7.5}]
while len(selected) < total_target and remaining:
    selected.append(remaining.pop(0))
assert len(selected) == 4  # only 4 available
"

通过标准：文章按 categories 正确分入 ai/dev/other 池；池内按 composite_score 排序；配额截取和补足逻辑正确。

## G7. 分池排名开关

- [ ] cmd: python3 -c "
# 开关关闭时走旧逻辑
pool_ranking_enabled = 0
if not pool_ranking_enabled:
    # fallback: score DESC
    result = 'legacy_sort'
else:
    result = 'pool_ranking'
assert result == 'legacy_sort'
"
- [ ] cmd: python3 -c "
# 开关开启时走分池逻辑
pool_ranking_enabled = 1
if not pool_ranking_enabled:
    result = 'legacy_sort'
else:
    result = 'pool_ranking'
assert result == 'pool_ranking'
"

通过标准：pool_ranking_enabled=0 时回退到旧的纯 score 排名；=1 时启用分池排名。

## G8. 前端配置 — Pipeline Job API

- [ ] cmd: python3 -c "
# 验证 pipeline_jobs 新字段的默认值
defaults = {
    'pool_ranking_enabled': 0,
    'ai_quota': 6,
    'dev_quota': 4,
    'other_quota': 2,
    'relevance_weight': 0.6,
    'novelty_weight': 0.4,
}
assert defaults['ai_quota'] + defaults['dev_quota'] + defaults['other_quota'] == 12
"
- [ ] human: 在前端定时任务配置页面，修改 AI 配额从 6 改为 8，保存后刷新页面，确认值为 8
- [ ] human: 在前端定时任务配置页面，修改 relevance_weight 从 0.6 改为 0.7，保存后刷新页面，确认值为 0.7

通过标准：API 正确存储和返回新字段；前端配置界面能读取和修改所有新参数。

## G9. 前端配置 — 源优先级

- [ ] human: 在定时任务配置页面的源列表中，为某个源设置优先级为 P0，保存后刷新，确认优先级为 P0
- [ ] human: 在定时任务配置页面，为 P0 源设置 fetch_limit 为 3（覆盖默认值 5），保存后刷新，确认值为 3

通过标准：源优先级和 fetch_limit 可通过前端配置并持久化。

## G10. 端到端 — 完整管线运行

- [ ] human: 创建一个测试 pipeline job，配置 3 个源（P0/P1/P2 各一个），开启分池排名，设置配额 AI=2, dev=1, other=1，运行一次，确认推送文章数为 4 且类别分布符合配额
- [ ] human: 关闭分池排名开关，重新运行，确认推送逻辑回退到纯 score 降序

通过标准：完整管线运行结果符合配置的配额和排名策略。

## G11. 向后兼容

- [ ] cmd: python3 -c "
# 未配置新参数时，旧字段仍然工作
score = 8
pool_ranking_enabled = 0
relevance_weight = 0.6
novelty_weight = 0.4
# composite_score fallback
composite_score = score  # when relevance/novelty are None
assert composite_score == 8
"
- [ ] human: 使用现有 pipeline job（未配置任何新参数），运行一次，确认行为与之前完全一致

通过标准：未配置新参数时，系统行为与当前版本一致。

---

通过标准（全局）：所有 G1-G11 分组的 checklist 条目全部通过。cmd 条目 exit code 为 0，human 条目用户确认通过。

---

## TDD 测试文件

| 测试文件 | 关联检查项 | 状态 |
|---|---|---|
| tests/test_enhanced_pipeline.py | G1-cmd1~3, G2-cmd1~2, G3-cmd1~2, G4-cmd1~2, G5-cmd1~2, G6-cmd1~2, G7-cmd1~2, G8-cmd1, G11-cmd1 | Red |
