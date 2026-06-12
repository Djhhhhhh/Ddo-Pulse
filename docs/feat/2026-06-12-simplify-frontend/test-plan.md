# Ddo-Pulse 前端简化 Test Plan

> 本文档把已确认的 `spec.md` 中的 AC + 关键 FR 拆为可勾选 checklist。
>
> Verification 阶段按下面两类语法判定：
>
> - `- [ ] cmd: <shell>` —— 机器执行，`exit code == 0` 视为通过；输出 / 错误写入 `verification.log`。
> - `- [ ] human: <描述>` —— 人工核对勾选，由用户在终端确认。
>
> 每个 group 末尾的 **Pass criterion** 是该组的整体通过标准。
>
> 用户确认本 test-plan 后，方可进入 Tasking。

---

## G1. 模型与密钥简化（FR-LLM-1/2/3, AC-1）

> 对应 spec 3.1 节。

- [ ] cmd: grep -c "temperature" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue" | grep -q "^0$"
- [ ] cmd: grep -c "max_tokens" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue" | grep -q "^0$"
- [ ] cmd: grep -c "score_threshold" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue" | grep -q "^0$"
- [ ] cmd: grep -c "category_hints" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue" | grep -q "^0$"
- [ ] cmd: grep -q 'v-model.*profileDraft.*\.model' "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue"
- [ ] cmd: grep -q 'type="password"' "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue"
- [ ] human: LLM 配置页面仅显示 model 和 api_key 两个可编辑字段，无其他高级参数

**Pass criterion**：LLM Tab 仅保留 model + api_key 编辑，移除 temperature/max_tokens/score_threshold/category_hints

---

## G2. 阈值删除（FR-FORM-3, AC-2）

> 对应 spec 3.3.2 节。

- [ ] cmd: grep -c "score_threshold" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue" | grep -q "^0$"
- [ ] cmd: grep -c "精选阈值" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue" | grep -q "^0$"
- [ ] human: 定时任务创建/编辑表单中不出现「精选阈值」或「score_threshold」相关输入

**Pass criterion**：阈值字段从前端表单完全移除

---

## G3. 评分侧重点只读预览（FR-FORM-4/5/6, AC-3）

> 对应 spec 3.3.3 节。

- [ ] cmd: test -f "D:/work_area/ddo-pulse/services/web/frontend/src/components/ScoringRubricPreview.vue"
- [ ] cmd: grep -q "RUBRIC_PRESETS" "D:/work_area/ddo-pulse/services/web/frontend/src/components/ScoringRubricPreview.vue"
- [ ] cmd: grep -q "readonly\|disabled\|contenteditable.*false" "D:/work_area/ddo-pulse/services/web/frontend/src/components/ScoringRubricPreview.vue"
- [ ] human: 评分侧重点区域为只读预览，用户可切换查看 balanced/tech_depth/timely 三个模板但不能编辑内容
- [ ] human: 默认显示 balanced 模板

**Pass criterion**：评分侧重点为只读预览，支持模板切换，不可编辑

---

## G4. 抓取与 Digest 必填（FR-FORM-7/8/9, AC-4）

> 对应 spec 3.3.4 节。

- [ ] cmd: grep -q "抓取与 Digest" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue"
- [ ] cmd: grep -c "adv-details.*modal-details.*抓取" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue" | grep -q "^0$"
- [ ] cmd: grep -q "analyze_limit.*50\|analyze_limit.*=.*50" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue"
- [ ] cmd: grep -q "digest_top_n.*10\|digest_top_n.*=.*10" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue"
- [ ] human: 「抓取与 Digest」区域默认展开（不在折叠区内），字段有默认值（analyze_limit=50, digest_top_n=10, push_digest=true）

**Pass criterion**：抓取与 Digest 为必填区域，默认展开且有合理默认值

---

## G5. 模型 Profile 移除（FR-FORM-10, AC-5）

> 对应 spec 3.3.5 节。

