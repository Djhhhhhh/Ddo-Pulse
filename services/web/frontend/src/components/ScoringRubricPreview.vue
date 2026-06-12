<script setup lang="ts">
/**
 * 评分侧重点只读预览组件
 * 提供 3 个预设模板切换查看，不允许编辑。
 */
import { computed } from "vue";

export interface RubricPreset {
  id: string;
  label: string;
  hint: string;
  body: string;
}

const RUBRIC_PRESETS: RubricPreset[] = [
  {
    id: "balanced",
    label: "均衡精选（推荐）",
    hint: "兼顾新颖度、可读性与主题相关度，适合多数订阅场景。",
    body: `采用 10 分制为文章打分，维度如下：
- 信息新颖度与对目标读者的实际价值（约占 30%）
- 论述是否清晰、结论是否可验证或可落地（约占 30%）
- 与当前关注主题 / 关键词的相关程度（约占 40%）

分数含义建议：
9–10：必读级，有明显稀缺观点或可立刻行动的建议。
7–8：值得一读，有清晰增量信息。
5–6：可读但增量有限或偏综述。
1–4：价值偏低、陈旧信息较多或与主题弱相关。

请严格按系统约定的 JSON 结构输出分数与理由。`,
  },
  {
    id: "tech_depth",
    label: "技术深度优先",
    hint: "适合开发者向订阅：实现细节、教训与可复现性权重大。",
    body: `采用 10 分制，偏重技术与工程深度：
- 是否有具体实现细节、数据、边界情况或代码级洞察（权重大）
- 是否澄清常见误区、给出可操作的排查或优化路径
- 泛泛而谈、纯营销口径或与实践脱节则显著扣分

分数含义建议：
8–10：对专业读者有明显启发，可指导实际工作。
6–7：有一定技术增量但深度一般。
4–5：概念正确但缺少实质细节。
1–3：空洞或与工程实践无关。

请严格按系统约定的 JSON 结构输出分数与理由。`,
  },
  {
    id: "timely",
    label: "时效与影响力优先",
    hint: "适合新闻向订阅：新近、影响面广、一手视角加分。",
    body: `采用 10 分制，偏重时效与影响：
- 事件或观点是否新近，对行业/用户是否有广泛影响（权重大）
- 是否有一手信息、独家视角或可核验的来源支撑
- 重复报道、迟到综述或二手拼凑则扣分

分数含义建议：
8–10：高优先级跟进，可能改变读者决策或认知。
6–7：有价值但不是窗口期必读。
4–5：信息尚可但时效或独特性不足。
1–3：过时或转载堆砌。

请严格按系统约定的 JSON 结构输出分数与理由。`,
  },
];

const props = defineProps<{
  /** 当前选中的模板 id */
  modelValue: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [id: string];
  /** 模板 body 变化时触发 */
  "update:body": [body: string];
}>();

const selectedId = computed({
  get: () => props.modelValue || "balanced",
  set: (id: string) => {
    emit("update:modelValue", id);
    const preset = RUBRIC_PRESETS.find((p) => p.id === id);
    if (preset) emit("update:body", preset.body);
  },
});

const currentPreset = computed(
  () => RUBRIC_PRESETS.find((p) => p.id === selectedId.value) ?? RUBRIC_PRESETS[0]
);

const currentHint = computed(() => currentPreset.value.hint);

const currentBody = computed(() => currentPreset.value.body);

function onSelect(ev: Event) {
  const el = ev.target as HTMLSelectElement;
  selectedId.value = el.value;
}

// 导出预设列表供父组件使用
defineExpose({ RUBRIC_PRESETS });
</script>

<template>
  <div class="scoring-rubric-preview">
    <label class="label">评分侧重点</label>
    <div class="select-wrap">
      <select class="select" :value="selectedId" @change="onSelect">
        <option v-for="p in RUBRIC_PRESETS" :key="p.id" :value="p.id">
          {{ p.label }}
        </option>
      </select>
    </div>
    <p class="muted small field-hint">{{ currentHint }}</p>
    <textarea
      class="textarea rubric-readonly"
      :value="currentBody"
      rows="8"
      readonly
      disabled
    />
  </div>
</template>

<style scoped>
.scoring-rubric-preview {
  width: 100%;
}
.rubric-readonly {
  opacity: 0.75;
  cursor: not-allowed;
  background: var(--surface);
  resize: none;
}
.field-hint {
  margin: 0 0 8px;
  line-height: 1.45;
}
.subtle-top {
  margin-top: 12px;
}
</style>
