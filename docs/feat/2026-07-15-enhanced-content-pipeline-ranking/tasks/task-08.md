# Task-08: 前端 SettingsView 集成

## 关联验收点
- G8: 前端配置 — Pipeline Job API
- G9: 前端配置 — 源优先级
- G10: 端到端 — 完整管线运行

## 目标
将新组件集成到 SettingsView.vue 的定时任务编辑页面。

## 修改文件
- `services/web/frontend/src/views/SettingsView.vue`

## 具体改动

### SettingsView.vue
1. 在定时任务编辑 modal 中新增「评分策略」配置区域：
   - 分池排名开关
   - 评分权重编辑器（ScoringWeightEditor 组件）

2. 新增「推送配额」配置区域：
   - 类别配额编辑器（CategoryQuotaEditor 组件）

3. 在现有源列表区域增强：
   - 每个源新增「优先级」列（P0/P1/P2 下拉）
   - 每个源新增「抓取上限」列（数字输入框，留空用默认值）

4. 在 job 创建/编辑的 save 逻辑中：
   - 收集所有新字段值
   - 传递给 API 的 create/update 请求

5. 在 job 加载逻辑中：
   - 从 API 读取新字段并填充到表单

## 验证
运行 G8、G9、G10 的 human 测试项。
