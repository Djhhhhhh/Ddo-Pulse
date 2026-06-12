<script setup lang="ts">
/**
 * 提示词配置组件
 * 系统模板选择 + 用户需求输入 → 最终提示词预览
 */
import { computed } from "vue";

export interface PromptTemplate {
  id: string;
  label: string;
  body: string;
}

const PROMPT_TEMPLATES: PromptTemplate[] = [
  {
    id: "default",
    label: "通用精选",
    body: `你是一位中文技术博客策展编辑。请阅读以下文章信息，判断是否值得推荐给中文读者，并输出**仅包含一个合法 JSON 对象**（不要用 markdown 代码块；字符串内若有双引号须写成 \\"）。

可选分类标签（从中选择 0-3 个最贴切的）：{categories_hint}

读者关注的关键词或主题（可参考，不必逐字命中）：{interest_keywords}

文章标题：{title}

正文摘要：
{content}

输出 JSON 格式（字段名必须一致）：
{{
  "is_quality": true,
  "score": 8,
  "categories": ["AI"],
  "summary_zh": "50-120 字中文摘要（严禁超过 120 字，宁可短）",
  "reason": "一句话说明评分理由（简短）"
}}

{scoring_rubric}`,
  },
  {
    id: "paper",
    label: "论文分析",
    body: `请分析以下论文信息，判断其学术价值。

## 可用分类标签
{categories_hint}

## 读者研究兴趣
{interest_keywords}

## 论文信息
**标题**：{title}
**内容**：
{content}

## 评分标准
{scoring_rubric}

## 输出格式
请输出以下 JSON 结构（字段名必须一致）：
{{
  "is_quality": true,
  "score": 8,
  "categories": ["标签1", "标签2"],
  "summary_zh": "50-120字中文摘要",
  "reason": "一句话评分理由",
  "novelty": "high",
  "methodology": "一句话概括研究方法",
  "key_findings": ["核心发现1"],
  "practical_value": "high"
}}`,
  },
];

const props = defineProps<{
  systemTemplate: string;
  userPrompt: string;
}>();

const emit = defineEmits<{
  "update:systemTemplate": [body: string];
  "update:userPrompt": [text: string];
}>();

const selectedTemplateId = computed(() => {
  const hit = PROMPT_TEMPLATES.find((t) => t.body === props.systemTemplate);
  return hit?.id ?? "default";
});

const finalPreview = computed(() => {
  const base = props.systemTemplate || PROMPT_TEMPLATES[0].body;
  if (!props.userPrompt?.trim()) return base;
  return `${base}\n\n用户补充需求：${props.userPrompt.trim()}`;
});

function onTemplateSelect(ev: Event) {
  const el = ev.target as HTMLSelectElement;
  const tpl = PROMPT_TEMPLATES.find((t) => t.id === el.value);
  if (tpl) emit("update:systemTemplate", tpl.body);
}

function onUserInput(ev: Event) {
  const el = ev.target as HTMLTextAreaElement;
  emit("update:userPrompt", el.value);
}

defineExpose({ PROMPT_TEMPLATES });
</script>

<template>
  <div class="pts">
    <label class="label">提示词配置</label>

    <label class="label sub-label">用户需求描述</label>
    <textarea
      class="textarea"
      :value="userPrompt"
      rows="2"
      placeholder="描述你关注的领域和偏好，如：关注 AI 大模型和 RAG，偏好实战分享"
      @input="onUserInput"
    />

    <div class="pts-row">
      <div class="pts-col">
        <label class="label sub-label">系统模板</label>
        <div class="select-wrap">
          <select class="select" :value="selectedTemplateId" @change="onTemplateSelect">
            <option v-for="t in PROMPT_TEMPLATES" :key="t.id" :value="t.id">
              {{ t.label }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <label class="label sub-label">最终提示词预览</label>
    <textarea
      class="textarea pts-preview"
      :value="finalPreview"
      rows="8"
      readonly
      disabled
    />
  </div>
</template>

<style scoped>
.pts {
  width: 100%;
  padding-top: 8px;
}
.sub-label {
  margin-top: 8px;
  font-size: 0.88rem;
}
.pts-row {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}
.pts-col {
  flex: 1;
  min-width: 0;
}
.pts-preview {
  opacity: 0.75;
  cursor: not-allowed;
  background: var(--surface);
  resize: none;
  font-size: 0.82rem;
  line-height: 1.5;
}
</style>
