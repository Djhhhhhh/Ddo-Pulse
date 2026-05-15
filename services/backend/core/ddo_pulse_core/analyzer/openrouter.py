"""OpenRouter-backed article analyzer."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from ddo_pulse_core.analyzer.models import AnalysisOutput
from ddo_pulse_core.analyzer.prompt import (
    DEFAULT_PROMPT_TEMPLATE,
    DEFAULT_SCORING_RUBRIC,
    format_prompt_template,
)

logger = logging.getLogger(__name__)

_MAX_CONTENT_CHARS = 8000
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    return _HTML_TAG_RE.sub("", text)


def normalize_content(text: str, max_chars: int = _MAX_CONTENT_CHARS) -> str:
    cleaned = strip_html(text or "").strip()
    if len(cleaned) > max_chars:
        return cleaned[:max_chars]
    return cleaned


def _extract_json_payload(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", stripped, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    start = stripped.find("{")
    if start == -1:
        return stripped
    end = stripped.rfind("}")
    if end != -1 and end > start:
        return stripped[start : end + 1]
    # Truncated generation (no closing brace): salvage still needs the `{`..tail slice.
    return stripped[start:]


def _repair_json_text(payload: str) -> str:
    """Best-effort fixes for common LLM JSON mistakes."""
    text = payload.strip()
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)
    return text


def _read_json_string_value(payload: str, start_after_quote: int) -> tuple[str, int]:
    """
    Read a JSON string value starting at *start_after_quote* (index of first char inside quotes).
    Returns (decoded_value, index_one_past_closing_quote) or (decoded_up_to_end, len(payload))
    if the string was never closed (truncated generation).
    """
    i = start_after_quote
    out: list[str] = []
    while i < len(payload):
        c = payload[i]
        if c == "\\":
            if i + 1 >= len(payload):
                break
            esc = payload[i + 1]
            if esc == '"':
                out.append('"')
            elif esc == "\\":
                out.append("\\")
            elif esc == "/":
                out.append("/")
            elif esc == "b":
                out.append("\b")
            elif esc == "f":
                out.append("\f")
            elif esc == "n":
                out.append("\n")
            elif esc == "r":
                out.append("\r")
            elif esc == "t":
                out.append("\t")
            elif esc == "u" and i + 6 <= len(payload):
                hex_part = payload[i + 2 : i + 6]
                try:
                    out.append(chr(int(hex_part, 16)))
                except ValueError:
                    out.append(payload[i : i + 6])
                i += 6
                continue
            else:
                out.append(esc)
            i += 2
            continue
        if c == '"':
            return "".join(out), i + 1
        out.append(c)
        i += 1
    return "".join(out), len(payload)


def _salvage_analysis_json(text: str) -> AnalysisOutput | None:
    """Extract fields when JSON is truncated (common when max_tokens cuts mid-string)."""
    payload = _extract_json_payload(text)
    if not payload.strip().startswith("{"):
        return None

    m_q = re.search(r'"is_quality"\s*:\s*(true|false)', payload, re.I)
    if not m_q:
        return None
    is_quality = m_q.group(1).lower() == "true"

    m_s = re.search(r'"score"\s*:\s*(\d+)', payload)
    if not m_s:
        return None
    score = max(1, min(10, int(m_s.group(1))))

    categories: list[str] = []
    m_c = re.search(r'"categories"\s*:\s*(\[[\s\S]*?\])', payload)
    if m_c:
        raw_cat = m_c.group(1)
        try:
            parsed = json.loads(raw_cat)
            if isinstance(parsed, list):
                categories = [str(x) for x in parsed if str(x).strip()]
        except json.JSONDecodeError:
            categories = []

    m_sum = re.search(r'"summary_zh"\s*:\s*"', payload)
    if not m_sum:
        return None
    summary_zh, _ = _read_json_string_value(payload, m_sum.end())
    summary_zh = summary_zh.strip()
    if not summary_zh:
        return None

    reason = "模型 JSON 被截断，已从不完整输出中恢复字段。"
    m_r = re.search(r'"reason"\s*:\s*"', payload)
    if m_r:
        r_val, _ = _read_json_string_value(payload, m_r.end())
        if r_val.strip():
            reason = r_val.strip()

    try:
        return AnalysisOutput(
            is_quality=is_quality,
            score=score,
            categories=categories,
            summary_zh=summary_zh[:4000],
            reason=reason[:4000],
        )
    except ValidationError:
        return None


def parse_analysis_json(text: str) -> AnalysisOutput:
    payload = _extract_json_payload(text)
    data: dict[str, Any] | None = None
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        try:
            data = json.loads(_repair_json_text(payload))
        except json.JSONDecodeError:
            salvaged = _salvage_analysis_json(text)
            if salvaged:
                return salvaged
            raise
    try:
        return AnalysisOutput.model_validate(data)
    except ValidationError:
        salvaged = _salvage_analysis_json(text)
        if salvaged:
            return salvaged
        raise


_JSON_REPAIR_USER = (
    "你上一段回复不是合法 JSON（解析错误）。请仅输出一个 JSON 对象，不要 markdown。"
    "summary_zh 最多 80 个汉字，务必简短。字符串内双引号写成 \\\"。"
    "字段：is_quality, score, categories, summary_zh, reason。"
)

_JSON_EMPTY_RETRY_USER = (
    "上一轮流式输出为空或无效。请仅输出一个完整 JSON 对象，不要其他文字。"
    "summary_zh 最多 80 个汉字。字段：is_quality, score, categories, summary_zh, reason。"
)


class OpenRouterAnalyzer:
    def __init__(self, profile: dict[str, Any]) -> None:
        self.profile = profile
        api_key = (profile.get("api_key") or "").strip()
        if not api_key:
            raise ValueError("OpenRouter API key is not configured")
        base_url = profile.get("base_url") or "https://openrouter.ai/api/v1"
        self._client = OpenAI(base_url=base_url, api_key=api_key)

    def _build_prompt(self, title: str, content: str) -> str:
        hints = self.profile.get("category_hints") or "[]"
        if isinstance(hints, str):
            try:
                hint_list = json.loads(hints)
            except json.JSONDecodeError:
                hint_list = []
        else:
            hint_list = list(hints)
        categories_hint = "、".join(str(h) for h in hint_list) or "通用"

        raw_kw = self.profile.get("_job_interest_keywords")
        if isinstance(raw_kw, str):
            try:
                kw_list = json.loads(raw_kw)
            except json.JSONDecodeError:
                kw_list = []
        elif isinstance(raw_kw, list):
            kw_list = raw_kw
        else:
            kw_list = []
        interest_keywords = "、".join(str(x) for x in kw_list) or "（无特别限定）"

        rubric = (self.profile.get("_job_scoring_rubric") or "").strip()
        if not rubric:
            rubric = DEFAULT_SCORING_RUBRIC

        template = self.profile.get("prompt_template") or DEFAULT_PROMPT_TEMPLATE
        return format_prompt_template(
            template,
            title=title,
            content=normalize_content(content),
            categories_hint=categories_hint,
            interest_keywords=interest_keywords,
            scoring_rubric=rubric,
        )

    def analyze(self, title: str, content: str) -> AnalysisOutput:
        profile = self.profile
        prompt = self._build_prompt(title, content)
        extra_headers: dict[str, str] = {}
        if profile.get("site_url"):
            extra_headers["HTTP-Referer"] = str(profile["site_url"])
        app_title = profile.get("app_title") or "Ddo-Pulse"
        extra_headers["X-OpenRouter-Title"] = str(app_title)

        messages: list[dict[str, str]] = []
        sys_msg = (profile.get("system_prompt") or "").strip()
        if sys_msg:
            messages.append({"role": "system", "content": sys_msg})
        messages.append({"role": "user", "content": prompt})
        base_messages = list(messages)
        base_max = int(profile.get("max_tokens") or 2048)
        create_kwargs: dict[str, Any] = {
            "extra_headers": extra_headers or None,
            "model": str(profile["model"]),
            "messages": messages,
            "temperature": float(profile.get("temperature") or 0.3),
            "max_tokens": base_max,
        }

        last_error: Exception | None = None
        last_raw = ""
        for attempt in range(3):
            create_kwargs["max_tokens"] = min(max(base_max, 1536) * (attempt + 1), 8192)
            create_kwargs["messages"] = messages
            try:
                if attempt == 0:
                    try:
                        completion = self._client.chat.completions.create(
                            **create_kwargs,
                            response_format={"type": "json_object"},
                        )
                    except Exception:
                        completion = self._client.chat.completions.create(**create_kwargs)
                else:
                    completion = self._client.chat.completions.create(**create_kwargs)

                raw = completion.choices[0].message.content or ""
                last_raw = raw
                if not raw.strip():
                    raise ValueError("empty completion content")
                return parse_analysis_json(raw)
            except (json.JSONDecodeError, ValidationError, IndexError, TypeError, ValueError) as exc:
                last_error = exc
                preview = (last_raw or "")[:200].replace("\n", " ")
                logger.warning(
                    "Analysis parse failed (attempt %s): %s; raw_preview=%r",
                    attempt + 1,
                    exc,
                    preview,
                )
                if attempt >= 2:
                    break
                if not (last_raw or "").strip():
                    messages = list(base_messages)
                    messages.append({"role": "user", "content": _JSON_EMPTY_RETRY_USER})
                else:
                    messages = list(messages)
                    messages.append({"role": "assistant", "content": last_raw})
                    messages.append({"role": "user", "content": _JSON_REPAIR_USER})
            except Exception as exc:
                last_error = exc
                logger.warning("OpenRouter call failed (attempt %s): %s", attempt + 1, exc)
                if attempt >= 2:
                    raise
                # Same messages, higher max_tokens on next iteration.
        assert last_error is not None
        raise last_error
