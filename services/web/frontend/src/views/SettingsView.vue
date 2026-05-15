<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import {
  api,
  type JobRun,
  type PipelineJob,
  type Profile,
  type Source,
} from "../api/client";

type Section = "pipeline" | "llm";

const section = ref<Section>("pipeline");
const error = ref("");
const message = ref("");

const jobs = ref<PipelineJob[]>([]);
const selectedJobId = ref<number | null>(null);
const sources = ref<Source[]>([]);

const profiles = ref<Profile[]>([]);

const profileKey = ref<Record<number, string>>({});
const runMsg = ref("");
const jobRunning = ref(false);
const jobRuns = ref<JobRun[]>([]);

const sourceDialog = ref<HTMLDialogElement | null>(null);
const newSource = ref({
  name: "",
  type: "rss",
  url: "",
  config_json: "{}",
  analyze_limit: null as number | null,
});
const testMsg = ref("");

/** 评分侧重点：用户只需选类型，具体打分细则由预设文案给出（仍可微调）。 */
const RUBRIC_PRESETS = [
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

const rubricPresetId = ref<string>("custom");

const rubricHint = computed(() => {
  const p = RUBRIC_PRESETS.find((x) => x.id === rubricPresetId.value);
  return p?.hint ?? "可直接编辑评分说明。模型按 10 分制输出分数，再结合「精选阈值」决定是否入选 Digest。";
});

type JobFormMode = "create" | "edit";

const jobFormDialog = ref<HTMLDialogElement | null>(null);
const jobFormMode = ref<JobFormMode>("create");

const jobModal = ref({
  name: "",
  schedule_cron: "0 8 * * *",
  enabled: true,
  feishu_webhook_url: "",
  push_digest: false,
  analyze_limit: 50,
  digest_top_n: 8,
  score_threshold: 7,
  keywordsText: "",
  keyword_prefilter: false,
  prompt_template: "",
  scoring_rubric: "",
  system_prompt: "",
  llm_profile_id: "" as string,
});

function syncRubricPresetFromDraft(text: string) {
  const t = text.trim();
  const hit = RUBRIC_PRESETS.find((p) => p.body.trim() === t);
  rubricPresetId.value = hit ? hit.id : "custom";
}

function onRubricPresetChange(id: string) {
  rubricPresetId.value = id;
  if (id === "custom") return;
  const p = RUBRIC_PRESETS.find((x) => x.id === id);
  if (p) jobModal.value.scoring_rubric = p.body;
}

function onRubricPresetSelect(ev: Event) {
  const el = ev.target as HTMLSelectElement;
  onRubricPresetChange(el.value);
}

function populateJobModalFromJob(j: PipelineJob) {
  jobModal.value = {
    name: j.name,
    schedule_cron: j.schedule_cron,
    enabled: j.enabled,
    feishu_webhook_url: j.feishu_webhook_url || "",
    push_digest: j.push_digest,
    analyze_limit: j.analyze_limit,
    digest_top_n: j.digest_top_n,
    score_threshold: j.score_threshold,
    keywordsText: j.interest_keywords?.length ? j.interest_keywords.join("\n") : "",
    keyword_prefilter: j.keyword_prefilter,
    prompt_template: j.prompt_template || "",
    scoring_rubric: j.scoring_rubric || "",
    system_prompt: j.system_prompt || "",
    llm_profile_id: j.llm_profile_id != null ? String(j.llm_profile_id) : "",
  };
  syncRubricPresetFromDraft(j.scoring_rubric || "");
}

function openCreateJobModal() {
  jobFormMode.value = "create";
  jobModal.value = {
    name: `定时任务 ${jobs.value.length + 1}`,
    schedule_cron: "0 8 * * *",
    enabled: true,
    feishu_webhook_url: "",
    push_digest: false,
    analyze_limit: 50,
    digest_top_n: 8,
    score_threshold: 7,
    keywordsText: "",
    keyword_prefilter: false,
    prompt_template: "",
    scoring_rubric: RUBRIC_PRESETS[0].body,
    system_prompt: "",
    llm_profile_id: "",
  };
  rubricPresetId.value = "balanced";
  jobFormDialog.value?.showModal();
}

function openEditJobModal() {
  const j = jobs.value.find((x) => x.id === selectedJobId.value);
  if (!j) return;
  jobFormMode.value = "edit";
  populateJobModalFromJob(j);
  jobFormDialog.value?.showModal();
}

async function submitJobModal() {
  message.value = "";
  error.value = "";
  const m = jobModal.value;
  const kws = m.keywordsText
    .split(/[\n,，]+/)
    .map((s) => s.trim())
    .filter(Boolean);
  const whIn = m.feishu_webhook_url.trim();

  if (jobFormMode.value === "create" && !whIn) {
    error.value = "请填写飞书 Webhook URL（每个任务单独配置）";
    return;
  }

  const base: Record<string, unknown> = {
    name: m.name.trim(),
    schedule_cron: m.schedule_cron.trim(),
    enabled: m.enabled,
    analyze_limit: m.analyze_limit,
    digest_top_n: m.digest_top_n,
    push_digest: m.push_digest,
    score_threshold: m.score_threshold,
    interest_keywords: kws,
    keyword_prefilter: m.keyword_prefilter,
    prompt_template: m.prompt_template || null,
    scoring_rubric: m.scoring_rubric || null,
    system_prompt: m.system_prompt || null,
    llm_profile_id: m.llm_profile_id === "" ? null : Number(m.llm_profile_id),
  };

  try {
    if (jobFormMode.value === "create") {
      await api.createPipelineJob({ ...base, feishu_webhook_url: whIn });
      message.value = "已创建定时任务";
    } else {
      const id = selectedJobId.value;
      if (id == null) return;
      const patch = { ...base };
      if (whIn) patch.feishu_webhook_url = whIn;
      await api.updatePipelineJob(id, patch);
      message.value = "已保存任务配置";
    }
    await api.reloadScheduler();
    jobFormDialog.value?.close();
    await refresh();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

async function patchJobEnabled(j: PipelineJob, enabled: boolean) {
  error.value = "";
  try {
    await api.updatePipelineJob(j.id, { enabled });
    await api.reloadScheduler();
    await refresh();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

function onJobEnabledInput(j: PipelineJob, ev: Event) {
  const el = ev.target as HTMLInputElement;
  patchJobEnabled(j, el.checked);
}

const profileDraft = ref<Record<number, {
  model: string;
  score_threshold: number;
  prompt_template: string;
  system_prompt: string;
  category_hints_text: string;
  temperature: number;
  max_tokens: number;
}>>({});

const selectedJob = computed(() => jobs.value.find((j) => j.id === selectedJobId.value) ?? null);

async function loadJobRuns() {
  const jid = selectedJobId.value;
  if (jid == null) {
    jobRuns.value = [];
    return;
  }
  try {
    jobRuns.value = await api.jobRuns(40, jid);
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
    jobRuns.value = [];
  }
}

async function refresh() {
  error.value = "";
  try {
    jobs.value = await api.pipelineJobs();
    if (
      selectedJobId.value != null &&
      !jobs.value.some((j) => j.id === selectedJobId.value)
    ) {
      selectedJobId.value = null;
    }
    if (selectedJobId.value == null && jobs.value.length) {
      selectedJobId.value = jobs.value[0].id;
    }
    profiles.value = await api.profiles();
    for (const p of profiles.value) {
      profileDraft.value[p.id] = {
        model: p.model,
        score_threshold: p.score_threshold,
        prompt_template: p.prompt_template || "",
        system_prompt: p.system_prompt || "",
        category_hints_text: p.category_hints.join("\n"),
        temperature: p.temperature,
        max_tokens: p.max_tokens,
      };
    }
    if (selectedJobId.value) {
      sources.value = await api.sources(selectedJobId.value);
      await loadJobRuns();
    } else {
      sources.value = [];
      jobRuns.value = [];
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

onMounted(refresh);

watch(selectedJobId, async (id) => {
  if (id == null) {
    sources.value = [];
    jobRuns.value = [];
    return;
  }
  try {
    sources.value = await api.sources(id);
    await loadJobRuns();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
});

watch(
  jobs,
  (list) => {
    if (selectedJobId.value == null && list.length) {
      selectedJobId.value = list[0].id;
    }
  },
  { deep: true }
);

watch(
  () => jobModal.value.scoring_rubric,
  (text) => {
    syncRubricPresetFromDraft(text || "");
  }
);

async function removeJob() {
  const id = selectedJobId.value;
  if (id == null || !confirm("确定删除该定时任务？关联订阅源会一并删除。")) return;
  try {
    await api.deletePipelineJob(id);
    selectedJobId.value = null;
    await refresh();
    if (jobs.value.length) selectedJobId.value = jobs.value[0].id;
    message.value = "已删除";
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

async function runCurrentJob() {
  runMsg.value = "";
  const id = selectedJobId.value;
  const job = selectedJob.value;
  if (id == null || job == null || jobRunning.value) return;
  jobRunning.value = true;
  runMsg.value = "任务运行中，请稍候…";
  try {
    const wantPush = Boolean(job.push_digest);
    const params: {
      skip_push: boolean;
      analyze_limit?: number;
    } = {
      skip_push: !wantPush,
    };
    if (job.analyze_limit > 0) params.analyze_limit = job.analyze_limit;
    const res = await api.runPipelineJob(id, params);
    const st = res.stats as Record<string, unknown>;
    const pushed = Boolean(st.pushed);
    const pushSkipped = Boolean(st.push_skipped);
    const pushReason = String(st.push_skip_reason || "");
    const pushLabels: Record<string, string> = {
      push_disabled: "已跳过（任务未开启推送 Digest）",
      no_webhook: "已跳过（未配置 Webhook）",
      already_pushed: "已跳过（该 Digest 已成功推送过）",
      no_enabled_sources: "已跳过（无已启用的订阅源）",
    };

    if (!res.ok) {
      runMsg.value = "运行结束（状态异常，请查看下方日志）";
    } else if (wantPush) {
      if (pushed) runMsg.value = "本次运行已完成，已发起飞书推送";
      else if (pushSkipped)
        runMsg.value = `本次运行已完成；飞书：${pushLabels[pushReason] || `已跳过（${pushReason || "未知原因"}）`}`;
      else runMsg.value = "本次运行已完成";
    } else {
      runMsg.value = "本次运行已完成（未勾选「推送 Digest」，已跳过飞书）";
    }
    await refresh();
    await loadJobRuns();
  } catch (e) {
    runMsg.value = e instanceof Error ? e.message : String(e);
  } finally {
    jobRunning.value = false;
  }
}

function openSourceDialog() {
  newSource.value = {
    name: "",
    type: "rss",
    url: "",
    config_json: "{}",
    analyze_limit: null,
  };
  testMsg.value = "";
  sourceDialog.value?.showModal();
}

async function testNewSource() {
  testMsg.value = "";
  try {
    const r = await api.testSourceFetch({
      type: newSource.value.type,
      url: newSource.value.url,
      config_json: newSource.value.config_json,
    });
    testMsg.value = `可抓取 ${r.count} 条；示例：${r.sample.map((x) => x.title).join("；")}`;
  } catch (e) {
    testMsg.value = e instanceof Error ? e.message : String(e);
  }
}

async function addSource() {
  const jid = selectedJobId.value;
  if (jid == null) return;
  try {
    const body: Record<string, unknown> = {
      job_id: jid,
      name: newSource.value.name,
      type: newSource.value.type,
      url: newSource.value.url,
      config_json: newSource.value.config_json,
      enabled: true,
    };
    const cap = newSource.value.analyze_limit;
    if (cap != null && cap > 0) body.analyze_limit = cap;
    await api.createSource(body);
    sourceDialog.value?.close();
    message.value = "已添加订阅源";
    await refresh();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

async function patchSourceEnabled(s: Source, enabled: boolean) {
  error.value = "";
  try {
    await api.updateSource(s.id, { enabled });
    if (selectedJobId.value) sources.value = await api.sources(selectedJobId.value);
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
    await refresh();
  }
}

function onSourceEnabledInput(s: Source, ev: Event) {
  const el = ev.target as HTMLInputElement;
  patchSourceEnabled(s, el.checked);
}

async function removeSource(id: number) {
  if (!confirm("删除该订阅源？")) return;
  await api.deleteSource(id);
  if (selectedJobId.value) sources.value = await api.sources(selectedJobId.value);
}

async function saveProfile(p: Profile) {
  const d = profileDraft.value[p.id];
  if (!d) return;
  const key = profileKey.value[p.id];
  const hints = d.category_hints_text
    .split(/[\n,，]+/)
    .map((s) => s.trim())
    .filter(Boolean);
  const body: Record<string, unknown> = {
    model: d.model,
    score_threshold: d.score_threshold,
    prompt_template: d.prompt_template || null,
    system_prompt: d.system_prompt || null,
    category_hints: hints,
    temperature: d.temperature,
    max_tokens: d.max_tokens,
  };
  if (key) body.api_key = key;
  await api.updateProfile(p.id, body);
  profileKey.value[p.id] = "";
  profiles.value = await api.profiles();
}

async function onSourceAnalyzeLimitChange(s: Source, ev: Event) {
  const el = ev.target as HTMLInputElement;
  const raw = el.value.trim();
  let next: number | null;
  if (raw === "") {
    next = null;
  } else {
    const n = Number(raw);
    if (!Number.isFinite(n)) {
      el.value = s.analyze_limit != null ? String(s.analyze_limit) : "";
      return;
    }
    next = Math.min(50000, Math.max(1, Math.floor(n)));
  }
  const prev = s.analyze_limit ?? null;
  if (next === prev) return;
  error.value = "";
  try {
    await api.updateSource(s.id, { analyze_limit: next });
    await refresh();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
    el.value = prev != null ? String(prev) : "";
  }
}

function runStatusLabel(status: string) {
  if (status === "running") return "运行中";
  if (status === "ok" || status === "success") return "成功";
  if (status === "failed") return "失败";
  return status;
}

function runStatusClass(status: string) {
  if (status === "running") return "run-badge run-badge--running";
  if (status === "ok" || status === "success") return "run-badge run-badge--ok";
  if (status === "failed") return "run-badge run-badge--err";
  return "run-badge";
}
</script>

<template>
  <div class="settings-page">
    <h1>配置</h1>
    <p class="muted">定时任务（含飞书 Webhook）、订阅源与模型连接</p>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="message" class="muted">{{ message }}</p>

    <div class="layout">
      <nav class="card nav">
        <button type="button" class="nav-btn" :class="{ on: section === 'pipeline' }" @click="section = 'pipeline'">
          定时任务
        </button>
        <button type="button" class="nav-btn" :class="{ on: section === 'llm' }" @click="section = 'llm'">模型与密钥</button>
      </nav>

      <div class="content">
        <transition name="fade-slide" mode="out-in">
          <section v-if="section === 'pipeline'" key="pipeline" class="card stack">
            <div class="pipeline-intro-row">
              <div class="pipeline-intro-text">
                <h2>定时任务</h2>
                <p class="muted small row-sub">
                  左侧选择任务；启用状态用滑块切换。任务名称、Cron、飞书 Webhook、阈值与评分等在「新建任务 / 修改任务」表单中配置。
                </p>
              </div>
              <button type="button" class="btn btn-primary pipeline-new-btn" @click="openCreateJobModal">
                新建任务
              </button>
            </div>
            <p v-if="runMsg" class="muted small pipeline-run-msg">{{ runMsg }}</p>

            <div class="job-shell">
              <aside class="job-aside card flat">
                <p class="aside-label">任务列表</p>
                <ul class="job-index">
                  <li v-for="j in jobs" :key="j.id">
                    <div class="job-li" :class="{ on: selectedJobId === j.id }">
                      <label class="toggle job-li-toggle" @click.stop>
                        <input
                          type="checkbox"
                          role="switch"
                          :aria-label="`${j.name} 启用调度`"
                          :checked="j.enabled"
                          @change="onJobEnabledInput(j, $event)"
                        />
                        <span class="toggle-track" aria-hidden="true" />
                      </label>
                      <button type="button" class="job-index-main" @click="selectedJobId = j.id">
                        <span class="job-index-head">
                          <span class="job-index-name">{{ j.name }}</span>
                        </span>
                        <span class="job-index-cron">{{ j.schedule_cron }}</span>
                      </button>
                    </div>
                  </li>
                </ul>
                <p v-if="!jobs.length" class="muted small aside-empty">暂无定时任务，请点击上方「新建任务」。</p>
              </aside>

              <div class="job-editor">
                <template v-if="selectedJob">
                  <div class="job-summary card flat">
                    <div class="summary-head">
                      <h3 class="summary-title">{{ selectedJob.name }}</h3>
                      <div class="summary-actions">
                        <button
                          type="button"
                          class="btn btn-secondary btn-summary-compact"
                          :disabled="jobRunning"
                          @click="runCurrentJob"
                        >
                          {{ jobRunning ? "运行中…" : "运行当前任务" }}
                        </button>
                        <button type="button" class="btn btn-primary btn-summary-compact" @click="openEditJobModal">
                          修改任务
                        </button>
                        <button
                          type="button"
                          class="btn btn-secondary btn-danger-soft btn-summary-compact"
                          :disabled="jobRunning"
                          @click="removeJob"
                        >
                          删除任务
                        </button>
                      </div>
                    </div>
                    <dl class="summary-dl">
                      <div class="summary-row">
                        <dt>Cron</dt>
                        <dd>
                          <code class="cron-code">{{ selectedJob.schedule_cron }}</code>
                        </dd>
                      </div>
                      <div class="summary-row">
                        <dt>精选阈值</dt>
                        <dd>≥ {{ selectedJob.score_threshold }} / 10</dd>
                      </div>
                      <div v-if="selectedJob.feishu_webhook_url?.trim()" class="summary-row">
                        <dt>飞书 Webhook</dt>
                        <dd class="webhook-dd">{{ selectedJob.feishu_webhook_url }}</dd>
                      </div>
                      <div class="summary-row summary-row--compact">
                        <dt title="任务跑完后是否推送当日 Digest 到飞书">Digest 推送</dt>
                        <dd>{{ selectedJob.push_digest ? "是" : "否" }}</dd>
                      </div>
                    </dl>
                  </div>

                  <div class="sources-block">
                    <div class="sources-head-row">
                      <div class="sources-head-text">
                        <h3 class="sources-heading">订阅源（本任务）</h3>
                        <p class="muted small sources-sub">
                          「每源最多分析」为本轮从该源取用的未分析条数上限；留空则只受任务级「每轮最多分析」约束。
                        </p>
                      </div>
                      <button type="button" class="btn btn-secondary sources-add-btn" @click="openSourceDialog">
                        添加
                      </button>
                    </div>
                    <table v-if="sources.length" class="src-table">
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>名称</th>
                          <th>类型</th>
                          <th>每源最多分析</th>
                          <th>启用</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="s in sources" :key="s.id">
                          <td>{{ s.id }}</td>
                          <td>{{ s.name }}</td>
                          <td>{{ s.type }}</td>
                          <td>
                            <input
                              type="number"
                              class="input src-cap-input"
                              min="1"
                              max="50000"
                              placeholder="继承任务"
                              :value="s.analyze_limit ?? ''"
                              :disabled="jobRunning"
                              @change="onSourceAnalyzeLimitChange(s, $event)"
                            />
                          </td>
                          <td>
                            <label class="toggle toggle-inline" @click.stop>
                              <input
                                type="checkbox"
                                role="switch"
                                :aria-label="`${s.name} 启用订阅`"
                                :checked="s.enabled"
                                @change="onSourceEnabledInput(s, $event)"
                              />
                              <span class="toggle-track" aria-hidden="true" />
                            </label>
                          </td>
                          <td class="src-delete-cell">
                            <button
                              type="button"
                              class="btn-src-delete"
                              title="删除订阅源"
                              @click="removeSource(s.id)"
                            >
                              删除
                            </button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                    <p v-else class="muted">暂无订阅源</p>
                  </div>

                  <div class="runs-block card flat">
                    <h3 class="runs-block-title">运行日志（本任务）</h3>
                    <p class="muted small runs-time-hint">
                      数据库存储与以下为<strong>东八区（UTC+8）</strong>时间。
                    </p>
                    <table v-if="jobRuns.length" class="src-table runs-table">
                      <colgroup>
                        <col class="runs-col-time" />
                        <col class="runs-col-status" />
                        <col class="runs-col-trigger" />
                        <col class="runs-col-preview" />
                      </colgroup>
                      <thead>
                        <tr>
                          <th class="runs-th-time">开始时间</th>
                          <th>状态</th>
                          <th>触发</th>
                          <th class="runs-th-preview">摘要 <span class="runs-col-hint">悬停查看全文</span></th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="r in jobRuns" :key="r.id">
                          <td class="nowrap">{{ r.started_at }}</td>
                          <td>
                            <span :class="runStatusClass(r.status)">{{ runStatusLabel(r.status) }}</span>
                          </td>
                          <td class="runs-trigger-cell">{{ r.trigger }}</td>
                          <td class="run-preview-cell">
                            <span v-if="r.error" class="run-preview-ellip run-err" :title="r.error">{{ r.error }}</span>
                            <span v-else-if="r.preview" class="run-preview-ellip" :title="r.preview">{{ r.preview }}</span>
                            <span v-else class="muted">—</span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                    <p v-else class="muted">暂无运行记录；点击「运行当前任务」后将在此显示。</p>
                  </div>
                </template>
                <p v-else-if="jobs.length" class="muted padded-hint">请选择左侧一条任务。</p>
                <p v-else class="muted padded-hint">请先点击「新建任务」创建定时任务。</p>
              </div>
            </div>
          </section>

          <section v-else-if="section === 'llm'" key="llm" class="card stack">
            <h2>模型与密钥</h2>
            <p class="muted small llm-intro">
              此处配置<strong>调用哪家模型、API Key、温度与长度</strong>等连接参数。「写什么、如何打分」请在<strong>定时任务</strong>中按任务设置；
              <strong>默认精选阈值</strong>亦可被任务侧覆盖。
              下方「兜底提示词」仅在任务未填写自己的模板时使用。
            </p>
            <div v-for="p in profiles" :key="p.id" class="prof-block">
              <p>
                <strong>{{ p.name }}</strong>
                <span v-if="p.is_default" class="tag">默认</span>
              </p>
              <template v-if="profileDraft[p.id]">
                <div class="form-grid">
                  <div>
                    <label class="label">模型 model</label>
                    <input v-model="profileDraft[p.id].model" class="input" placeholder="例如 gpt-4o-mini" />
                  </div>
                  <div>
                    <label class="label">temperature</label>
                    <input v-model.number="profileDraft[p.id].temperature" type="number" step="0.1" class="input" />
                  </div>
                  <div>
                    <label class="label">max_tokens</label>
                    <input v-model.number="profileDraft[p.id].max_tokens" type="number" class="input" />
                  </div>
                  <div>
                    <label class="label">默认精选阈值（1–10）</label>
                    <input v-model.number="profileDraft[p.id].score_threshold" type="number" class="input" min="1" max="10" />
                  </div>
                  <div class="full">
                    <label class="label">分类提示（每行一个）</label>
                    <p class="muted small field-hint">示例：<code>人工智能</code>、<code>产品发布</code> —— 帮助模型归类。</p>
                    <textarea v-model="profileDraft[p.id].category_hints_text" class="textarea" rows="3" />
                  </div>
                  <details class="adv-details">
                    <summary>高级：全局兜底提示词（可选）</summary>
                    <p class="muted small">
                      多数用户只需在定时任务里配置提示词；这里用于「任务留空时」的退路。
                    </p>
                    <div class="full">
                      <label class="label">prompt_template</label>
                      <textarea v-model="profileDraft[p.id].prompt_template" class="textarea" rows="8" />
                    </div>
                    <div class="full">
                      <label class="label">system_prompt</label>
                      <textarea v-model="profileDraft[p.id].system_prompt" class="textarea" rows="3" />
                    </div>
                  </details>
                  <div class="full">
                    <input v-model="profileKey[p.id]" class="input" type="password" placeholder="更新 API Key（可选）" />
                  </div>
                  <div class="full">
                    <button type="button" class="btn" @click="saveProfile(p)">保存 Profile</button>
                  </div>
                </div>
              </template>
            </div>
          </section>
        </transition>
      </div>
    </div>

    <dialog ref="jobFormDialog" class="dlg dlg-job ui-motion">
      <div class="dlg-inner dlg-job-inner">
        <h3>{{ jobFormMode === "create" ? "新建定时任务" : "修改定时任务" }}</h3>

        <label class="label">任务名称</label>
        <input v-model="jobModal.name" class="input" placeholder="例如：早间科技精选" />

        <div class="modal-field-row">
          <span class="label tight-label">启用调度</span>
          <label class="toggle toggle-inline">
            <input v-model="jobModal.enabled" type="checkbox" role="switch" />
            <span class="toggle-track" aria-hidden="true" />
          </label>
        </div>

        <label class="label">Cron（五段：分 时 日 月 周）</label>
        <input v-model="jobModal.schedule_cron" class="input" placeholder="每日 8:00 → 0 8 * * *" />

        <label class="label">飞书 Webhook URL</label>
        <input
          v-model="jobModal.feishu_webhook_url"
          class="input"
          type="url"
          autocomplete="off"
          :placeholder="
            jobFormMode === 'create'
              ? 'https://open.feishu.cn/open-apis/bot/v2/hook/...'
              : ''
          "
        />

        <div class="modal-field-row modal-field-row-tight">
          <label class="label tight-label">精选阈值（1–10）</label>
          <input v-model.number="jobModal.score_threshold" type="number" min="1" max="10" class="input thr-input" />
        </div>
        <p class="muted small thr-hint">模型输出分数 ≥ 此值的条目视为精选并优先进入 Digest。</p>

        <label class="label">评分侧重点</label>
        <div class="select-wrap">
          <select class="select" :value="rubricPresetId" @change="onRubricPresetSelect($event)">
            <option v-for="p in RUBRIC_PRESETS" :key="p.id" :value="p.id">{{ p.label }}</option>
            <option value="custom">完全自定义</option>
          </select>
        </div>
        <p class="muted small field-hint">{{ rubricHint }}</p>
        <label class="label subtle-top">评分说明（写入提示词，可编辑）</label>
        <textarea v-model="jobModal.scoring_rubric" class="textarea" rows="8" />

        <details class="adv-details modal-details">
          <summary>抓取与 Digest（可选）</summary>
          <label class="label">每轮最多分析条数（0=不限制）</label>
          <input v-model.number="jobModal.analyze_limit" type="number" class="input" min="0" />
          <label class="label">Digest Top N</label>
          <input v-model.number="jobModal.digest_top_n" type="number" class="input" min="1" />
          <label class="chk-inline">
            <input v-model="jobModal.push_digest" type="checkbox" /> 运行结束后推送 Digest 到上述飞书 Webhook
          </label>
        </details>

        <details class="adv-details modal-details">
          <summary>关键词与预过滤（可选）</summary>
          <p class="muted small">
            开启「预过滤」后：系统会先检查标题和摘要里是否出现你在下方配置的关键词。<strong>没有任何关键词命中时，不会调用大模型</strong>（直接跳过），适合只想精读某一主题、同时节省模型费用的场景。
            若关闭预过滤，关键词仍会写入提示词作为参考，但所有抓取到的条目都会参与分析。
          </p>
          <label class="chk-inline">
            <input v-model="jobModal.keyword_prefilter" type="checkbox" /> 启用关键词预过滤（未命中则跳过分析）
          </label>
          <label class="label">关注关键词（每行一个）</label>
          <textarea v-model="jobModal.keywordsText" class="textarea" rows="4" placeholder="示例：大模型（每行一条）" />
        </details>

        <details class="adv-details modal-details">
          <summary>模型 Profile（可选）</summary>
          <div class="select-wrap">
            <select v-model="jobModal.llm_profile_id" class="select">
              <option value="">默认 Profile</option>
              <option v-for="p in profiles" :key="p.id" :value="String(p.id)">{{ p.name }}</option>
            </select>
          </div>
        </details>

        <details class="adv-details modal-details">
          <summary>高级提示词（可选）</summary>
          <label class="label">分析提示词模板</label>
          <textarea v-model="jobModal.prompt_template" class="textarea" rows="5" placeholder="留空则使用「模型与密钥」全局兜底" />
          <label class="label">系统提示</label>
          <textarea v-model="jobModal.system_prompt" class="textarea" rows="3" placeholder="可选；约束输出格式等" />
        </details>

        <div class="dlg-actions">
          <button type="button" class="btn btn-primary" @click="submitJobModal">
            {{ jobFormMode === "create" ? "创建" : "保存" }}
          </button>
          <button type="button" class="btn btn-secondary" @click="jobFormDialog?.close()">取消</button>
        </div>
      </div>
    </dialog>

    <dialog ref="sourceDialog" class="dlg ui-motion">
      <div class="dlg-inner">
        <h3>添加订阅源</h3>
        <input v-model="newSource.name" class="input" placeholder="名称" />
        <select v-model="newSource.type" class="select">
          <option value="rss">rss</option>
          <option value="json_feed">json_feed</option>
          <option value="html_list">html_list</option>
          <option value="browser_session">browser_session</option>
        </select>
        <input v-model="newSource.url" class="input" placeholder="URL" />
        <label class="label">每源最多分析（可选）</label>
        <input
          v-model.number="newSource.analyze_limit"
          type="number"
          class="input"
          min="1"
          max="50000"
          placeholder="留空则仅受任务级上限约束"
        />
        <textarea v-model="newSource.config_json" class="textarea" placeholder="config_json" />
        <p v-if="testMsg" class="muted small">{{ testMsg }}</p>
        <div class="dlg-actions">
          <button type="button" class="btn btn-secondary" @click="testNewSource">测试抓取</button>
          <button type="button" class="btn" @click="addSource">添加</button>
          <button type="button" class="btn btn-secondary" @click="sourceDialog?.close()">取消</button>
        </div>
      </div>
    </dialog>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 1200px;
}
.layout {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 20px;
  margin-top: 24px;
  align-items: start;
}
@media (max-width: 768px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
.nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
}
.nav-btn {
  text-align: left;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  font-size: 0.95rem;
}
.nav-btn.on {
  border-color: var(--border);
  background: var(--surface);
}
.stack {
  padding: 24px;
}
.row-title {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}
.row-sub {
  margin: 6px 0 0;
  max-width: 560px;
  line-height: 1.45;
}
.pipeline-intro-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 4px;
}
.pipeline-intro-text {
  flex: 1;
  min-width: 0;
}
.pipeline-intro-text h2 {
  margin: 0 0 4px;
}
.pipeline-new-btn {
  flex-shrink: 0;
  align-self: flex-start;
}
.pipeline-run-msg {
  margin: 6px 0 18px;
}
.btns {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.job-shell {
  display: grid;
  grid-template-columns: minmax(232px, 280px) 1fr;
  gap: 20px;
  align-items: start;
}
@media (max-width: 900px) {
  .job-shell {
    grid-template-columns: 1fr;
  }
}
.job-aside.flat {
  padding: 16px 14px;
  background: linear-gradient(180deg, var(--surface) 0%, var(--bg) 72%);
}
.aside-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-secondary);
  margin: 0 0 10px;
}
.job-index {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: min(52vh, 420px);
  overflow-y: auto;
}
.job-li {
  display: flex;
  align-items: stretch;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--bg);
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}
.job-li.on {
  border-color: #6366f1;
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.22);
  background: linear-gradient(145deg, #f5f3ff 0%, var(--bg) 55%);
}
.job-li-toggle {
  flex-shrink: 0;
  align-self: center;
}
.job-index-main {
  flex: 1;
  min-width: 0;
  text-align: left;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.job-index-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.job-index-name {
  font-weight: 600;
  font-size: 0.92rem;
}
.job-index-cron {
  font-family: ui-monospace, monospace;
  font-size: 0.78rem;
  color: var(--text-secondary);
}
.toggle {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
}
.toggle input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}
.toggle-track {
  display: block;
  width: 44px;
  height: 26px;
  background: var(--border);
  border-radius: 999px;
  transition: background 0.2s ease;
  position: relative;
}
.toggle-track::after {
  content: "";
  position: absolute;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #fff;
  top: 2px;
  left: 2px;
  transition: transform 0.2s var(--ease-page, cubic-bezier(0.22, 1, 0.36, 1));
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.18);
}
.toggle input:checked + .toggle-track {
  background: #6366f1;
}
.toggle input:checked + .toggle-track::after {
  transform: translateX(18px);
}
.toggle-inline {
  flex-shrink: 0;
}
.btn-block {
  width: 100%;
}
.aside-empty {
  margin: 10px 0 0;
}
.job-summary {
  margin-bottom: 24px;
  padding: 18px 20px;
}
.summary-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}
.summary-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
  align-items: center;
}
.summary-actions .btn-summary-compact {
  font-size: 0.9rem;
  line-height: 1.35;
  padding: 5px 12px;
  min-height: 0;
  border-radius: 8px;
  font-weight: 500;
}
.btn-danger-soft {
  border-color: #fca5a5;
  color: #991b1b;
  background: linear-gradient(180deg, #fef2f2 0%, #fee2e2 100%);
}
.btn-danger-soft:hover {
  border-color: #f87171;
  background: #fecaca;
}
.summary-title {
  margin: 0;
  font-size: 1.1rem;
}
.summary-dl {
  margin: 0;
  display: grid;
  gap: 10px;
}
.summary-row {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 12px;
  font-size: 0.9rem;
  align-items: baseline;
}
@media (max-width: 500px) {
  .summary-row {
    grid-template-columns: 1fr;
  }
}
.summary-row dt {
  margin: 0;
  color: var(--text-secondary);
  font-weight: 500;
}
.summary-row dd {
  margin: 0;
}
.webhook-dd {
  word-break: break-all;
  overflow-wrap: anywhere;
}
.cron-code {
  font-family: ui-monospace, monospace;
  font-size: 0.85rem;
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--surface);
}
.padded-hint {
  padding: 24px 8px;
}
.field-hint {
  margin: 0 0 8px;
  line-height: 1.45;
}
.field-hint code {
  font-size: 0.82em;
  padding: 1px 6px;
  border-radius: 6px;
  background: var(--surface);
}
.subtle-top {
  margin-top: 12px;
}
.llm-intro {
  margin-bottom: 20px;
  line-height: 1.55;
  max-width: 720px;
}
.adv-details {
  grid-column: 1 / -1;
  border: 1px dashed var(--border);
  border-radius: 10px;
  padding: 12px 16px;
  background: var(--surface);
}
.adv-details summary {
  cursor: pointer;
  font-weight: 500;
}
.modal-details {
  width: 100%;
  margin-bottom: 12px;
}
.modal-details .label {
  margin-top: 10px;
}
.modal-details .label:first-child {
  margin-top: 4px;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.form-grid .full {
  grid-column: 1 / -1;
}
.chk-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  font-size: 0.9rem;
  cursor: pointer;
}
.sources-block {
  margin-top: 8px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
}
.runs-block {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
}
.runs-block.flat {
  padding: 18px 20px;
}
.sources-sub {
  margin: 6px 0 0;
  max-width: 560px;
  line-height: 1.45;
}
.sources-head-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}
.sources-head-text {
  flex: 1;
  min-width: 0;
}
.sources-heading {
  margin: 0 0 4px;
  font-size: 1.05rem;
}
.sources-add-btn {
  flex-shrink: 0;
  margin-top: 2px;
}
.btn-src-delete {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 10px;
  font-size: 0.82rem;
  font-weight: 500;
  font-family: inherit;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #dc2626;
  cursor: pointer;
  transition: box-shadow 0.18s ease, color 0.15s ease;
}
.btn-src-delete:hover {
  box-shadow: 0 2px 10px rgba(220, 38, 38, 0.22);
  color: #b91c1c;
}
.btn-src-delete:focus-visible {
  outline: 2px solid rgba(220, 38, 38, 0.35);
  outline-offset: 2px;
}
.src-delete-cell {
  vertical-align: middle;
}
.summary-row--compact dt {
  white-space: nowrap;
}
.nowrap {
  white-space: nowrap;
}
.src-cap-input {
  max-width: 120px;
}
.runs-block-title {
  margin: 0 0 6px;
  font-size: 1.05rem;
}
.runs-time-hint {
  margin: 0 0 14px;
  max-width: 720px;
  line-height: 1.45;
}
.run-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}
.run-badge--running {
  background: #eef2ff;
  color: #3730a3;
}
.run-badge--ok {
  background: #dcfce7;
  color: #166534;
}
.run-badge--err {
  background: #fee2e2;
  color: #991b1b;
}
.runs-table {
  table-layout: fixed;
  width: 100%;
}
.runs-table th,
.runs-table td {
  vertical-align: middle;
}
.runs-col-time {
  width: 15rem;
}
.runs-th-time {
  white-space: nowrap;
}
.runs-col-status {
  width: 4.75rem;
}
.runs-col-trigger {
  width: 6.75rem;
}
.runs-col-preview {
  width: auto;
  min-width: 8rem;
}
.runs-col-hint {
  margin-left: 6px;
  font-weight: 400;
  font-size: 0.72rem;
  color: var(--text-secondary);
}
.runs-th-preview {
  white-space: normal;
  line-height: 1.35;
}
.runs-trigger-cell {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.88rem;
}
.run-preview-cell {
  min-width: 0;
  font-size: 0.82rem;
  line-height: 1.4;
}
.run-preview-ellip {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: help;
}
.run-err {
  color: #b91c1c;
}
.src-table {
  margin-top: 12px;
}
.prof-block {
  padding: 16px 0;
  border-bottom: 1px solid var(--border);
}
.small {
  font-size: 0.85rem;
}
.req {
  margin-left: 8px;
  font-size: 0.75rem;
  color: #b91c1c;
  font-weight: 600;
}
.modal-field-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 12px;
}
.modal-field-row-tight {
  margin-top: 16px;
}
.tight-label {
  margin: 0;
}
.thr-input {
  max-width: 96px;
  flex-shrink: 0;
}
.thr-hint {
  margin: 6px 0 0;
}
.modal-field-row .thr-input {
  margin: 0;
}
.dlg {
  border: none;
  border-radius: var(--radius-card);
  padding: 0;
  max-width: 480px;
  width: calc(100vw - 32px);
}
.dlg-job {
  max-width: 560px;
}
.dlg::backdrop {
  background: rgba(0, 0, 0, 0.35);
}
.dlg-inner {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.dlg-job-inner {
  max-height: min(90vh, 720px);
  overflow-y: auto;
}
.dlg-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}
</style>
