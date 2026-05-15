<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { api, type Article } from "../api/client";

const route = useRoute();
const article = ref<Article | null>(null);
const error = ref("");

onMounted(async () => {
  const id = Number(route.params.id);
  try {
    article.value = await api.article(id);
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
});
</script>

<template>
  <div class="article-detail-page">
    <template v-if="article">
      <p class="muted">
        <RouterLink to="/articles">← 返回列表</RouterLink>
      </p>
      <h1>{{ article.title }}</h1>
      <p>
        <span class="tag">{{ article.score }} 分</span>
        <span v-if="article.is_quality" class="tag">精选</span>
        <span v-for="c in article.categories" :key="c" class="tag">{{ c }}</span>
      </p>
      <p class="muted">分析于 {{ article.analyzed_at }}</p>
      <section class="card" style="margin-top: 20px">
        <h2>摘要</h2>
        <p>{{ article.summary_zh }}</p>
        <p v-if="article.reason" class="muted" style="margin-top: 12px">{{ article.reason }}</p>
      </section>
      <a :href="article.url" class="btn btn-primary" target="_blank" rel="noopener" style="margin-top: 20px">阅读原文</a>
    </template>
    <p v-else-if="error" class="error">{{ error }}</p>
    <p v-else class="muted">加载中…</p>
  </div>
</template>