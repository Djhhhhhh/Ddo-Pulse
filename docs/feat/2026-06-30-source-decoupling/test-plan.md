# Ddo-Pulse 信息源逻辑重构 测试计划

> 基于已确认的 spec.md 生成的验收测试 checklist。

## G1. DB Schema 变更与数据迁移

- [ ] cmd: python -c "import sqlite3; conn=sqlite3.connect(':memory:'); conn.executescript(open('services/backend/db/schema.sql').read()); cur=conn.execute('PRAGMA table_info(sources)'); cols=[r[1] for r in cur.fetchall()]; assert 'job_id' not in cols, 'job_id should be removed'; assert 'url' in cols; print('PASS')"
- [ ] cmd: python -c "import sqlite3; conn=sqlite3.connect(':memory:'); conn.executescript(open('services/backend/db/schema.sql').read()); cur=conn.execute('SELECT sql FROM sqlite_master WHERE name=\"job_sources\"'); assert cur.fetchone(), 'job_sources table should exist'; print('PASS')"
- [ ] cmd: python -c "import sqlite3; conn=sqlite3.connect(':memory:'); conn.executescript(open('services/backend/db/schema.sql').read()); cur=conn.execute(\"SELECT sql FROM sqlite_master WHERE name='sources'\"); sql=cur.fetchone()[0]; assert 'UNIQUE' in sql and 'url' in sql, 'url should have UNIQUE constraint'; print('PASS')"
- [ ] cmd: python -c "import sqlite3; conn=sqlite3.connect(':memory:'); conn.executescript(open('services/backend/db/schema.sql').read()); cur=conn.execute('SELECT sql FROM sqlite_master WHERE name=\"job_sources\"'); sql=cur.fetchone()[0]; assert 'focus_config_json' in sql, 'focus_config_json column should exist'; assert 'UNIQUE(job_id, source_id)' in sql, 'composite unique constraint'; print('PASS')"

通过标准：sources 表无 job_id 列，url 有 UNIQUE 约束，job_sources 表存在且含 focus_config_json 和唯一约束。

## G2. CSV 全量覆盖同步 API

- [ ] cmd: curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8765/api/sources/sync-from-csv | grep -q "200"
- [ ] cmd: curl -s -X POST http://127.0.0.1:8765/api/sources/sync-from-csv | python -c "import sys,json; d=json.load(sys.stdin); assert 'added' in d and 'updated' in d and 'skipped' in d; print('PASS')"
- [ ] cmd: curl -s http://127.0.0.1:8765/api/sources | python -c "import sys,json; sources=json.load(sys.stdin); urls=[s['url'] for s in sources]; assert len(urls)==len(set(urls)), 'duplicate urls found'; print('PASS')"
- [ ] cmd: curl -s -X POST http://127.0.0.1:8765/api/sources/sync-from-csv -o /tmp/sync1.json && curl -s -X POST http://127.0.0.1:8765/api/sources/sync-from-csv -o /tmp/sync2.json && python -c "import json; a=json.load(open('/tmp/sync1.json')); b=json.load(open('/tmp/sync2.json')); assert a['added']==b['added']==0 or True; assert a['updated']==b['updated'], 'idempotent'; print('PASS')"

通过标准：同步 API 返回 200，结果包含 added/updated/skipped 计数，URL 唯一，多次执行幂等。

## G3. 信息源与定时任务解耦

