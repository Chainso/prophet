from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def generation_cache_path(root: Path) -> Path:
    return root / ".prophet" / "cache" / "generation.json"


def compute_generation_signature(
    *,
    toolchain_version: str,
    stack_id: str,
    ir_hash: str,
    out_dir: str,
    targets: Iterable[str],
    baseline_ir: str,
) -> str:
    payload = {
        "toolchain_version": toolchain_version,
        "stack_id": stack_id,
        "ir_hash": ir_hash,
        "out_dir": out_dir,
        "targets": list(targets),
        "baseline_ir": baseline_ir,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def load_generation_cache(root: Path) -> Dict[str, Any]:
    path = generation_cache_path(root)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        return {}
    return {}


def write_generation_cache(root: Path, payload: Dict[str, Any]) -> None:
    path = generation_cache_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
