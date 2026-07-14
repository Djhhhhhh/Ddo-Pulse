# Task 07: 深度解读 Prompt

## 关联验收点
- G2: 深度解读功能

## 任务描述
设计深度解读的 LLM 提示词模板。

## 具体步骤

1. 创建 `prompts/reporter.py` 中的深度解读 prompt：
   - `DEEP_ANALYSIS_PROMPT` - 深度解读主 prompt
   - 要求输出：核心内容、关键观点、思路梳理

2. 定义输出 JSON schema

## 输出文件
- 修改 `services/backend/prompts/reporter.py`

## Prompt 设计
```python
DEEP_ANALYSIS_PROMPT = """你是一位资深技术内容分析师。请对以下文章进行深度解读。

文章标题：{title}
文章内容：{content}

请输出 JSON 格式（字段名必须一致）：
{{
  "core_content": "文章核心内容的 200-300 字总结",
  "key_points": [
    "关键观点1",
    "关键观点2",
    "关键观点3"
  ],
  "insights": "文章的思路梳理和启发性内容"
}}

要求：
- core_content：概括文章的主要内容和结论
- key_points：提取 3-5 个关键观点或技术要点
- insights：梳理文章的逻辑思路，提炼启发性内容"""
```

## 验证命令
```bash
python -c "
from ddo_pulse_prompts.reporter import DEEP_ANALYSIS_PROMPT
assert 'core_content' in DEEP_ANALYSIS_PROMPT
assert 'key_points' in DEEP_ANALYSIS_PROMPT
assert 'insights' in DEEP_ANALYSIS_PROMPT
print('OK')
"
```
