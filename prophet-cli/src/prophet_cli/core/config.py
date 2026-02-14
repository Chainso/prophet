from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from .errors import ProphetError


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise ProphetError(f"prophet.yaml not found in current directory: {path.parent}")
    try:
        with path.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    except OSError as exc:
        raise ProphetError(f"Failed to read config {path}: {exc}") from exc
    if not isinstance(cfg, dict):
        raise ProphetError(f"Invalid config format in {path}")
    return cfg


def cfg_get(cfg: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    cur: Any = cfg
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

