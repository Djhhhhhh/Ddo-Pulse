# 反思报告 — Ddo-Pulse 信息源逻辑重构

---

## 1. 未完结项

无 TODO/FIXME/XXX 标记。

---

## 2. 遗留风险

| # | 风险 | 描述 | 建议处理 |
|---|------|------|---------|
| R-1 | G2/G5/G6 未自动化验证 | CSV 同步 API 和前端 UI 需要运行服务器才能测试 | 启动后端服务后手动验证 |
| R-2 | 历史数据迁移未在生产环境验证 | `_migrate_sources_to_global()` 在内存测试中通过，但未在真实 DB 上测试 | 首次启动时观察迁移日志 |
| R-3 | 前端 `removeSource` 行为变更 | 原来是物理删除源，现在是从 job 取消关联 | 用户需了解新语义 |

---

## 3. 经验教训

| # | 经验 | 说明 |
|---|------|------|
| L-1 | 解耦重构需全链路排查 | sources.job_id 的引用遍布 schema/repository/api/pipeline/cli/mcp/frontend，需系统性排查 |
| L-2 | SQLite CASCADE 需开启 foreign_keys | 测试中发现 `PRAGMA foreign_keys = ON` 是必须的，否则 CASCADE 不生效 |
| L-3 | 前端类型与 API 契约需同步更新 | 改后端 schema 后，前端的 TypeScript 接口和模板引用都需要同步修改 |

---

## 4. 推荐后续动作

1. **启动服务验证**：`ddo-pulse start` 后手动执行 G2/G5/G6 测试项
2. **检查迁移日志**：首次连接现有 DB 时，确认 `_migrate_sources_to_global()` 成功执行
3. **提交代码**：`git add -A && git commit -m "feat: 信息源与定时任务解耦，支持 CSV 全量覆盖和 per-source 关注点配置"`
4. **合并到 main**：验证无误后合并分支

---

## 5. 用户确认

请确认以下任一选项：

- ✅ **同意**：反思报告已完成，流水线进入 **Done** 阶段。
- ❌ **修改**：请列出需要补充的内容。