- [ ] cmd: grep -c "模型 Profile" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue" | grep -q "^0$"
- [ ] cmd: grep -c "llm_profile_id" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue" | grep -q "^0$"
- [ ] human: 定时任务创建/编辑表单中不出现「模型 Profile」选择区域

**Pass criterion**：模型 Profile 选择从前端表单完全移除

---

## G6. 关键词与预过滤保留（FR-FORM-11/12）

> 对应 spec 3.3.6 节。

- [ ] cmd: grep -q "关键词与预过滤" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue"
- [ ] cmd: grep -q "keyword_prefilter" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue"
- [ ] cmd: grep -q "keywordsText" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue"
- [ ] human: 关键词与预过滤区域保留为可选折叠区，功能不变

**Pass criterion**：关键词与预过滤功能完整保留

---

## G7. 提示词模板选择与组合（FR-FORM-13/14/15/16/17, AC-6）

> 对应 spec 3.3.7 节。

- [ ] cmd: test -f "D:/work_area/ddo-pulse/services/web/frontend/src/components/PromptTemplateSelector.vue"
- [ ] cmd: grep -q "PROMPT_TEMPLATES\|promptTemplates" "D:/work_area/ddo-pulse/services/web/frontend/src/components/PromptTemplateSelector.vue"
- [ ] cmd: grep -q "user.*需求\|userPrompt\|user_prompt" "D:/work_area/ddo-pulse/services/web/frontend/src/components/PromptTemplateSelector.vue"
- [ ] cmd: grep -q "预览\|preview" "D:/work_area/ddo-pulse/services/web/frontend/src/components/PromptTemplateSelector.vue"
- [ ] human: 提示词区域提供系统模板下拉选择，选择后显示模板预览
- [ ] human: 有「用户需求描述」文本输入框
- [ ] human: 有最终组合提示词的预览区域（系统模板 + 用户需求）

**Pass criterion**：提示词配置支持模板选择、用户需求输入、最终预览

---

## G8. 定时任务运行约束（FR-RUN-1, AC-7）

> 对应 spec 3.4 节。

- [ ] cmd: grep -q "jobRunning" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue"
- [ ] cmd: grep -q ':disabled.*jobRunning' "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue"
- [ ] human: 运行按钮在任务运行期间为 disabled 状态

**Pass criterion**：定时任务同一时刻只运行一个实例

---

## G9. 多任务与其他保留功能（FR-JOB-1/2/3, FR-FORM-1/2, AC-8）

> 对应 spec 3.2 和 3.3.1 节。

- [ ] cmd: grep -q "新建任务" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue"
- [ ] cmd: grep -q "schedule_cron" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue"
- [ ] cmd: grep -q "feishu_webhook_url" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue"
- [ ] cmd: grep -q "jobFormDialog" "D:/work_area/ddo-pulse/services/web/frontend/src/views/SettingsView.vue"
- [ ] human: 可以创建多个定时任务，列表正常显示
- [ ] human: Cron 表达式和飞书 Webhook URL 字段正常保留

**Pass criterion**：多任务管理、cron、webhook 功能完整保留

---

## G10. 后端兼容性（NFR-1）

> 对应 spec 8 节。

- [ ] cmd: cd "D:/work_area/ddo-pulse" && python -c "from services.backend.api.ddo_pulse_api.schemas import PipelineJobCreate; print('ok')"
- [ ] cmd: grep -q "score_threshold" "D:/work_area/ddo-pulse/services/backend/api/ddo_pulse_api/schemas.py"
- [ ] cmd: grep -q "llm_profile_id" "D:/work_area/ddo-pulse/services/backend/api/ddo_pulse_api/schemas.py"
- [ ] human: 后端 schema 保持不变，前端不发送的字段使用后端默认值

**Pass criterion**：后端 API 向后兼容，无破坏性变更

---

## 最终验收

- [ ] human: 上述全部 group 均勾选完成。
- [ ] cmd: tail -n 1 verification.log | grep -q "ALL PASSED"

---

## 用户确认

- ✅ **同意**：本 test-plan 符合预期，可进入 **Tasking** 阶段。
- ❌ **修改**：请列出 group / 条目编号与意见。
