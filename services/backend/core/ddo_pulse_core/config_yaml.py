"""Default config.yaml template and YAML helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ddo_pulse_db.paths import get_config_path

DEFAULT_CONFIG: dict[str, Any] = {
    "app": {
        "web_host": "127.0.0.1",
        "web_port": 8765,
        "log_level": "INFO",
        "db_path": "ddo_pulse.db",
        "fetch_schedule_cron": "0 8 * * *",
    },
    "browser": {"default_profile": "chrome"},
    "feishu": {"webhook_url": ""},
    "llm": {
        "default_profile": "default",
        "profiles": [
            {
                "name": "default",
                "provider": "openrouter",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": "",
                "model": "openai/gpt-4o-mini",
                "site_url": "http://127.0.0.1:8765",
                "app_title": "Ddo-Pulse",
                "temperature": 0.3,
                "max_tokens": 1024,
                "score_threshold": 7,
                "category_hints": ["AI", "工程", "产品", "安全"],
            }
        ],
    },
    "sources": [],
}


def write_default_config(path: Path | None = None) -> Path:
    target = path or get_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            DEFAULT_CONFIG,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
    return target


def load_config(path: Path | None = None) -> dict[str, Any]:
    target = path or get_config_path()
    if not target.exists():
        return {}
    with target.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def get_default_profile_template() -> dict[str, Any]:
    profiles = DEFAULT_CONFIG.get("llm", {}).get("profiles") or []
    return dict(profiles[0]) if profiles else {}


def export_config(path: Path | None = None, sources: list[dict[str, Any]] | None = None) -> Path:
    target = path or get_config_path()
    data = load_config(target) if target.exists() else dict(DEFAULT_CONFIG)
    if sources is not None:
        data["sources"] = sources
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
    return target
