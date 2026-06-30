# Ddo-Pulse 测试计划

> 基于已确认的 spec.md 生成的验收测试 checklist。每条验收项标记为 cmd（自动化）或 human（手动）。

## G1. 后端 API — base_url 字段贯通

- [ ] cmd: python -c "import sqlite3; conn = sqlite3.connect(':memory:'); conn.execute('CREATE TABLE llm_profiles (id INTEGER, name TEXT, base_url TEXT DEFAULT \"https://openrouter.ai/api/v1\", model TEXT, api_key TEXT)'); conn.execute('INSERT INTO llm_profiles (name, model) VALUES (\"test\", \"gpt-4o\")'); r = conn.execute('SELECT base_url FROM llm_profiles WHERE id=1').fetchone(); assert r[0] == 'https://openrouter.ai/api/v1', f'Expected default base_url, got {r[0]}'; print('OK')"
- [ ] cmd: python -c "from services.backend.api.ddo_pulse_api.schemas import ProfileOut; p = ProfileOut(id=1, name='test', base_url='https://openrouter.ai/api/v1', model='gpt-4o', is_default=True, score_threshold=7, api_key_set=True); assert hasattr(p, 'base_url'), 'ProfileOut missing base_url'; print('OK')"
- [ ] cmd: python -c "from services.backend.api.ddo_pulse_api.schemas import ProfileUpdate; p = ProfileUpdate(base_url='http://localhost:11434/v1', model='llama3'); assert p.base_url == 'http://localhost:11434/v1'; print('OK')"

通过标准：ProfileOut 和 ProfileUpdate 均包含 base_url 字段，数据库默认值正确。

## G2. 后端 DB 层 — update_llm_profile 支持 base_url

- [ ] cmd: python -c "
import sqlite3, sys, os
sys.path.insert(0, os.path.join(os.getcwd(), 'services/backend/db'))
from ddo_pulse_db.repository import Repository
conn = sqlite3.connect(':memory:')
conn.row_factory = sqlite3.Row
conn.executescript(open('services/backend/db/schema.sql').read())
repo = Repository(conn)
repo.ensure_default_profile_from_dict({'name': 'default', 'model': 'gpt-4o', 'api_key': 'sk-test', 'base_url': 'https://openrouter.ai/api/v1'})
repo.update_llm_profile(1, base_url='http://localhost:11434/v1')
row = repo.get_llm_profile(1)
assert row['base_url'] == 'http://localhost:11434/v1', f'Expected new base_url, got {row[\"base_url\"]}'
print('OK')
"

通过标准：update_llm_profile 成功更新 base_url 字段。

## G3. 前端 TypeScript 类型 — Profile 接口

- [ ] cmd: cd services/web/frontend && npx tsc --noEmit src/api/client.ts 2>&1 | grep -c "error" | xargs -I{} test {} -eq 0 && echo "OK" || echo "FAIL"

通过标准：Profile 接口包含 base_url 字段，TypeScript 编译无错误。

## G4. 前端 UI — 设置页 base_url 输入框（手动验证）

- [ ] human: 打开设置页，切换到「模型与密钥」tab，确认每个 profile 卡片显示三个输入框：base_url、model、API Key
- [ ] human: 确认 base_url 输入框的 placeholder 显示 `https://openrouter.ai/api/v1`
- [ ] human: 确认 base_url 输入框回填了当前 profile 的 base_url 值
- [ ] human: 修改 base_url 为 `http://localhost:11434/v1`，点击保存，确认提示"已保存模型配置"
- [ ] human: 刷新页面，确认 base_url 输入框显示上次保存的值 `http://localhost:11434/v1`
- [ ] human: 清空 base_url 输入框后保存，刷新页面确认 base_url 恢复为默认值 `https://openrouter.ai/api/v1`

通过标准：base_url 输入框显示、回填、保存、刷新保持、清空恢复均正常。

## G5. 端到端 — LLM 调用使用新 base_url

- [ ] human: 将 base_url 修改为一个可访问的 OpenAI 兼容服务地址（如 Ollama 的 `http://localhost:11434/v1`），修改 model 为对应模型名，触发 pipeline 运行，确认 LLM 分析正常完成
- [ ] human: 将 base_url 恢复为 `https://openrouter.ai/api/v1`，确认 OpenRouter 服务正常工作

通过标准：修改 base_url 后 pipeline 运行使用新地址，恢复后 OpenRouter 正常。

## 最终验证

- [ ] cmd: tail -n 1 verification.log | grep -q "ALL PASSED"

## TDD 测试文件

| 测试文件 | 关联检查项 | 状态 |
|---|---|---|
| tests/test_profile_base_url.py | G1 cmd1, G1 cmd2, G1 cmd3, G2 cmd1 | Red |
