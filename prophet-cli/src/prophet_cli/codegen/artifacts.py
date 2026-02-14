from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def write_outputs(outputs: Dict[str, str], root: Path) -> None:
    for rel_path, content in outputs.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def managed_existing_files(root: Path, out_dir: str) -> List[str]:
    manifest_path = root / out_dir / "manifest" / "generated-files.json"
    if manifest_path.exists():
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            outputs = payload.get("outputs", [])
            if isinstance(outputs, list):
                managed_from_manifest = []
                for entry in outputs:
                    if isinstance(entry, dict):
                        rel = entry.get("path")
                        if isinstance(rel, str) and rel:
                            managed_from_manifest.append(rel)
                managed_from_manifest.append(str(manifest_path.relative_to(root)))
                return sorted(set(managed_from_manifest))
        except Exception:
            pass

    managed_paths = [
        root / out_dir / "sql",
        root / out_dir / "migrations",
        root / out_dir / "openapi",
        root / out_dir / "spring-boot",
        root / out_dir / "manifest",
    ]
    ignored_parts = {"build", ".gradle", ".idea", ".settings", "bin", "out", "target"}
    result: List[str] = []
    for p in managed_paths:
        if p.exists():
            for child in p.rglob("*"):
                if child.is_file():
                    rel = child.relative_to(root)
                    if any(part in ignored_parts for part in rel.parts):
                        continue
                    if any(part.startswith(".") for part in rel.parts):
                        continue
                    result.append(str(rel))
    return sorted(result)


def remove_stale_outputs(root: Path, out_dir: str, outputs: Dict[str, str]) -> None:
    existing = set(managed_existing_files(root, out_dir))
    desired = set(outputs.keys())
    stale = sorted(existing - desired)
    for rel in stale:
        p = root / rel
        if p.exists():
            p.unlink()
            parent = p.parent
            while parent != root and parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent

