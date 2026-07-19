"""CLI configuration store."""

import os
from pathlib import Path

import yaml

CONFIG_DIR = Path.home() / ".greencloud"
CONFIG_FILE = CONFIG_DIR / "config.yml"


def get_config() -> dict:
    """Load config from ~/.greencloud/config.yml."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        return yaml.safe_load(CONFIG_FILE.read_text()) or {}
    except Exception:
        return {}


def save_config(config: dict) -> None:
    """Save config to ~/.greencloud/config.yml."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(yaml.dump(config, default_flow_style=False))


def set_value(key: str, value: str) -> None:
    """Set a single config value."""
    config = get_config()
    config[key] = value
    save_config(config)


def get_value(key: str, default: str = "") -> str:
    """Get a single config value."""
    return get_config().get(key, default)
