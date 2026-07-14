# Task 01: 创建 Agent 基础结构目录

## 关联验收点
- G1: 项目结构 Agent 化

## 任务描述
创建 Agent 项目的标准目录结构，包括 `agents/`、`tools/`、`prompts/`、`workflows/` 目录及其 `__init__.py` 文件。

## 具体步骤

1. 在 `services/backend/` 下创建以下目录：
   - `agents/`
   - `tools/`
   - `tools/fetchers/`
   - `tools/analyzers/`
   - `tools/publishers/`
   - `prompts/`
   - `workflows/`

2. 为每个目录创建 `__init__.py` 文件

3. 更新 `pyproject.toml` 中的 `packages.find` 配置，添加新目录

## 输出文件
- `services/backend/agents/__init__.py`
- `services/backend/tools/__init__.py`
- `services/backend/tools/fetchers/__init__.py`
- `services/backend/tools/analyzers/__init__.py`
- `services/backend/tools/publishers/__init__.py`
- `services/backend/prompts/__init__.py`
- `services/backend/workflows/__init__.py`

## 验证命令
```bash
ls -la services/backend/agents/ services/backend/tools/ services/backend/prompts/ services/backend/workflows/
```
