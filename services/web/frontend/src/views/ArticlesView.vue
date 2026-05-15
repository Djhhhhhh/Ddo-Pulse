<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { api, type Article } from "../api/client";

const items = ref<Article[]>([]);
const total = ref(0);
const error = ref("");
const days = ref(30);
const minScore = ref<number | "">("");
const titleQ = ref("");
const category = ref("");
const categories = ref<string[]>([]);
const page = ref(0);
const limit = 20;

const dialogOpen = ref(false);
const selected = ref<Article | null>(null);
const dialogEl = ref<HTMLDialogElement | null>(null);

function openArticle(a: Article) {
  selected.value = a;
  dialogOpen.value = true;
  dialogEl.value?.showModal();
}

function closeDialog() {
  dialogOpen.value = false;
  dialogEl.value?.close();
  selected.value = null;
}

async function loadCategories() {
  try {
    const r = await api.articleCategories(365);
    categories.value = r.categories;
  } catch {
    categories.value = [];
  }
}

async function load() {
  error.value = "";
  const params = new URLSearchParams({
    days: String(days.value),
    limit: String(limit),
    offset: String(page.value * limit),
  });
  if (minScore.value !== "") params.set("min_score", String(minScore.value));
  if (category.value) params.set("category", category.value);
  if (titleQ.value.trim()) params.set("q", titleQ.value.trim());
  try {
    const res = await api.articles(params);
    items.value = res.items;
    total.value = res.total;
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

function pickCategory(c: string) {
  category.value = category.value === c ? "" : c;
}

function categoriesLine(a: Article): string {
  return a.categories?.length ? a.categories.join(" · ") : "";
}

onMounted(async () => {
  await loadCategories();
  await load();
});

watch([days, minScore, page, category], load);
</script>

<template>
  <div class="articles-page">
    <h1>文章</h1>
    <p class="muted">已分析文章，共 {{ total }} 篇</p>

    <div class="layout">
      <aside class="side card">
        <div class="side-section">
          <h3 class="side-heading"><span class="side-accent" aria-hidden="true" />筛选</h3>
          <div class="field">
            <label class="label">最近天数</label>
            <input v-model.number="days" type="number" class="input filter-input-full" min="1" />
          </div>
          <div class="field">
            <label class="label">最低分</label>
            <input v-model="minScore" type="number" class="input filter-input-full" min="1" max="10" placeholder="全部" />
          </div>
          <div class="field">
            <label class="label">标题关键词</label>
            <input v-model="titleQ" class="input filter-input-full" placeholder="回车筛选" @keydown.enter="load()" />
          </div>
          <button type="button" class="btn side-apply" @click="load">应用筛选</button>
        </div>

        <div class="side-section">
          <h3 class="side-heading"><span class="side-accent" aria-hidden="true" />分类</h3>
          <p class="muted small">点击切换</p>
          <ul class="cat-list">
            <li v-for="c in categories" :key="c">
              <button type="button" class="cat-btn" :class="{ on: category === c }" @click="pickCategory(c)">
                {{ c }}
              </button>
            </li>
          </ul>
          <p v-if="!categories.length" class="muted small">暂无分类数据</p>
        </div>
      </aside>

      <div class="main">
        <p v-if="error" class="error">{{ error }}</p>

        <div class="card table-wrap">
          <table v-if="items.length" class="data-table">
            <thead>
              <tr>
                <th class="col-n">#</th>
                <th class="col-title">标题</th>
                <th class="col-score">评分</th>
                <th class="col-cats">分类</th>
                <th class="col-time">分析时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(a, idx) in items" :key="a.id" class="row-click" @click="openArticle(a)">
                <td class="muted">{{ page * limit + idx + 1 }}</td>
                <td class="cell-title">
                  <span class="cell-ellipsis" :title="a.title">{{ a.title }}</span>
                </td>
                <td class="cell-score">{{ a.score ?? "—" }}</td>
                <td class="cell-cats">
                  <span class="cell-ellipsis" :title="categoriesLine(a) || undefined">{{
                    categoriesLine(a) || "—"
                  }}</span>
                </td>
                <td class="muted nowrap">{{ a.analyzed_at }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else-if="!error" class="muted inner-pad">暂无文章</p>

          <div v-if="total > limit" class="pager">
            <button type="button" class="btn btn-secondary" :disabled="page === 0" @click="page--">上一页</button>
            <span class="muted">第 {{ page + 1 }} 页</span>
            <button
              type="button"
              class="btn btn-secondary"
              :disabled="(page + 1) * limit >= total"
              @click="page++"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>

    <dialog ref="dialogEl" class="article-dialog ui-motion" @close="dialogOpen = false">
      <div v-if="selected" class="dialog-inner">
        <button type="button" class="close-x" aria-label="关闭" @click="closeDialog">×</button>
        <h2>{{ selected.title }}</h2>
        <p>
          <span class="tag">{{ selected.score ?? "—" }} 分</span>
          <span v-if="selected.is_quality" class="tag">精选</span>
          <span v-for="c in selected.categories" :key="c" class="tag">{{ c }}</span>
        </p>
        <p class="muted small">分析于 {{ selected.analyzed_at }}</p>
        <section class="block">
          <h3>摘要</h3>
          <p>{{ selected.summary_zh || "—" }}</p>
          <div v-if="selected.reason" class="reason">
            <p class="label">评分理由</p>
            <p class="muted">{{ selected.reason }}</p>
          </div>
        </section>
        <a :href="selected.url" class="btn btn-primary" target="_blank" rel="noopener">阅读原文</a>
      </div>
    </dialog>
  </div>
</template>

<style scoped>
.articles-page {
  max-width: 1280px;
}
.layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 20px;
  margin-top: 20px;
  align-items: start;
}
@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
.side {
  position: sticky;
  top: 20px;
  padding: 22px 20px;
  background: linear-gradient(165deg, #f8fafc 0%, var(--bg) 42%, var(--bg) 100%);
  border: 1px solid #e2e8f0;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
}
.side-section + .side-section {
  margin-top: 22px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}
.side-heading {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 14px;
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: -0.02em;
}
.side-accent {
  display: inline-block;
  width: 4px;
  height: 1em;
  border-radius: 4px;
  background: linear-gradient(180deg, #6366f1 0%, #8b5cf6 100%);
  flex-shrink: 0;
}
.field {
  margin-bottom: 14px;
}
.field .label {
  font-weight: 500;
}
.filter-input-full {
  width: 100%;
  max-width: none;
  box-sizing: border-box;
}
.mt {
  margin-top: 20px;
}
.cat-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.cat-list li {
  list-style: none;
  margin: 0;
  padding: 0;
}
.side-apply {
  width: 100%;
  margin-top: 8px;
}
.cat-btn {
  display: inline-flex;
  align-items: center;
  padding: 7px 14px;
  margin: 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  background: var(--bg);
  cursor: pointer;
  font-size: 0.82rem;
  transition: border-color 0.18s var(--ease-page, ease), background 0.18s ease, transform 0.15s ease;
}
.cat-btn:hover {
  border-color: #c7d2fe;
  background: #eef2ff;
}
.cat-btn.on {
  border-color: #6366f1;
  background: linear-gradient(145deg, #eef2ff 0%, #e0e7ff 100%);
  color: #312e81;
  font-weight: 500;
}
.small {
  font-size: 0.8rem;
}
.table-wrap {
  padding: 0;
  overflow: auto;
}
.data-table {
  table-layout: fixed;
  width: 100%;
  min-width: 640px;
}
.col-n {
  width: 44px;
}
.col-score {
  width: 56px;
}
.col-title {
  width: 36%;
}
.col-cats {
  width: 22%;
}
.col-time {
  width: 148px;
}
.cell-title,
.cell-cats {
  overflow: hidden;
}
.cell-score {
  white-space: nowrap;
}
.cell-ellipsis {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.row-click {
  cursor: pointer;
}
.row-click:hover {
  background: var(--surface);
}
.nowrap {
  white-space: nowrap;
}
.inner-pad {
  padding: 24px;
}
.pager {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid var(--border);
}
.article-dialog {
  border: none;
  border-radius: var(--radius-card);
  padding: 0;
  max-width: 640px;
  width: calc(100vw - 32px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}
.article-dialog::backdrop {
  background: rgba(0, 0, 0, 0.35);
}
.dialog-inner {
  padding: 28px 32px;
  position: relative;
}
.close-x {
  position: absolute;
  top: 12px;
  right: 12px;
  border: none;
  background: transparent;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: var(--text-secondary);
}
.block {
  margin: 20px 0;
}
.reason {
  margin-top: 16px;
}
</style>
