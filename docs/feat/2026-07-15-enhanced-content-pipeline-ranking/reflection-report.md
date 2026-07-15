# Reflection Report

> 2026-07-15 | feat/2026-07-15-enhanced-content-pipeline-ranking

## 已完成

- ✅ 数据库 schema 扩展（3 张表新增 11 个字段）
- ✅ 双维度评分（relevance + novelty）prompt 模型和存储
- ✅ Fetch 阶段按优先级截取（P0→P1→P2 排序 + fetch_limit）
- ✅ 分池排名算法（分池→排序→截取→补足→全局重排）
- ✅ Pipeline 编排集成（权重传递、池配置传递）
- ✅ API/Repository 扩展（CRUD 支持所有新字段）
- ✅ 前端类型定义更新
- ✅ 前端配置 UI（评分策略、推送配额、源优先级选择器）
- ✅ TDD 测试骨架（17 个 cmd 测试）
- ✅ 17/17 cmd 测试通过

## 待手动验证（human 测试项）

1. 前端修改 AI 配额后保存并刷新，确认值持久化
2. 前端修改 relevance_weight 后保存并刷新
3. 前端设置源优先级为 P0 并保存
4. 前端设置 fetch_limit 覆盖默认值
5. 端到端：创建测试 job，开启分池排名，运行并确认配额均衡
6. 端到端：关闭分池排名，确认回退到旧逻辑
7. 使用现有 job 运行，确认向后兼容

## 后续建议

1. **飞书推送格式**：当前推送格式未变，后续可考虑在推送中标注文章所属类别池
2. **配额动态调整**：可基于历史数据自动建议最优配额
3. **前端可视化**：可添加分池排名结果的可视化图表
4. **性能监控**：当文章量大时，分池排名算法的性能需要监控

## 技术债务

- `_MISSING` sentinel 在 repository.py 中使用，可考虑用 Pydantic 的 `exclude_unset` 统一
- 前端 `ai_category_tags` 和 `dev_category_tags` 当前为 JSON 字符串输入，后续可改为标签选择器
