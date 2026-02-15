from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

JAVA_INIT_TARGETS = ["sql", "openapi", "spring_boot", "flyway", "liquibase"]


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _detect_package_manager(root: Path) -> str:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    if (root / "bun.lockb").exists() or (root / "bun.lock").exists():
        return "bun"
    if (root / "package-lock.json").exists():
        return "npm"
    return "unknown"


def _detect_tsconfig(root: Path) -> str:
    for candidate in ["tsconfig.json", "tsconfig.base.json", "apps/api/tsconfig.json"]:
        if (root / candidate).exists():
            return candidate
    return ""


def _detect_entrypoint(root: Path, package_json: Dict[str, Any]) -> str:
    scripts = package_json.get("scripts", {}) if isinstance(package_json.get("scripts"), dict) else {}
    start = str(scripts.get("start", "")).strip()
    if start:
        match = re.search(r"([A-Za-z0-9_./\-]+\.(?:ts|js))", start)
        if match:
            return match.group(1)

    main = str(package_json.get("main", "")).strip()
    if main:
        return main

    for candidate in [
        "src/index.ts",
        "src/server.ts",
        "src/app.ts",
        "index.ts",
        "server.ts",
    ]:
        if (root / candidate).exists():
            return candidate
    return ""


def _dependencies(package_json: Dict[str, Any]) -> Dict[str, str]:
    deps: Dict[str, str] = {}
    for key in ["dependencies", "devDependencies", "peerDependencies"]:
        section = package_json.get(key, {})
        if isinstance(section, dict):
            for dep_name, dep_version in section.items():
                deps[str(dep_name)] = str(dep_version)
    return deps


def detect_node_stack(root: Path) -> Dict[str, Any]:
    package_json_path = root / "package.json"
    package_json = _read_json(package_json_path)
    deps = _dependencies(package_json)

    has_package_json = package_json_path.exists()
    has_express = "express" in deps
    has_prisma = "prisma" in deps or "@prisma/client" in deps or (root / "prisma" / "schema.prisma").exists()
    has_typeorm = "typeorm" in deps or any((root / "src").glob("**/*entity*.ts"))

    stack_id = ""
    confidence = "none"
    reasons: List[str] = []
    warnings: List[str] = []

    if has_express and has_prisma and has_typeorm:
        confidence = "ambiguous"
        warnings.append("Detected both Prisma and TypeORM in an Express project; set generation.stack.id explicitly.")
    elif has_express and has_prisma:
        stack_id = "node_express_prisma"
        confidence = "high"
        reasons.extend(["express dependency detected", "prisma dependency/schema detected"])
    elif has_express and has_typeorm:
        stack_id = "node_express_typeorm"
        confidence = "high"
        reasons.extend(["express dependency detected", "typeorm dependency/entities detected"])
    elif has_express:
        confidence = "low"
        warnings.append("Express detected, but no supported ORM detected for Node target auto-selection.")

    module_mode = str(package_json.get("type", "commonjs")) if package_json else ""
    if module_mode not in {"module", "commonjs"}:
        module_mode = "unknown"

    report = {
        "enabled": has_package_json,
        "project_kind": "node" if has_package_json else "unknown",
        "stack_id": stack_id,
        "confidence": confidence,
        "package_manager": _detect_package_manager(root),
        "module_mode": module_mode,
        "tsconfig": _detect_tsconfig(root),
        "entrypoint": _detect_entrypoint(root, package_json),
        "monorepo": bool(package_json.get("workspaces")) if isinstance(package_json, dict) else False,
        "signals": {
            "has_package_json": has_package_json,
            "has_express": has_express,
            "has_prisma": has_prisma,
            "has_typeorm": bool(has_typeorm),
        },
        "reasons": reasons,
        "warnings": warnings,
    }
    return report


def apply_node_autodetect(cfg: Dict[str, Any], root: Path) -> Dict[str, Any]:
    report = detect_node_stack(root)
    if not isinstance(cfg.get("generation"), dict):
        cfg["generation"] = {}
    generation = cfg["generation"]

    if not isinstance(generation.get("stack"), dict):
        generation["stack"] = {}
    stack_cfg = generation["stack"]

    explicit_stack = bool(str(stack_cfg.get("id", "")).strip()) or all(
        str(stack_cfg.get(key, "")).strip() for key in ["language", "framework", "orm"]
    )
    default_java_stack = (
        str(stack_cfg.get("id", "")).strip() == "java_spring_jpa"
        and not str(stack_cfg.get("language", "")).strip()
        and not str(stack_cfg.get("framework", "")).strip()
        and not str(stack_cfg.get("orm", "")).strip()
    )

    if (not explicit_stack or default_java_stack) and str(report.get("stack_id", "")).strip():
        stack_cfg["id"] = str(report["stack_id"])

    targets = generation.get("targets")
    if isinstance(targets, list) and targets == JAVA_INIT_TARGETS and str(report.get("stack_id", "")).startswith("node_express"):
        if str(report.get("stack_id")) == "node_express_prisma":
            generation["targets"] = ["sql", "openapi", "node_express", "prisma", "manifest"]
        elif str(report.get("stack_id")) == "node_express_typeorm":
            generation["targets"] = ["sql", "openapi", "node_express", "typeorm", "manifest"]

    cfg["_autodetect"] = report
    return cfg
