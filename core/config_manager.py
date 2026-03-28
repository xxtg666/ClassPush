import json
import os
import logging
from pathlib import Path

logger = logging.getLogger("classpush.config")

CONFIG_PATH = None

DEFAULT_CONFIG = {
    "display": {
        "font_size": 28,
        "sidebar_position": "right",
        "sidebar_width_percent": 30,
        "auto_close_seconds": 30,
        "dark_mode": False,
    },
    "notification": {
        "sound_enabled": True,
        "sound_volume": 60,
        "auto_start": False,
    },
    "network": {"port": 8080, "password": None},
    "theme": {
        "primary_color": "#4361ee",
        "card_style": "glassmorphism",
        "wallpaper": None,
    },
    "user": {"last_sender_name": "老师", "sender_history": [], "class_name": "班级"},
    "general": {"first_run": True},
    "web": {"saved_link": ""},
}


def get_config_path():
    global CONFIG_PATH
    if CONFIG_PATH is None:
        base_dir = Path(__file__).parent.parent
        CONFIG_PATH = str(base_dir / "config.json")
    return CONFIG_PATH


def load_config() -> dict:
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            config = _deep_merge(DEFAULT_CONFIG.copy(), user_config)
            return config
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Config file corrupted, using defaults: %s", e)
            backup = config_path + ".bak"
            if os.path.exists(config_path):
                import shutil

                shutil.copy2(config_path, backup)
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    config_path = get_config_path()
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        logger.info("Config saved")
    except IOError as e:
        logger.error("Failed to save config: %s", e)


def get_value(config: dict, *keys):
    val = config
    for k in keys:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            return None
    return val


def set_value(config: dict, value, *keys):
    d = config
    for k in keys[:-1]:
        if k not in d:
            d[k] = {}
        d = d[k]
    d[keys[-1]] = value


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
