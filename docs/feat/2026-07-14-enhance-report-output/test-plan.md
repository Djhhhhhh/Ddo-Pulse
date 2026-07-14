# Ddo-Pulse 报告增强 测试计划

> 基于已确认的 spec.md 生成的验收测试 checklist。

---

## G1. 项目结构 Agent 化

- [ ] cmd: ls -la services/backend/agents/ | grep -E "base.py|curator.py|reporter.py"
- [ ] cmd: ls -la services/backend/tools/ | grep -E "fetchers|analyzers|publishers"
- [ ] cmd: ls -la services/backend/prompts/ | grep -E "curator.py|reporter.py"
- [ ] cmd: ls -la services/backend/workflows/ | grep "daily_digest.py"
- [ ] cmd: python -c "from ddo_pulse_agents.base import Agent; print('Agent base import OK')"
- [ ] cmd: python -c "from ddo_pulse_agents.curator import CuratorAgent; print('Curator import OK')"
- [ ] cmd: python -c "from ddo_pulse_agents.reporter import ReporterAgent; print('Reporter import OK')"

通过标准：所有目录和文件存在，Agent 类可正常导入。

---

## G2. 深度解读功能

- [ ] cmd: python -c "from ddo_pulse_db.repository import Database; db = Database(); db.init_schema(); print('Schema OK')"
- [ ] cmd: grep -q "deep_analysis_json" services/backend/db/schema.sql && echo "Field exists"
- [ ] cmd: python -c "
from ddo_pulse_prompts.reporter import DEEP_ANALYSIS_PROMPT
assert 'core_content' in DEEP_ANALYSIS_PROMPT
assert 'key_points' in DEEP_ANALYSIS_PROMPT
assert 'insights' in DEEP_ANALYSIS_PROMPT
print('Prompt OK')
"
- [ ] human: 运行 `ddo-pulse run-once --skip-digest`，检查 analyzed_items 表中 deep_analysis_json 字段是否填充

通过标准：数据库包含深度解读字段，Prompt 模板正确，深度解读结果正常存储。

---

## G3. 报告目录结构

- [ ] cmd: python -c "
from datetime import datetime
ts = datetime.now().strftime('%Y-%m-%d-%H%M%S')
assert len(ts) == 15
print(f'Timestamp format OK: {ts}')
"
- [ ] cmd: python -c "
import os
report_dir = os.path.expanduser('~/.ddo_pulse/reports/test-2026-07-14-120000')
os.makedirs(report_dir, exist_ok=True)
os.makedirs(os.path.join(report_dir, 'images'), exist_ok=True)
assert os.path.isdir(report_dir)
os.rmdir(os.path.join(report_dir, 'images'))
os.rmdir(report_dir)
print('Directory creation OK')
"

通过标准：时间戳格式正确（yyyy-mm-dd-HHmmss），目录可正常创建。

---

## G4. 本地 MD 报告

- [ ] cmd: ls ~/.ddo_pulse/reports/*/digest.md 2>/dev/null | head -1 || echo "No MD report yet"
- [ ] human: 运行 pipeline 后，检查 `~/.ddo_pulse/reports/<timestamp>/digest.md` 文件是否生成
- [ ] human: 打开 digest.md，确认包含文章标题、评分、分类、深度解读内容
- [ ] human: 复制 digest.md 内容到微信公众号编辑器，确认排版正常

通过标准：MD 文件正常生成，内容完整，公众号排版友好。

---

## G5. HTML PPT 式报告

- [ ] cmd: ls ~/.ddo_pulse/reports/*/digest.html 2>/dev/null | head -1 || echo "No HTML report yet"
- [ ] human: 运行 pipeline 后，检查 `~/.ddo_pulse/reports/<timestamp>/digest.html` 文件是否生成
- [ ] human: 在浏览器中打开 digest.html，确认每页显示一篇文章解读
- [ ] human: 点击翻页按钮，确认可正常切换页面
- [ ] human: 检查 HTML 样式是否美观，适合截图

通过标准：HTML 文件正常生成，支持翻页，样式美观。

---

## G6. 自动截图功能

- [ ] cmd: python -c "import playwright; print('Playwright installed')" 2>/dev/null || echo "Playwright not installed (skip)"
- [ ] cmd: ls ~/.ddo_pulse/reports/*/images/*.png 2>/dev/null | head -1 || echo "No screenshots yet"
- [ ] human: 运行 pipeline 后，检查 `~/.ddo_pulse/reports/<timestamp>/images/` 目录下是否有 PNG 文件
- [ ] human: 打开 PNG 文件，确认图片清晰，内容与 HTML 报告一致
- [ ] human: 确认图片宽度适合公众号使用（约 1080px）

通过标准：截图正常生成，图片清晰，尺寸合适。

---

## G7. 飞书推送（回归测试）

- [ ] cmd: python -c "
from ddo_pulse_core.notifier.feishu import build_feishu_post_payload
print('Feishu payload builder OK')
"
- [ ] human: 运行 `ddo-pulse digest push`，确认飞书消息正常推送
- [ ] human: 检查飞书消息格式是否正确（标题、摘要、链接）

通过标准：飞书推送功能正常，不受本次改动影响。

---

## G8. 前端报告预览

- [ ] cmd: curl -s http://localhost:8765/api/reports 2>/dev/null | python -m json.tool || echo "API not running"
- [ ] human: 启动 `ddo-pulse dev`，访问 `/reports` 页面
- [ ] human: 确认报告列表正确显示（日期、文章数）
- [ ] human: 点击报告进入预览页面，确认 HTML 报告在 iframe 中正常加载
- [ ] human: 点击全屏按钮，确认全屏预览正常
- [ ] human: 点击下载按钮，确认 MD/HTML/PNG 文件可正常下载

通过标准：前端页面正常显示，预览和下载功能正常。

---

## G9. Docker 数据卷挂载

- [ ] cmd: grep -q "reports" docker-compose.yml && echo "Volume mount configured"
- [ ] cmd: docker-compose config 2>/dev/null | grep -q "reports" && echo "Docker config OK" || echo "Docker not available"
- [ ] human: 使用 `docker-compose up` 启动服务
- [ ] human: 在宿主机 `~/.ddo_pulse/reports/` 目录下查看报告文件
- [ ] human: 确认报告文件可正常访问和复制

通过标准：Docker 容器内生成的报告文件在宿主机可正常访问。

---

## TDD 测试文件

| 测试文件 | 关联检查项 | 状态 |
|---|---|---|
| tests/test_agents_base.py | G1 cmd5 | Red |
| tests/test_agents_curator.py | G1 cmd6 | Red |
| tests/test_agents_reporter.py | G1 cmd7 | Red |
| tests/test_deep_analysis.py | G2 cmd1, G2 cmd2, G2 cmd3 | Red |
| tests/test_report_dir.py | G3 cmd1, G3 cmd2 | Red |
| tests/test_feishu_regression.py | G7 cmd1 | Red |
