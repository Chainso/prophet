from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

DEFAULT_RUNTIME_VERSION = "0.5.0"
DEFAULT_JAVA_RUNTIME_GROUP = "io.github.chainso"


def _find_runtime_repo_root(start: Path) -> Optional[Path]:
    cursor = start.resolve()
    for candidate in (cursor, *cursor.parents):
        if (candidate / "prophet-lib" / "VERSION").is_file():
            return candidate
    return None


def resolve_runtime_version(start: Path) -> str:
    repo_root = _find_runtime_repo_root(start)
    if repo_root is None:
        return DEFAULT_RUNTIME_VERSION
    version_text = (repo_root / "prophet-lib" / "VERSION").read_text(encoding="utf-8").strip()
    return version_text or DEFAULT_RUNTIME_VERSION


def resolve_java_runtime_group(start: Path) -> str:
    repo_root = _find_runtime_repo_root(start)
    if repo_root is None:
        return DEFAULT_JAVA_RUNTIME_GROUP
    build_file = repo_root / "prophet-lib" / "java" / "build.gradle.kts"
    if not build_file.is_file():
        return DEFAULT_JAVA_RUNTIME_GROUP
    text = build_file.read_text(encoding="utf-8")
    match = re.search(r'^\s*group\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        return DEFAULT_JAVA_RUNTIME_GROUP
    group = match.group(1).strip()
    return group or DEFAULT_JAVA_RUNTIME_GROUP
