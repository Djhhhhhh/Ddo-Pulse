<script setup lang="ts">
import MarkdownIt from "markdown-it";
import DOMPurify from "dompurify";
import { computed } from "vue";

const props = defineProps<{
  source: string;
}>();

const md = new MarkdownIt({ html: false, linkify: true, breaks: true });

const html = computed(() => {
  const raw = md.render(props.source || "");
  return DOMPurify.sanitize(raw);
});
</script>

<template>
  <div class="markdown-body" v-html="html" />
</template>

<style scoped>
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  margin-top: 1.25em;
  margin-bottom: 0.5em;
}
.markdown-body :deep(p) {
  margin: 0.6em 0;
}
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 1.5rem;
}
.markdown-body :deep(code) {
  font-size: 0.9em;
  background: var(--surface);
  padding: 0.1em 0.35em;
  border-radius: 4px;
}
.markdown-body :deep(pre) {
  background: var(--surface);
  padding: 12px;
  border-radius: var(--radius-card);
  overflow: auto;
}
.markdown-body :deep(a) {
  color: #2563eb;
}
</style>
