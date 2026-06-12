# Context Summary

## Loaded sources

| File | Summary |
|---|---|
| Project structure | Monorepo: Python backend (FastAPI+SQLite+APScheduler) + Vue 3 frontend (Vite+TypeScript) |
| `services/web/frontend/src/views/SettingsView.vue` | Main config page: 2 sections (pipeline jobs, LLM profiles). Job form has 10+ fields across 4 collapsible sections |
| `services/web/frontend/src/api/client.ts` | TypeScript API client with PipelineJob interface covering all DB fields |
| `services/backend/api/ddo_pulse_api/api_routes.py` | FastAPI routes: CRUD for pipeline_jobs, sources, profiles, articles, digests, dashboard |
| `services/backend/api/ddo_pulse_api/schemas.py` | Pydantic schemas for PipelineJobCreate/Update with all fields |
| `services/backend/db/schema.sql` | 8 tables: llm_profiles, pipeline_jobs, sources, raw_items, analyzed_items, digests, push_logs, app_settings |
| `services/backend/db/ddo_pulse_db/repository.py` | SQLite repository with full CRUD for all entities |
| `services/backend/core/ddo_pulse_core/pipeline.py` | Pipeline orchestration: fetch→analyze→digest→push, profile merging logic |
| `services/backend/core/ddo_pulse_core/analyzer/prompt.py` | Default prompt template, paper analysis template, format_prompt_template() |
| `services/backend/core/ddo_pulse_core/analyzer/openrouter.py` | OpenRouter client, prompt building, JSON parsing with retries |
| `services/backend/api/ddo_pulse_api/scheduler.py` | APScheduler CronTrigger integration, reload on job changes |

## Context missing

- No AGENTS.md found
- No product.md found (docs/mvp.md exists but was not listed in defaults)
