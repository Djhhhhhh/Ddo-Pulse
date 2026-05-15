"""Cross-platform paths for ~/.ddo_pulse."""

from __future__ import annotations

from pathlib import Path

DATA_DIR_NAME = ".ddo_pulse"
CONFIG_FILENAME = "config.yaml"
DB_FILENAME = "ddo_pulse.db"


def get_data_dir() -> Path:
    return Path.home() / DATA_DIR_NAME


def get_config_path() -> Path:
    return get_data_dir() / CONFIG_FILENAME


def get_db_path() -> Path:
    return get_data_dir() / DB_FILENAME


def ensure_data_dir() -> Path:
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
