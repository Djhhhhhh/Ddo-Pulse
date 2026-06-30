# Task-07: 前端 CSV 同步按钮

## 目标
在前端设置页面添加「全量覆盖信息源」按钮，调用同步 API 并展示结果。

## 关联验收点
- G5: 前端 CSV 同步按钮

## 变更文件
- `services/web/frontend/src/api/client.ts`（新增 API 方法）
- `services/web/frontend/src/views/SettingsView.vue`（新增按钮和交互）

## 具体变更

### client.ts
- 新增 `syncSourcesFromCsv()` 方法：`POST /api/sources/sync-from-csv`

### SettingsView.vue
1. 在设置页面顶部或源管理区域添加「全量覆盖信息源」按钮
2. 点击后弹出确认对话框："将用 CSV 文件内容全量替换信息源列表，是否继续？"
3. 确认后调用 `syncSourcesFromCsv()`
4. 成功后显示结果 toast：`新增 X 个，更新 Y 个，跳过 Z 个`
5. 刷新源列表

## 验收
- 运行 test-plan G5 中所有 human 检查项
