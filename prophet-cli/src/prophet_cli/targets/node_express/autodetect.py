from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

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


def _detect_tsconfig_details(root: Path, rel_path: str) -> Dict[str, Any]:
    if not rel_path:
        return {}
    payload = _read_json(root / rel_path)
    if not isinstance(payload, dict):
        return {}
    compiler = payload.get("compilerOptions", {}) if isinstance(payload.get("compilerOptions"), dict) else {}
    return {
        "rootDir": str(compiler.get("rootDir", "")),
        "outDir": str(compiler.get("outDir", "")),
        "module": str(compiler.get("module", "")),
        "moduleResolution": str(compiler.get("moduleResolution", "")),
    }


def _detect_monorepo(root: Path, package_json: Dict[str, Any]) -> bool:
    if isinstance(package_json.get("workspaces"), list):
        return True
    if isinstance(package_json.get("workspaces"), dict):
        return True
    if (root / "pnpm-workspace.yaml").exists():
        return True
    if (root / "turbo.json").exists():
        return True
    if (root / "lerna.json").exists():
        return True
    return False


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
    has_mongoose = "mongoose" in deps or any((root / "src").glob("**/*model*.ts"))

    stack_id = ""
    confidence = "none"
    confidence_score = 0
    reasons: List[str] = []
    warnings: List[str] = []

    detected_orms: List[tuple[str, str, str]] = []
    if has_prisma:
        detected_orms.append(("prisma", "node_express_prisma", "prisma dependency/schema detected"))
    if has_typeorm:
        detected_orms.append(("typeorm", "node_express_typeorm", "typeorm dependency/entities detected"))
    if has_mongoose:
        detected_orms.append(("mongoose", "node_express_mongoose", "mongoose dependency/models detected"))

    if has_express and len(detected_orms) > 1:
        confidence = "ambiguous"
        confidence_score = 40
        warnings.append(
            "Detected multiple ORM signals in an Express project ("
            + ", ".join(item[0] for item in detected_orms)
            + "); set generation.stack.id explicitly."
        )
    elif has_express and len(detected_orms) == 1:
        _, detected_stack_id, reason = detected_orms[0]
        stack_id = detected_stack_id
        confidence = "high"
        confidence_score = 90
        reasons.extend(["express dependency detected", reason])
    elif has_express:
        confidence = "low"
        confidence_score = 30
        warnings.append("Express detected, but no supported ORM detected for Node target auto-selection.")

    module_mode = str(package_json.get("type", "commonjs")) if package_json else ""
    if module_mode not in {"module", "commonjs"}:
        module_mode = "unknown"

    tsconfig_rel = _detect_tsconfig(root)
    diagnostics: List[Dict[str, str]] = []
    for reason in reasons:
        diagnostics.append({"level": "info", "message": reason})
    for warning in warnings:
        diagnostics.append({"level": "warning", "message": warning})

    report = {
        "enabled": has_package_json,
        "project_kind": "node" if has_package_json else "unknown",
        "stack_id": stack_id,
        "confidence": confidence,
        "confidence_score": confidence_score,
        "package_manager": _detect_package_manager(root),
        "module_mode": module_mode,
        "tsconfig": tsconfig_rel,
        "tsconfig_details": _detect_tsconfig_details(root, tsconfig_rel),
        "entrypoint": _detect_entrypoint(root, package_json),
        "monorepo": _detect_monorepo(root, package_json),
        "versions": {
            "express": str(deps.get("express", "")),
            "prisma": str(deps.get("prisma", deps.get("@prisma/client", ""))),
            "typeorm": str(deps.get("typeorm", "")),
            "mongoose": str(deps.get("mongoose", "")),
        },
        "signals": {
            "has_package_json": has_package_json,
            "has_express": has_express,
            "has_prisma": has_prisma,
            "has_typeorm": bool(has_typeorm),
            "has_mongoose": bool(has_mongoose),
        },
        "reasons": reasons,
        "warnings": warnings,
        "diagnostics": diagnostics,
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
        elif str(report.get("stack_id")) == "node_express_mongoose":
            generation["targets"] = ["openapi", "node_express", "mongoose", "manifest"]

    cfg.pop("_autodetect_error", None)
    if report.get("enabled") and (not explicit_stack or default_java_stack) and not str(report.get("stack_id", "")).strip():
        if str(report.get("confidence")) in {"ambiguous", "low"}:
            warning_list = report.get("warnings", [])
            warning_hint = warning_list[0] if isinstance(warning_list, list) and warning_list else "Unable to infer Node stack."
            cfg["_autodetect_error"] = (
                f"{warning_hint} "
                "Set generation.stack.id explicitly to node_express_prisma, node_express_typeorm, or node_express_mongoose."
            )

    cfg["_autodetect"] = report
    return cfg
