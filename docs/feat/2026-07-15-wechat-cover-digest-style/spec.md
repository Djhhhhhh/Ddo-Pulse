# Ddo-Pulse Specification

> AI 基于用户原始需求与 context-summary.md 对需求的规约化理解。
> 仅描述 What / Why 与验收标准；技术方案见 plan.md。

---

## 1. 项目概述

### 1.1 项目名称
Ddo-Pulse — 微信公众号封面图拼合 & digest.md 文风优化

### 1.2 一句话定义
为 Ddo-Pulse 的报告发布流程新增微信公众号封面图拼合能力，并优化 digest.md 的排版与文风。

### 1.3 设计意图
- 微信公众号只允许上传一张封面图，但有 2.35:1（首图）和 1:1（小图）两种展示尺寸。将两张图拼合为一张 1283×383 的图，可同时适配两种裁切。
- 当前 digest.md 的排版较乱、AI 味过重，需要更贴近人类写作习惯的文风和更清晰的格式。

---

## 2. 功能需求（Functional Requirements）

### 2.1 封面图拼合

- **FR-COVER-1**：提供一个独立工具/函数，接收两张图片（大封面 900×383、小封面 383×383），拼合为一张 1283×383 的图片。
- **FR-COVER-2**：大封面放在左侧（0,0）至（900,383），小封面放在右侧（900,0）至（1283,383）。
- **FR-COVER-3**：输出图片格式为 PNG，质量不劣于原图。
- **FR-COVER-4**：拼合工具应能被报告生成流程调用（ReporterAgent 或 pipeline 中集成）。

### 2.2 digest.md 文风优化

- **FR-STYLE-1**：重新设计 digest.md 的排版模板，使结构更清晰、层次更分明。
- **FR-STYLE-2**：降低 AI 生成内容的「AI 味」——减少套话、模板化表述、过度修饰，使文风更自然。
- **FR-STYLE-3**：深度解读部分（core_content / key_points / insights）的输出风格需要调整，更像人类技术博主的口吻。
- **FR-STYLE-4**：修改 DEEP_ANALYSIS_PROMPT 中的提示词，引导 LLM 输出更自然的文风。

---

## 3. 产物与目录结构（What gets created）

```text
services/backend/
├── tools/
│   └── publishers/
│       ├── cover_merger.py        # 新增：封面图拼合工具
│       ├── markdown.py            # 修改：优化排版模板
│       └── html_report.py         # 可能修改：同步排版优化
├── agents/
│   └── reporter.py                # 修改：集成封面图拼合
└── prompts/
    └── reporter.py                # 修改：优化深度解读提示词
```

---

## 4. 关键流程

```text
报告生成流程（修改后）：
  ReporterAgent.run()
    ├─ _deep_analyze_batch()       ← 使用优化后的 prompt
    ├─ _generate_md()              ← 使用优化后的排版模板
    ├─ _generate_html()            ← 同步排版优化
    ├─ _generate_cover()           ← 新增：拼合封面图
    │   ├─ 读取/生成大封面 (900×383)
    │   ├─ 读取/生成小封面 (383×383)
    │   └─ 输出拼合图 (1283×383)
    └─ _generate_screenshots()
```

---

## 5. 约束与原则

- **C-1**：封面图拼合工具必须是纯 Python 实现（Pillow），不引入外部服务依赖。
- **C-2**：文风优化应通过修改 prompt 实现，不改变数据模型或 API 接口。
- **C-3**：所有改动限定在 `services/backend` 目录内。
- **C-4**：不破坏现有的 HTML 报告和截图功能。

---

## 6. 验收标准（Acceptance Criteria）

- **AC-1**：封面图拼合工具能正确将 900×383 和 383×383 的图片拼合为 1283×383 的 PNG。
- **AC-2**：拼合后的图片在微信公众号上传时，首图和小图裁切均显示完整内容。
- **AC-3**：digest.md 的排版格式更清晰，层次分明，可读性提升。
- **AC-4**：深度解读部分的文风更自然，减少明显的 AI 模板化表述。
- **AC-5**：现有测试通过，不引入回归。

---

## 7. 范围说明（In / Out of Scope）

### In Scope
- 封面图拼合工具的实现
- digest.md 排版模板优化
- DEEP_ANALYSIS_PROMPT 文风调整
- ReporterAgent 集成封面图拼合

### Out of Scope
- 自动生成封面图内容（仅提供拼合能力）
- 微信公众号 API 对接
- 前端 UI 变更
- 飞书推送格式变更

---

## 8. 开放问题（Open Questions，待 Plan 阶段决策）

- **Q-1**：封面图拼合是作为独立 CLI 命令暴露，还是仅在 ReporterAgent 内部调用？
- **Q-2**：是否需要支持自定义封面图模板（如添加文字、logo 水印）？
- **Q-3**：文风优化的具体 prompt 策略——是修改 system prompt 还是 user prompt？

---

## 9. 用户确认

请确认以下任一选项：

- ✅ **同意**：本 spec 符合预期，可进入 **Planning** 阶段生成 `plan.md`。
- ❌ **修改**：请在下方/对话中列出需要调整的条款编号与意见，AI 将基于反馈重新生成本文档。