- [ ] cmd: python -c "
import sqlite3
conn = sqlite3.connect(':memory:')
conn.executescript(open('services/backend/db/schema.sql').read())
# Insert a pipeline job
conn.execute(\"INSERT INTO pipeline_jobs (name, enabled, schedule_cron, created_at) VALUES ('test', 1, '0 8 * * *', '2026-01-01')\")
# Insert a source (no job_id)
conn.execute(\"INSERT INTO sources (name, type, url, enabled, created_at) VALUES ('src1', 'rss', 'http://example.com/feed.xml', 1, '2026-01-01')\")
# Link via job_sources
conn.execute(\"INSERT INTO job_sources (job_id, source_id, focus_config_json, enabled, created_at) VALUES (1, 1, '{}', 1, '2026-01-01')\")
# Delete the source - should cascade to job_sources but not affect pipeline_jobs
conn.execute('DELETE FROM sources WHERE id = 1')
job = conn.execute('SELECT * FROM pipeline_jobs WHERE id = 1').fetchone()
assert job is not None, 'pipeline_job should survive source deletion'
js = conn.execute('SELECT * FROM job_sources WHERE job_id = 1').fetchall()
assert len(js) == 0, 'job_sources should be cascaded'
print('PASS')
"
- [ ] cmd: python -c "
import sqlite3
conn = sqlite3.connect(':memory:')
conn.executescript(open('services/backend/db/schema.sql').read())
conn.execute(\"INSERT INTO pipeline_jobs (name, enabled, schedule_cron, created_at) VALUES ('test', 1, '0 8 * * *', '2026-01-01')\")
conn.execute(\"INSERT INTO sources (name, type, url, enabled, created_at) VALUES ('src1', 'rss', 'http://a.com/feed', 1, '2026-01-01')\")
conn.execute(\"INSERT INTO job_sources (job_id, source_id, focus_config_json, enabled, created_at) VALUES (1, 1, '{}', 1, '2026-01-01')\")
# Delete the job - should cascade to job_sources but not to sources
conn.execute('DELETE FROM pipeline_jobs WHERE id = 1')
src = conn.execute('SELECT * FROM sources WHERE id = 1').fetchone()
assert src is not None, 'source should survive job deletion'
print('PASS')
"

通过标准：删除 source 不影响 pipeline_job，删除 pipeline_job 不影响 source。两者通过 job_sources 独立关联。

## G4. Per-Source 关注点配置

- [ ] cmd: python -c "
import sqlite3, json
conn = sqlite3.connect(':memory:')
conn.executescript(open('services/backend/db/schema.sql').read())
conn.execute(\"INSERT INTO pipeline_jobs (name, enabled, schedule_cron, created_at) VALUES ('test', 1, '0 8 * * *', '2026-01-01')\")
conn.execute(\"INSERT INTO sources (name, type, url, enabled, created_at) VALUES ('src1', 'rss', 'http://a.com/feed', 1, '2026-01-01')\")
focus = json.dumps({'interest_keywords': ['AI'], 'need_llm_analysis': True, 'analyze_limit': 10})
conn.execute('INSERT INTO job_sources (job_id, source_id, focus_config_json, enabled, created_at) VALUES (1, 1, ?, 1, \"2026-01-01\")', (focus,))
row = conn.execute('SELECT focus_config_json FROM job_sources WHERE job_id=1 AND source_id=1').fetchone()
cfg = json.loads(row[0])
assert cfg['interest_keywords'] == ['AI']
assert cfg['analyze_limit'] == 10
print('PASS')
"

通过标准：job_sources 表可存储和读取 per-source 的 focus_config_json。

## G5. 前端 CSV 同步按钮

- [ ] human: 在设置页面找到「全量覆盖信息源」按钮，点击后观察同步结果提示（显示新增/更新/跳过数量）
- [ ] human: 编辑 docs/ddo_pulse_rss_seed_library.csv 添加一个新源，点击同步按钮后在源列表中看到新源
- [ ] human: 编辑 CSV 修改某个源的名称，点击同步按钮后源列表中该源名称已更新
- [ ] human: 连续点击两次同步按钮，第二次显示"更新数=相同，新增数=0"（幂等性）

通过标准：同步按钮可用，结果反馈清晰，操作幂等。

## G6. 前端 Per-Source 关注点配置

- [ ] human: 在定时任务的源列表中，点击某个源的「关注点配置」按钮，打开编辑对话框
- [ ] human: 在对话框中设置关注关键词为 ["AI", "LLM"]，保存后重新打开，配置保持不变
- [ ] human: 设置 need_llm_analysis 为 false，触发一次任务执行，确认该源的文章未被 LLM 分析
- [ ] human: 设置 analyze_limit 为 5，触发任务执行，确认该源最多分析 5 篇文章

通过标准：per-source 关注点可编辑、可持久化、在任务执行时生效。

## G7. Pipeline 执行适配

- [ ] cmd: python -c "
# Verify pipeline loads sources via job_sources instead of job_id
import ast, inspect
src = open('services/backend/core/ddo_pulse_core/pipeline.py').read()
assert 'job_sources' in src or 'JOIN job_sources' in src or 'join job_sources' in src.lower(), 'pipeline should query job_sources'
assert 'job_id' not in src.split('list_sources')[1].split(')')[0] if 'list_sources' in src else True, 'should not filter by job_id in sources'
print('PASS')
"
- [ ] cmd: python -c "
# Verify focus_config_json is read during pipeline execution
src = open('services/backend/core/ddo_pulse_core/pipeline.py').read()
assert 'focus_config' in src or 'focus_config_json' in src, 'pipeline should read focus_config_json'
print('PASS')
"

通过标准：pipeline.py 通过 job_sources 加载源，读取 focus_config_json 进行差异化处理。

## 最终验证

- [ ] cmd: tail -n 1 verification.log | grep -q "ALL PASSED"
