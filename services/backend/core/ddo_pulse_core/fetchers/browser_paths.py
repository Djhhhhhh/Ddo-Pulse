"""Default browser user-data directories per OS."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def get_chrome_user_data_dir() -> Path:
    home = Path.home()
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            return Path(local) / "Google" / "Chrome" / "User Data"
    elif sys.platform == "darwin":
        return home / "Library" / "Application Support" / "Google" / "Chrome"
    return home / ".config" / "google-chrome"


def get_edge_user_data_dir() -> Path:
    home = Path.home()
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            return Path(local) / "Microsoft" / "Edge" / "User Data"
    elif sys.platform == "darwin":
        return home / "Library" / "Application Support" / "Microsoft Edge"
    return home / ".config" / "microsoft-edge"


def resolve_browser_user_data_dir(profile: str) -> Path:
    key = (profile or "chrome").strip().lower()
    if key in ("chrome", "google-chrome"):
        return get_chrome_user_data_dir()
    if key in ("edge", "msedge", "microsoft-edge"):
        return get_edge_user_data_dir()
    path = Path(profile).expanduser()
    if not path.is_absolute():
        raise ValueError(f"Custom browser_profile must be an absolute path: {profile}")
    return path
