# Task 02: 优化深度解读提示词

## 目标

修改 `services/backend/prompts/reporter.py` 中的 `DEEP_ANALYSIS_PROMPT`，降低 AI 味。

## 关联验收点

- G3 cmd1: prompt 已更新，不再包含旧角色设定

## 实现要求

1. 去掉「资深技术内容分析师」角色设定
2. 改为更口语化、自然的角色描述
3. `core_content`：禁止使用「本文」「该文」「首先」「其次」「最后」等 AI 套话
4. `key_points`：直接说要点，不加「关键观点」「技术要点」等前缀
5. `insights`：用第一人称或直接陈述，不用「梳理」「提炼」等动词
6. 保持 JSON 输出格式不变（core_content / key_points / insights）

## 文件清单

- 修改：`services/backend/prompts/reporter.py`
