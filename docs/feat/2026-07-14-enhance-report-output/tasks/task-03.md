# Task 03: 提取提示词到 prompts/

## 关联验收点
- G1: 项目结构 Agent 化

## 任务描述
将 LLM 提示词模板从 analyzer 中提取到独立的 `prompts/` 目录。

## 具体步骤

1. 创建 `prompts/curator.py`：
   - 移入 `DEFAULT_PROMPT_TEMPLATE`
   - 移入 `DEFAULT_SCORING_RUBRIC`
   - 移入 `PAPER_SYSTEM_PROMPT`
   - 移入 `PAPER_PROMPT_TEMPLATE`
   - 移入 `PAPER_SCORING_RUBRIC`

2. 创建 `prompts/reporter.py`：
   - 预留深度解读 prompt（后续 task-07 实现）

3. 更新 `tools/analyzers/llm_analyzer.py` 中的导入

## 输出文件
- `services/backend/prompts/curator.py`
- `services/backend/prompts/reporter.py`

## 验证命令
```bash
python -c "from ddo_pulse_prompts.curator import DEFAULT_PROMPT_TEMPLATE; print('OK')"
```
