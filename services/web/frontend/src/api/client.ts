import { loadAppConfig } from "../config";

async function apiBase(): Promise<string> {
  const cfg = await loadAppConfig();
  const base = cfg.api_base || "/api";
  return base.endsWith("/") ? base.slice(0, -1) : base;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const base = await apiBase();
  const res = await fetch(`${base}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export interface Dashboard {
  sources_count: number;
  enabled_sources_count: number;
  raw_items_count: number;
  analyzed_count: number;
  read_count: number;
  quality_count: number;
  pending_analyze: number;
  digest_job_id: number | null;
  digest_date: string | null;
  digest_items_count: number;
  digest_preview: string | null;
  last_job_status: string | null;
  last_job_started_at: string | null;
}

export interface DigestToday {
  date: string;
  job_id: number | null;
  markdown_body: string;
  item_ids: number[];
}

export interface JobRun {
  id: number;
  started_at: string;
  finished_at: string | null;
  status: string;
  error: string | null;
  pipeline_job_id: number | null;
  pipeline_job_name: string | null;
  trigger: string;
  digest_id: number | null;
  preview: string | null;
}

export interface JobRunDetail extends JobRun {
  result_json: string | null;
  markdown_body: string | null;
}

export interface Article {
  id: number;
  title: string;
  url: string;
  score: number | null;
  is_quality: boolean;
  categories: string[];
  summary_zh: string | null;
  reason: string | null;
  analyzed_at: string;
  source_id: number;
  published_at: string | null;
  is_pushed: boolean;
  is_read: boolean;
}

export interface ArticleList {
  items: Article[];
  total: number;
  limit: number;
  offset: number;
}

export interface Source {
  id: number;
  job_id: number;
  name: string;
  type: string;
  url: string;
  config_json: string;
  enabled: boolean;
  /** 每轮从该订阅源最多分析的未处理条数；未设置则仅受任务级上限约束 */
  analyze_limit?: number | null;
}

export interface Profile {
  id: number;
  name: string;
  model: string;
  is_default: boolean;
  score_threshold: number;
  api_key_set: boolean;
  temperature: number;
  max_tokens: number;
  prompt_template: string | null;
  system_prompt: string | null;
  category_hints: string[];
}

export interface Settings {
  feishu_webhook_set: boolean;
  feishu_webhook_masked: string;
}

export interface RssSeedItem {
  category: string;
  name: string;
  type: string;
  url: string;
  site: string;
  freq: string;
  desc: string;
  priority: string;
}

export interface PipelineJob {
  id: number;
  name: string;
  enabled: boolean;
  schedule_cron: string;
  analyze_limit: number;
  digest_top_n: number;
  push_digest: boolean;
  score_threshold: number;
  interest_keywords: string[];
  keyword_prefilter: boolean;
  feishu_webhook_url: string;
  prompt_template: string | null;
  scoring_rubric: string | null;
  system_prompt: string | null;
  llm_profile_id: number | null;
}

export const api = {
  dashboard: (digestJobId?: number) => {
    const q = digestJobId != null ? `?digest_job_id=${digestJobId}` : "";
    return request<Dashboard>(`/dashboard${q}`);
  },
  digestToday: (jobId?: number) => {
    const q = jobId != null ? `?job_id=${jobId}` : "";
    return request<DigestToday>(`/digests/today${q}`);
  },
  jobRuns: (limit = 40, jobId?: number) => {
    const p = new URLSearchParams({ limit: String(limit) });
    if (jobId != null) p.set("job_id", String(jobId));
    return request<JobRun[]>(`/job-runs?${p}`);
  },
  jobRun: (id: number) => request<JobRunDetail>(`/job-runs/${id}`),
  articles: (params: URLSearchParams) =>
    request<ArticleList>(`/articles?${params}`),
  articleCategories: (days = 365) =>
    request<{ categories: string[] }>(`/articles/categories?days=${days}`),
  article: (id: number) => request<Article>(`/articles/${id}`),
  markArticleRead: (id: number) =>
    request<void>(`/articles/${id}/read`, { method: "POST" }),
  markArticleUnread: (id: number) =>
    request<void>(`/articles/${id}/read`, { method: "DELETE" }),
  sources: (jobId?: number) => {
    const q = jobId != null ? `?job_id=${jobId}` : "";
    return request<Source[]>(`/sources${q}`);
  },
  testSourceFetch: (body: object) =>
    request<{ count: number; sample: { title: string; url: string }[] }>(
      "/sources/test-fetch",
      { method: "POST", body: JSON.stringify(body) }
    ),
  createSource: (body: object) =>
    request<Source>("/sources", { method: "POST", body: JSON.stringify(body) }),
  updateSource: (id: number, body: object) =>
    request<Source>(`/sources/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  deleteSource: (id: number) =>
    request<void>(`/sources/${id}`, { method: "DELETE" }),
  profiles: () => request<Profile[]>("/profiles"),
  updateProfile: (id: number, body: object) =>
    request<Profile>(`/profiles/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  settings: () => request<Settings>("/settings"),
  updateSettings: (body: object) =>
    request<Settings>("/settings", {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  pipelineJobs: () => request<PipelineJob[]>("/pipeline-jobs"),
  createPipelineJob: (body: object) =>
    request<PipelineJob>("/pipeline-jobs", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updatePipelineJob: (id: number, body: object) =>
    request<PipelineJob>(`/pipeline-jobs/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  deletePipelineJob: (id: number) =>
    request<void>(`/pipeline-jobs/${id}`, { method: "DELETE" }),
  runPipelineJob: (
    id: number,
    params: {
      skip_analyze?: boolean;
      skip_digest?: boolean;
      skip_push?: boolean;
      force_push?: boolean;
      analyze_limit?: number;
    }
  ) => {
    const p = new URLSearchParams();
    if (params.skip_analyze) p.set("skip_analyze", "true");
    if (params.skip_digest) p.set("skip_digest", "true");
    if (params.skip_push != null) p.set("skip_push", params.skip_push ? "true" : "false");
    if (params.force_push != null) p.set("force_push", params.force_push ? "true" : "false");
    if (params.analyze_limit != null) p.set("analyze_limit", String(params.analyze_limit));
    return request<{ ok: boolean; stats: Record<string, unknown> }>(
      `/pipeline-jobs/${id}/run?${p}`,
      { method: "POST" }
    );
  },
  reloadScheduler: () =>
    request<void>("/pipeline-jobs/reload-scheduler", { method: "POST" }),
  rssLibrary: () =>
    request<{ items: RssSeedItem[] }>("/rss-library"),
  rssLibraryReload: () =>
    request<{ count: number }>("/rss-library/reload", { method: "POST" }),
  runOnce: (body: object) =>
    request<{ ok: boolean; stats: Record<string, unknown> }>("/jobs/run-once", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
