# Service Rules (backend)

> 由 AI 在开发过程中自动维护的规则文件。

## 架构规则

- 业务逻辑只在 `core/ddo_pulse_core`；`api` 做 HTTP 适配；`cli` 做进程与调度。
- 跨模块：`cli`/`mcp`/`api` → `core` → `db`，禁止 `core` import FastAPI。

## 代码规范

- 用户数据目录使用 `Path.home() / ".ddo_pulse"`，见 `docs/mvp.md` §12.2.1。
- LLM 统一经 OpenRouter，见 `docs/mvp.md` §10.3。

## 常见陷阱

- `browser_session` 抓取时 Chrome Profile 可能被占用，需提示用户关闭浏览器。

## 示例参考

- 见 `docs/mvp.md` §7、§10、§11。
