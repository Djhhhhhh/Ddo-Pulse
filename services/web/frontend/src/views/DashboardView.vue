<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import SafeMarkdown from "../components/SafeMarkdown.vue";
import {
  api,
  type Dashboard,
  type DigestToday,
  type JobRun,
  type JobRunDetail,
  type PipelineJob,
} from "../api/client";

const dashboard = ref<Dashboard | null>(null);
const digest = ref<DigestToday | null>(null);
const jobs = ref<PipelineJob[]>([]);
const runs = ref<JobRun[]>([]);
const selectedRunId = ref<number | null>(null);
const runDetail = ref<JobRunDetail | null>(null);
const error = ref("");
const digestJobId = ref<number | null>(null);

const selectedRunLabel = computed(() => {
  const r = runs.value.find((x) => x.id === selectedRunId.value);
  if (!r) return "";
  const name = r.pipeline_job_name || `#${r.pipeline_job_id ?? "-"}`;
  return `${r.started_at} · ${name} · ${r.status}`;
});

async function loadDigest() {
  const jid = digestJobId.value;
  if (jid == null) {
    digest.value = null;
    return;
  }
  digest.value = await api.digestToday(jid);
}

async function loadRuns() {
  runs.value = await api.jobRuns(50);
}

async function refresh() {
  error.value = "";
  try {
    jobs.value = await api.pipelineJobs();
    if (
      digestJobId.value != null &&
      !jobs.value.some((j) => j.id === digestJobId.value)
    ) {
      digestJobId.value = null;
    }
    if (digestJobId.value == null && jobs.value.length) {
      digestJobId.value = jobs.value[0].id;
    }
    const dj = digestJobId.value ?? undefined;
    dashboard.value = await api.dashboard(dj);
    await loadDigest();
    await loadRuns();
    selectedRunId.value = runs.value[0]?.id ?? null;
    if (selectedRunId.value) await loadRunDetail(selectedRunId.value);
    else runDetail.value = null;
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

async function loadRunDetail(id: number) {
  try {
    runDetail.value = await api.jobRun(id);
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
    runDetail.value = null;
  }
}

onMounted(refresh);

watch(digestJobId, async () => {
  try {
    if (digestJobId.value == null) {
      digest.value = null;
      return;
    }
    dashboard.value = await api.dashboard(digestJobId.value);
    await loadDigest();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
});

watch(selectedRunId, (id) => {
  if (id != null) loadRunDetail(id);
});
</script>

<template>
  <div class="dash-page">
    <header class="dash-head">
      <div>
        <h1>Dashboard</h1>
        <p class="muted">今日精选与任务概览</p>
      </div>
      <div v-if="jobs.length" class="job-pick">
        <label class="label">Digest 所属任务</label>
        <div class="select-wrap dash-select">
          <select v-model.number="digestJobId" class="select">
            <option v-for="j in jobs" :key="j.id" :value="j.id">{{ j.name }}</option>
          </select>
        </div>
      </div>
    </header>

    <p v-if="error" class="error">{{ error }}</p>

    <section v-if="dashboard" class="stat-row">
      <div class="stat-card stat-card--accent">
        <span class="stat-icon" aria-hidden="true">◎</span>
        <div>
          <p class="stat-label">订阅源（启用/总数）</p>
          <p class="stat-num">
            {{ dashboard.enabled_sources_count }}<span class="stat-denom">/{{ dashboard.sources_count }}</span>
          </p>
        </div>
      </div>
      <div class="stat-card">
        <span class="stat-icon" aria-hidden="true">↓</span>
        <div>
          <p class="stat-label">已抓取条目</p>
          <p class="stat-num">{{ dashboard.raw_items_count }}</p>
        </div>
      </div>
      <div class="stat-card">
        <span class="stat-icon" aria-hidden="true">✎</span>
        <div>
          <p class="stat-label">已分析</p>
          <p class="stat-num">{{ dashboard.analyzed_count }}</p>
        </div>
      </div>
      <div class="stat-card stat-card--warn">
        <span class="stat-icon" aria-hidden="true">⏱</span>
        <div>
          <p class="stat-label">待分析</p>
          <p class="stat-num">{{ dashboard.pending_analyze }}</p>
        </div>
      </div>
      <div class="stat-card stat-card--ok">
        <span class="stat-icon" aria-hidden="true">★</span>
        <div>
          <p class="stat-label">精选文章</p>
          <p class="stat-num">{{ dashboard.quality_count }}</p>
        </div>
      </div>
    </section>

    <section v-if="digest?.markdown_body" class="card digest-full">
      <div class="digest-head">
        <h2 class="digest-section-title">今日 Digest</h2>
        <p class="muted digest-meta">{{ digest.date }} · {{ digest.item_ids.length }} 篇</p>
      </div>
      <div class="digest-markdown-wrap">
        <SafeMarkdown :source="digest.markdown_body" />
      </div>
    </section>

    <section v-else-if="dashboard?.digest_date && !digest?.markdown_body" class="card muted-block">
      <p class="muted">今日尚无 Digest 正文，运行定时任务后将在此展示。</p>
    </section>

    <section class="split">
      <aside class="split-side card">
        <h3>最近任务</h3>
        <p class="muted small">点击条目查看详情（含 Markdown 或运行摘要）</p>
        <ul class="run-list">
          <li v-for="r in runs" :key="r.id">
            <button
              type="button"
              class="run-item"
              :class="{ active: selectedRunId === r.id }"
              @click="selectedRunId = r.id"
            >
              <span class="run-status" :data-s="r.status">{{ r.status }}</span>
              <span class="run-title">{{ r.pipeline_job_name || "任务" }} · {{ r.started_at?.slice(0, 19) }}</span>
            </button>
          </li>
        </ul>
        <p v-if="!runs.length" class="muted">暂无运行记录</p>
      </aside>
      <div class="split-main card">
        <template v-if="runDetail">
          <h3 class="detail-section-title">任务详情</h3>
          <p class="muted detail-meta">{{ selectedRunLabel }}</p>
          <div v-if="runDetail.markdown_body" class="detail-md detail-md--scaled">
            <SafeMarkdown :source="runDetail.markdown_body" />
          </div>
          <div v-else-if="runDetail.result_json" class="detail-json">
            <pre>{{ runDetail.result_json }}</pre>
          </div>
          <p v-if="runDetail.error" class="error tight">{{ runDetail.error }}</p>
        </template>
        <p v-else class="muted">选择左侧一条任务</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.dash-page {
  max-width: 1200px;
}
.dash-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 8px;
}
.job-pick .label {
  margin-bottom: 4px;
}
.dash-select {
  width: 100%;
  max-width: 320px;
}
.stat-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 14px;
  margin: 24px 0;
}
.stat-card {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 18px 20px;
  border-radius: var(--radius-card);
  border: 1px solid var(--border);
  background: linear-gradient(145deg, var(--bg) 0%, var(--surface) 100%);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
.stat-card--accent {
  border-color: #c7d2fe;
  background: linear-gradient(145deg, #eef2ff 0%, var(--bg) 100%);
}
.stat-card--warn {
  border-color: #fde68a;
  background: linear-gradient(145deg, #fffbeb 0%, var(--bg) 100%);
}
.stat-card--ok {
  border-color: #bbf7d0;
  background: linear-gradient(145deg, #ecfdf5 0%, var(--bg) 100%);
}
.stat-icon {
  font-size: 1.4rem;
  opacity: 0.75;
  line-height: 1;
}
.stat-label {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-secondary);
}
.stat-num {
  margin: 4px 0 0;
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.02em;
}
.stat-denom {
  font-size: 1rem;
  font-weight: 400;
  color: var(--text-secondary);
}
.digest-full {
  margin-bottom: 24px;
}
.digest-head {
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}
.digest-section-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: -0.01em;
}
.digest-meta {
  margin: 4px 0 0;
  font-size: 0.8rem;
}
.digest-markdown-wrap :deep(.markdown-body h1) {
  font-size: 1.15rem;
  margin-top: 0;
  font-weight: 650;
}
.digest-markdown-wrap :deep(.markdown-body h2) {
  font-size: 1.02rem;
}
.digest-markdown-wrap :deep(.markdown-body h3) {
  font-size: 0.95rem;
}
.digest-markdown-wrap :deep(.markdown-body p),
.digest-markdown-wrap :deep(.markdown-body li) {
  font-size: 0.875rem;
  line-height: 1.55;
}
.muted-block {
  margin-bottom: 24px;
}
.split {
  display: grid;
  grid-template-columns: minmax(240px, 320px) 1fr;
  gap: 20px;
  align-items: start;
}
@media (max-width: 800px) {
  .split {
    grid-template-columns: 1fr;
  }
}
.split-side h3 {
  margin-top: 0;
  font-size: 0.98rem;
  font-weight: 600;
}
.detail-section-title {
  margin: 0;
  font-size: 0.98rem;
  font-weight: 600;
}
.detail-meta {
  margin: 4px 0 0;
  font-size: 0.78rem;
  line-height: 1.35;
}
.small {
  font-size: 0.8rem;
}
.run-list {
  list-style: none;
  margin: 12px 0 0;
  padding: 0;
  max-height: 420px;
  overflow-y: auto;
}
.run-item {
  width: 100%;
  text-align: left;
  padding: 10px 12px;
  margin-bottom: 6px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.run-item:hover {
  background: var(--surface);
}
.run-item.active {
  border-color: var(--text);
  background: var(--surface);
}
.run-status {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
}
.run-status[data-s="ok"] {
  color: #15803d;
}
.run-status[data-s="failed"] {
  color: #b91c1c;
}
.run-title {
  font-size: 0.85rem;
  line-height: 1.3;
}
.detail-md {
  margin-top: 12px;
}
.detail-md--scaled :deep(.markdown-body h1) {
  font-size: 1.08rem;
  margin-top: 0;
}
.detail-md--scaled :deep(.markdown-body h2) {
  font-size: 0.98rem;
}
.detail-md--scaled :deep(.markdown-body h3) {
  font-size: 0.92rem;
}
.detail-md--scaled :deep(.markdown-body p),
.detail-md--scaled :deep(.markdown-body li) {
  font-size: 0.82rem;
  line-height: 1.5;
}
.detail-json pre {
  margin: 12px 0 0;
  padding: 10px 12px;
  background: var(--surface);
  border-radius: 8px;
  font-size: 0.76rem;
  line-height: 1.45;
  overflow: auto;
  max-height: 480px;
}
.tight {
  margin-top: 12px;
}
</style>
