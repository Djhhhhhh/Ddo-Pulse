# Service Rules (web)

> 由 AI 在开发过程中自动维护的规则文件。

## 架构规则

- Web 端仅通过 `/api` 访问 `services/backend/api`，不直连 SQLite。

## 代码规范

- 页面放在 `frontend/src/views/`；API 封装放在 `frontend/src/api/`。

## UI / 样式（强制）

- **后续生成或修改 Web 页面时，必须严格遵循** [DESIGN.md](../../DESIGN.md)（Ollama 风格设计系统：灰度色板、圆角体系、字体层级、按钮/卡片/表单等组件规范）。
- 不得自行引入与 DESIGN.md 冲突的配色（除文档允许的键盘焦点环）、渐变、阴影或字体体系；新增组件前先对照 DESIGN.md 对应章节。
- 若需求与 DESIGN.md 冲突，以 DESIGN.md 为准，并在 PR/提交说明中注明例外理由（原则上不接受例外）。

## 常见陷阱

- Vite 开发时需配置 proxy 指向 `127.0.0.1:8765`。

## 示例参考

- 样式与组件：[DESIGN.md](../../DESIGN.md)
- 功能与路由：见仓库根目录 `docs/mvp.md` §3.3、§6.2。
