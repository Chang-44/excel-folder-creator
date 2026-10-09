"""配置读写"""
import json
from pathlib import Path

from .models import AppConfig

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


def load_config() -> AppConfig:
    if not CONFIG_PATH.exists():
        return AppConfig()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return AppConfig.from_dict(json.load(f))
    except Exception:
        return AppConfig()


def save_config(cfg: AppConfig) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg.to_dict(), f, ensure_ascii=False, indent=2)