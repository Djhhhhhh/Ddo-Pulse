"""Web frontend configuration in ~/.ddo_pulse/web.yaml."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from ddo_pulse_db.paths import ensure_data_dir, get_web_config_path

VITE_ENV_FILENAME = ".ddo-pulse.env.json"


def _repo_frontend_dir() -> Path:
    # services/backend/core/ddo_pulse_core/web_config.py -> repo root
    return Path(__file__).resolve().parents[4] / "services" / "web" / "frontend"


def get_vite_env_path() -> Path:
    return _repo_frontend_dir() / VITE_ENV_FILENAME


DEFAULT_WEB_CONFIG: dict[str, Any] = {
    "api": {
        "host": "127.0.0.1",
        "port": 8765,
    },
    "dev_server": {
        "port": 5173,
        "api_proxy": "http://127.0.0.1:8765",
    },
    "app": {
        "title": "Ddo-Pulse",
        "api_base": "/api",
    },
}


def load_web_config(path: Path | None = None) -> dict[str, Any]:
    target = path or get_web_config_path()
    if not target.exists():
        return dict(DEFAULT_WEB_CONFIG)
    with target.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return dict(DEFAULT_WEB_CONFIG)
    return _merge_defaults(data)


def _merge_defaults(data: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(DEFAULT_WEB_CONFIG))
    for key, value in data.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    api = merged.get("api") or {}
    dev = merged.get("dev_server") or {}
    host = api.get("host", "127.0.0.1")
    port = api.get("port", 8765)
    if not dev.get("api_proxy"):
        dev["api_proxy"] = f"http://{host}:{port}"
    merged["dev_server"] = dev
    return merged


def write_default_web_config(path: Path | None = None, *, force: bool = False) -> Path:
    target = path or get_web_config_path()
    ensure_data_dir()
    if target.exists() and not force:
        return target
    with target.open("w", encoding="utf-8") as f:
        f.write(
            "# Ddo-Pulse Web 配置（可手工编辑）\n"
            "# 修改后执行: ddo-pulse web sync  或重启 start-dev 脚本\n\n"
        )
        yaml.safe_dump(
            DEFAULT_WEB_CONFIG,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
    return target


def api_public_config(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    data = cfg or load_web_config()
    app = data.get("app") or {}
    api = data.get("api") or {}
    return {
        "title": app.get("title", "Ddo-Pulse"),
        "api_base": app.get("api_base", "/api"),
        "api_host": api.get("host", "127.0.0.1"),
        "api_port": int(api.get("port", 8765)),
    }


def sync_vite_env_file(cfg: dict[str, Any] | None = None) -> Path:
    """Write frontend/.ddo-pulse.env.json for Vite (gitignored)."""
    data = cfg or load_web_config()
    dev = data.get("dev_server") or {}
    app = data.get("app") or {}
    payload = {
        "vitePort": int(dev.get("port", 5173)),
        "proxyTarget": str(dev.get("api_proxy", "http://127.0.0.1:8765")),
        "apiBase": str(app.get("api_base", "/api")),
        "appTitle": str(app.get("title", "Ddo-Pulse")),
    }
    out = get_vite_env_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
