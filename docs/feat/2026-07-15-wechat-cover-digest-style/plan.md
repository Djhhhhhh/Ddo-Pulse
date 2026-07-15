# Ddo-Pulse Plan

> 基于已确认的 spec.md 做技术决策。

---

## 1. 决策原则

| # | 原则 | 落地体现 |
|---|------|----------|
| P-1 | 最小侵入 | 只改必要的文件，不重构现有架构 |
| P-2 | 纯 Python | 封面拼合用 Pillow，不引入外部服务 |
| P-3 | Prompt 优先 | 文风优化通过修改 prompt 实现，不改数据模型 |

---

## 2. 整体架构

```
ReporterAgent.run()
    │
    ├─ _deep_analyze_batch()
    │      └─ 调用 LLM（优化后的 DEEP_ANALYSIS_PROMPT）
    │
    ├─ _generate_md()
    │      └─ generate_digest_md()（优化排版模板）
    │
    ├─ _generate_html()
    │      └─ generate_digest_html()（同步排版优化）
    │
    ├─ _generate_cover()          ← 新增
    │      └─ merge_cover_images()（Pillow 拼合）
    │
    └─ _generate_screenshots()
```

关键事实：
- 封面拼合作为独立工具函数，ReporterAgent 在生成报告后调用
- 文风优化通过修改 `prompts/reporter.py` 中的 `DEEP_ANALYSIS_PROMPT` 实现
- 排版优化通过修改 `tools/publishers/markdown.py` 中的模板实现

---

## 3. 目录与命名（最终定版）

```text
services/backend/
├── tools/
│   └── publishers/
│       ├── cover_merger.py        # 新增：封面图拼合工具
│       ├── markdown.py            # 修改：优化排版模板
│       └── html_report.py         # 不变（HTML 排版已较好）
├── agents/
│   └── reporter.py                # 修改：集成 _generate_cover()
└── prompts/
    └── reporter.py                # 修改：优化 DEEP_ANALYSIS_PROMPT
```

---

## 4. 核心 Schema

### 4.1 cover_merger.py 接口

```python
def merge_cover_images(
    large_cover: Path,    # 900×383 大封面
    small_cover: Path,    # 383×383 小封面
    output_path: Path,    # 输出 1283×383
) -> Path:
    """将大封面和小封面拼合为微信公众号兼容的封面图"""
```

字段语义约束：
- `large_cover`：必须是 900×383 或可调整为此尺寸的图片
- `small_cover`：必须是 383×383 或可调整为此尺寸的图片
- `output_path`：输出 PNG 格式，1283×383

校验：
- 输入图片尺寸不匹配时，自动 resize（不裁切）
- 输入文件不存在时，抛出 FileNotFoundError

### 4.2 DEEP_ANALYSIS_PROMPT 调整策略

保持 JSON 输出格式不变（core_content / key_points / insights），修改提示词引导更自然的文风：
- 去掉「资深技术内容分析师」角色设定 → 改为更口语化的角色
- 去掉「要求」中的模板化指令 → 改为更自由的写作引导
- 增加「避免 AI 味」的具体约束

---

## 5. 关键算法 / 流程

### 5.1 封面图拼合

1. 用 Pillow 打开 large_cover 和 small_cover
2. 验证/调整尺寸：large → 900×383，small → 383×383
3. 创建 1283×383 的空白画布（白色背景）
4. 将 large 粘贴到 (0, 0)
5. 将 small 粘贴到 (900, 0)
6. 保存为 PNG

### 5.2 文风优化

修改 DEEP_ANALYSIS_PROMPT 的策略：
- `core_content`：要求用 200-300 字概括，但禁止使用「本文」「该文」「首先」「其次」「最后」等 AI 套话
- `key_points`：要求直接说要点，不加「关键观点」「技术要点」等前缀
- `insights`：要求用第一人称或直接陈述，不用「梳理」「提炼」等动词

---

## 6. 错误处理与回退

| 触发条件 | 行为 |
|---|---|
| Pillow 未安装 | 跳过封面拼合，记录 warning |
| 输入图片尺寸不匹配 | 自动 resize 到目标尺寸 |
| 输入文件不存在 | 抛出 FileNotFoundError，由调用方处理 |
| LLM 输出格式异常 | 保持现有 fallback（返回空 dict） |

---

## 7. 风险与权衡

| # | 风险 | 描述 | 处置 |
|---|------|------|------|
| R-1 | Pillow 依赖 | pyproject.toml 中未声明 Pillow 依赖 | 添加到 dependencies 或 optional-dependencies |
| R-2 | 文风过度调整 | prompt 修改可能导致输出质量下降 | 先小范围测试，保留回退能力 |
| R-3 | 现有测试回归 | 修改 markdown.py 可能影响现有测试 | 运行测试验证 |

---

## 8. 实施次序（高层路线，供 Tasking 拆分参考）

1. **Task 1**：新增 `cover_merger.py`，实现 `merge_cover_images()` 函数
2. **Task 2**：修改 `prompts/reporter.py`，优化 `DEEP_ANALYSIS_PROMPT`
3. **Task 3**：修改 `tools/publishers/markdown.py`，优化排版模板
4. **Task 4**：修改 `agents/reporter.py`，集成 `_generate_cover()` 调用
5. **Task 5**：运行测试，验证无回归

---

## 9. 与 spec 的开放问题对应表

| spec Open Question | plan 中的落地 |
|---|---|
| Q-1 封面拼合是独立 CLI 还是内部调用？ | 作为工具函数 `merge_cover_images()` 在 ReporterAgent 内部调用，不暴露 CLI（第 4.1 节） |
| Q-2 是否需要支持自定义模板？ | 不支持，本期仅提供基础拼合能力（第 2 节 Out of Scope） |
| Q-3 文风优化修改 system prompt 还是 user prompt？ | 修改 user prompt（DEEP_ANALYSIS_PROMPT），因为它是发给 LLM 的具体指令（第 4.2 节） |

---

## 10. 用户确认

请确认以下任一选项：

- ✅ **同意**：本 plan 符合预期，可进入 **Test-Planning** 阶段生成 `test-plan.md`。
- ❌ **修改**：请在下方/对话中列出需要调整的章节与意见，AI 将基于反馈重新生成本文档。
