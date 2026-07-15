# Task-02: 分析器双维度评分

## 关联验收点
- G2: 双维度评分 — 分析器模型
- G3: 双维度评分 — Prompt 模板

## 目标
让 LLM 分析输出 relevance 和 novelty 两个独立评分字段。

## 修改文件
- `services/backend/core/ddo_pulse_core/analyzer/models.py`
- `services/backend/core/ddo_pulse_core/analyzer/prompt.py`
- `services/backend/core/ddo_pulse_core/analyzer/runner.py`

## 具体改动

### models.py
AnalysisOutput 新增可选字段：
```python
relevance: int | None = Field(default=None, ge=0, le=10)
novelty: int | None = Field(default=None, ge=0, le=10)
```

### prompt.py
新增 `DUAL_SCORE_PROMPT_TEMPLATE`：
- 与 DEFAULT_PROMPT_TEMPLATE 结构一致
- 输出字段变为 `relevance` 和 `novelty`（替代 `score`）
- 附带 `DUAL_SCORE_SCORING_RUBRIC`

新增 `DUAL_SCORE_SCORING_RUBRIC`：
```
评分标准：
- relevance（相关性）：0-10 分，衡量文章与读者兴趣领域的匹配程度
- novelty（新颖度）：0-10 分，衡量文章内容的新鲜程度和创新性
- is_quality 为 true 表示 relevance >= 7 或 novelty >= 7
```

### runner.py
分析完成后：
1. 读取 job 配置的 `relevance_weight` 和 `novelty_weight`
2. 若 relevance 和 novelty 均非 None：`composite_score = relevance * rw + novelty * nw`
3. 若任一为 None：`composite_score = score`（fallback）
4. 将 relevance、novelty、composite_score 一并写入 analyzed_items

## 验证
运行 G2、G3 的 cmd 测试项。
