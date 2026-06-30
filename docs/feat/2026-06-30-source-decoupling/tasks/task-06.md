# Task-06: API 端点补全

## 目标
新增 job_sources 关联管理的 REST API 端点。

## 关联验收点
- G3: 信息源与定时任务解耦
- G4: Per-Source 关注点配置

## 变更文件
- `services/backend/api/ddo_pulse_api/api_routes.py`

## 具体变更

### 新增端点

1. **`GET /api/pipeline-jobs/{job_id}/sources`**
   - 返回该 job 关联的所有 sources 及其 focus_config_json
   - 响应：`[{ source_id, name, type, url, enabled, focus_config_json }]`

2. **`POST /api/pipeline-jobs/{job_id}/sources`**
   - 关联一个 source 到 job
   - 请求体：`{ source_id, focus_config_json?, enabled? }`
   - 验证 source_id 和 job_id 存在
   - 响应：关联记录

3. **`PATCH /api/pipeline-jobs/{job_id}/sources/{source_id}`**
   - 更新关注点配置
   - 请求体：`{ focus_config_json?, enabled? }`
   - 响应：更新后的记录

4. **`DELETE /api/pipeline-jobs/{job_id}/sources/{source_id}`**
   - 取消关联（不删除 source 本身）
   - 响应：204 No Content

## 验收
- 所有端点返回正确的 HTTP 状态码
- 关联/取消关联不影响 source 和 pipeline_job 本身
