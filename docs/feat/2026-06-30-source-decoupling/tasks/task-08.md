# Task-08: 前端 Per-Source 关注点配置 UI

## 目标
在前端定时任务的源列表中，为每个源添加关注点配置的编辑入口。

## 关联验收点
- G6: 前端 Per-Source 关注点配置

## 变更文件
- `services/web/frontend/src/api/client.ts`（新增 API 方法）
- `services/web/frontend/src/views/SettingsView.vue`（新增关注点配置 UI）

## 具体变更

### client.ts
- 新增 `listJobSources(jobId)` 方法
- 新增 `updateJobSourceFocus(jobId, sourceId, focusConfig)` 方法
- 新增 `addJobSource(jobId, sourceId, focusConfig)` 方法
- 新增 `removeJobSource(jobId, sourceId)` 方法

### SettingsView.vue
1. 修改定时任务的源列表，从 `GET /api/sources?job_id=X` 改为 `GET /api/pipeline-jobs/{job_id}/sources`
2. 每行源添加「关注点配置」按钮
3. 点击打开对话框，包含以下字段：
   - 关注关键词（tag 输入，数组）
   - 是否需要 LLM 分析（开关）
   - 是否需要网页正文提取（开关）
   - 分析条数限制（数字输入）
   - 自定义 prompt 提示（文本框）
4. 保存时调用 `updateJobSourceFocus()`
5. 添加源到 job 时，可同时设置初始关注点配置

## 验收
- 运行 test-plan G6 中所有 human 检查项
