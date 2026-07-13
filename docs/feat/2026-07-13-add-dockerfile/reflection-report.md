# 复盘报告 — feat-2026-07-13-add-dockerfile

> 检查项目是否存在未完结的后续流程。

---

## 未完结项

无。本次 run 新增的文件中没有 TODO/FIXME/XXX 标记。

---

## 推荐后续动作

- **[可选] 添加 .dockerignore**：当前构建会拷贝整个项目（含 `.git`、`docs/`、`tests/` 等），添加 `.dockerignore` 可减小构建上下文体积
- **[可选] 多架构构建**：如需支持 ARM64（Apple Silicon），可使用 `docker buildx build --platform linux/amd64,linux/arm64`
- **[可选] CI/CD 集成**：将 `docker build` + `docker push` 集成到 CI 流水线

---

## 经验教训

- `pip install .` 后代码在 `site-packages/`，`Path(__file__).parents[N]` 解析的路径与源码树不同，需要额外步骤将资源文件复制到正确位置
- `StaticFiles(html=True)` 不支持 SPA 路由兜底，需要自定义 middleware
- `ddo-pulse init` 对已存在的数据库跳过 schema 初始化，容器环境应使用 `--force` 确保表结构完整

---

## 用户确认

请确认以下任一选项：

- ✅ **同意**：本复盘报告符合预期，流水线标记为完成。
- ❌ **修改**：请列出需要调整的内容。
