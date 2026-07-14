# Task 02: 迁移现有逻辑到 tools/

## 关联验收点
- G1: 项目结构 Agent 化

## 任务描述
将现有的 fetchers、analyzer、notifier 逻辑迁移到 `tools/` 目录下，保持功能不变。

## 具体步骤

1. 迁移 fetchers：
   - `core/ddo_pulse_core/fetchers/` → `tools/fetchers/`
   - 更新导入路径

2. 迁移 analyzers：
   - `core/ddo_pulse_core/analyzer/` → `tools/analyzers/`
   - 更新导入路径

3. 迁移 publishers：
   - `core/ddo_pulse_core/notifier/` → `tools/publishers/`
   - 重命名 `feishu.py` 保持不变
   - 更新导入路径

4. 更新所有引用这些模块的文件：
   - `pipeline.py`
   - `cli/main.py`
   - `api/` 下的文件

## 输出文件
- `services/backend/tools/fetchers/rss.py`
- `services/backend/tools/fetchers/html_list.py`
- `services/backend/tools/fetchers/browser_session.py`
- `services/backend/tools/analyzers/llm_analyzer.py`
- `services/backend/tools/publishers/feishu.py`

## 验证命令
```bash
python -c "from ddo_pulse_tools.fetchers.rss import RssFetcher; print('OK')"
python -c "from ddo_pulse_tools.analyzers.llm_analyzer import OpenRouterAnalyzer; print('OK')"
python -c "from ddo_pulse_tools.publishers.feishu import send_feishu_webhook; print('OK')"
```
