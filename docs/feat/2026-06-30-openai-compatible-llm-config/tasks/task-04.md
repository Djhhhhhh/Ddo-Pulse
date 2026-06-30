# task-04: 前端 UI — SettingsView.vue 增加 base_url 输入框

> 关联验收点：G4 (human × 6), G5 (human × 2)

## 目标

在设置页 LLM section 的每个 profile 卡片中增加 base_url 输入框，实现完整的配置闭环。

## 修改文件

- `services/web/frontend/src/views/SettingsView.vue`

## 具体改动

### 1. profileDraft 类型扩展

```typescript
const profileDraft = ref<Record<number, {
  base_url: string;  // 新增
  model: string;
}>>({});
```

### 2. refresh() 中初始化 base_url

```typescript
profileDraft.value[p.id] = {
  base_url: p.base_url,  // 新增
  model: p.model,
};
```

### 3. LLM section 模板增加 base_url 输入框

在 `<p><strong>{{ p.name }}</strong></p>` 之后、model 输入框之前，增加：

```html
<div class="full">
  <label class="label">Base URL</label>
  <input
    v-model="profileDraft[p.id].base_url"
    class="input"
    placeholder="https://openrouter.ai/api/v1"
  />
</div>
```

### 4. saveProfile() 增加 base_url

```typescript
const body: Record<string, unknown> = {
  base_url: d.base_url,  // 新增
  model: d.model,
};
```

## 验收标准

- [ ] 每个 profile 卡片显示 base_url、model、API Key 三个输入框
- [ ] base_url placeholder 显示 `https://openrouter.ai/api/v1`
- [ ] base_url 回填当前值
- [ ] 保存后刷新页面 base_url 保持不变
- [ ] 清空 base_url 保存后恢复默认值
