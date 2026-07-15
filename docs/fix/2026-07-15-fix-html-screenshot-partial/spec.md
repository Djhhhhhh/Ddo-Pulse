# HTML 截图功能修复 Specification

> AI 基于用户原始需求与 context-summary.md 对需求的规约化理解。
> 仅描述 What / Why 与验收标准；技术方案见 plan.md。

---

## 1. 项目概述

### 1.1 项目名称
Ddo-Pulse HTML 截图功能修复

### 1.2 一句话定义
修复 HTML 报告截图只能捕获部分内容的 bug，确保截图完整展示所有信息。

### 1.3 设计意图
- 确保报告截图完整展示所有内容
- 提升用户阅读体验
- 保证报告信息的完整性

---

## 2. 术语表（Glossary）

| 术语 | 定义 |
|---|---|
| HTML 报告 | 由 html_report.py 生成的 PPT 风格幻灯片报告 |
| Slide | HTML 报告中的单个幻灯片页面 |
| Viewport | 浏览器可视区域的尺寸 |
| Full-page screenshot | 捕获整个页面内容（包括滚动区域）的截图方式 |

---

## 3. 功能需求（Functional Requirements）

### 3.1 截图完整性

- **FR-SCREENSHOT-1**：截图应捕获每个 Slide 的完整内容，包括超出视口高度的部分
- **FR-SCREENSHOT-2**：截图应保持原始 HTML 的布局和样式不变
- **FR-SCREENSHOT-3**：截图应包含所有文本内容，不得截断

---

## 4. 验收标准（Acceptance Criteria）

- **AC-1**：当 Slide 内容高度超过 800px 时，截图仍能完整展示所有内容
- **AC-2**：截图中不出现内容截断或缺失的情况
- **AC-3**：截图的视觉效果与 HTML 页面一致

---

## 5. 范围说明（In / Out of Scope）

### In Scope
- 修复 screenshot.py 中的截图逻辑
- 确保截图捕获完整内容

### Out of Scope
- 修改 HTML 报告的布局或样式
- 添加新的截图功能（如批量截图、自定义尺寸等）
- 性能优化

---

## 6. 开放问题（Open Questions，待 Plan 阶段决策）

- **Q-1**：使用 `full_page=True` 还是动态计算内容高度设置视口？
- **Q-2**：是否需要保留固定视口宽度的参数化？
- **Q-3**：截图完成后是否需要恢复视口设置？

---

## 7. 用户确认

请确认以下任一选项：

- ✅ **同意**：本 spec 符合预期，可进入 **Planning** 阶段生成 `plan.md`。
- ❌ **修改**：请在下方/对话中列出需要调整的条款编号与意见，AI 将基于反馈重新生成本文档。
