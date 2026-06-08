from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .models import BenchmarkConfig


def _expand(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _expand(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand(item) for item in value]
    if isinstance(value, str):
        return os.path.expandvars(os.path.expanduser(value))
    return value


def load_config(path: str | Path) -> BenchmarkConfig:
    config_path = Path(path).expanduser().resolve()
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return BenchmarkConfig.model_validate(_expand(payload))

