from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Set

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - exercised on 3.10 runners
    import tomli as tomllib  # type: ignore[no-redef]

JAVA_INIT_TARGETS = ["sql", "openapi", "spring_boot", "flyway", "liquibase"]


def _read_toml(path: Path) -> Dict[str, Any]:
    try:
        if not path.exists():
            return {}
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _normalize_dep_name(raw: str) -> str:
    text = raw.strip().lower()
    if not text:
        return ""
    token = re.split(r"[<>=!~\[\]\s;]+", text, maxsplit=1)[0]
    token = token.replace("_", "-")
    return token


def _extract_dependencies_from_pyproject(payload: Dict[str, Any]) -> Set[str]:
    deps: Set[str] = set()
    project = payload.get("project", {}) if isinstance(payload.get("project"), dict) else {}
    direct = project.get("dependencies", [])
    if isinstance(direct, list):
        for item in direct:
            if isinstance(item, str):
                name = _normalize_dep_name(item)
                if name:
                    deps.add(name)

    optional = project.get("optional-dependencies", {})
    if isinstance(optional, dict):
        for values in optional.values():
            if isinstance(values, list):
                for item in values:
                    if isinstance(item, str):
                        name = _normalize_dep_name(item)
                        if name:
                            deps.add(name)

    tool = payload.get("tool", {}) if isinstance(payload.get("tool"), dict) else {}
    poetry = tool.get("poetry", {}) if isinstance(tool.get("poetry"), dict) else {}
    poetry_deps = poetry.get("dependencies", {}) if isinstance(poetry.get("dependencies"), dict) else {}
    for key in poetry_deps.keys():
        name = _normalize_dep_name(str(key))
        if name and name != "python":
            deps.add(name)
    return deps


def _extract_dependencies_from_requirements(root: Path) -> Set[str]:
    deps: Set[str] = set()
    for rel in [
        "requirements.txt",
        "requirements-dev.txt",
        "requirements/prod.txt",
        "requirements/base.txt",
    ]:
        path = root / rel
        if not path.exists():
            continue
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                stripped = raw.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith("-r "):
                    continue
                name = _normalize_dep_name(stripped)
                if name:
                    deps.add(name)
        except Exception:
            continue
    return deps


def _detect_python_package_manager(root: Path) -> str:
    if (root / "poetry.lock").exists():
        return "poetry"
    if (root / "uv.lock").exists():
        return "uv"
    if (root / "Pipfile.lock").exists():
        return "pipenv"
    if (root / "requirements.txt").exists():
        return "pip"
    return "unknown"


def _detect_frameworks(deps: Set[str], root: Path) -> List[str]:
    frameworks: List[str] = []
    if "fastapi" in deps:
        frameworks.append("fastapi")
    if "flask" in deps:
        frameworks.append("flask")
    if "django" in deps or (root / "manage.py").exists():
        frameworks.append("django")
    return frameworks


def _detect_orms(deps: Set[str], frameworks: List[str]) -> List[str]:
    orms: List[str] = []
    if "sqlmodel" in deps:
        orms.append("sqlmodel")
    if "sqlalchemy" in deps:
        orms.append("sqlalchemy")
    if "django" in frameworks:
        orms.append("django_orm")
    return orms


def detect_python_stack(root: Path) -> Dict[str, Any]:
    pyproject_path = root / "pyproject.toml"
    pyproject_payload = _read_toml(pyproject_path)
    pyproject_deps = _extract_dependencies_from_pyproject(pyproject_payload)
    requirements_deps = _extract_dependencies_from_requirements(root)
    deps = set(sorted(pyproject_deps | requirements_deps))
    frameworks = _detect_frameworks(deps, root)
    orms = _detect_orms(deps, frameworks)

    enabled = bool(pyproject_path.exists() or requirements_deps or (root / "manage.py").exists())
    stack_id = ""
    confidence = "none"
    confidence_score = 0
    reasons: List[str] = []
    warnings: List[str] = []

    unique_frameworks = sorted(dict.fromkeys(frameworks))
    if len(unique_frameworks) > 1:
        confidence = "ambiguous"
        confidence_score = 40
        warnings.append(
            "Detected multiple Python framework signals ("
            + ", ".join(unique_frameworks)
            + "); set generation.stack.id explicitly."
        )
    elif len(unique_frameworks) == 1:
        framework = unique_frameworks[0]
        reasons.append(f"{framework} signal detected")
        if framework == "django":
            stack_id = "python_django_django_orm"
            confidence = "high"
            confidence_score = 90
            reasons.append("django ORM selected")
        else:
            has_sqlmodel = "sqlmodel" in orms
            has_sqlalchemy = "sqlalchemy" in orms
            if has_sqlmodel:
                stack_id = f"python_{framework}_sqlmodel"
                confidence = "high"
                confidence_score = 90
                reasons.append("sqlmodel dependency detected")
            elif has_sqlalchemy:
                stack_id = f"python_{framework}_sqlalchemy"
                confidence = "high"
                confidence_score = 90
                reasons.append("sqlalchemy dependency detected")
            else:
                confidence = "low"
                confidence_score = 35
                warnings.append(
                    f"{framework} detected, but no supported ORM detected for Python stack auto-selection."
                )
    elif enabled:
        confidence = "low"
        confidence_score = 20
        warnings.append(
            "Python project files detected, but no supported framework signal found. "
            "Set generation.stack.id explicitly."
        )

    diagnostics: List[Dict[str, str]] = []
    for reason in reasons:
        diagnostics.append({"level": "info", "message": reason})
    for warning in warnings:
        diagnostics.append({"level": "warning", "message": warning})

    return {
        "enabled": enabled,
        "project_kind": "python" if enabled else "unknown",
        "stack_id": stack_id,
        "confidence": confidence,
        "confidence_score": confidence_score,
        "package_manager": _detect_python_package_manager(root),
        "framework_signals": unique_frameworks,
        "orm_signals": sorted(dict.fromkeys(orms)),
        "signals": {
            "has_pyproject": pyproject_path.exists(),
            "has_requirements": bool(requirements_deps),
            "has_manage_py": (root / "manage.py").exists(),
            "dependency_count": len(deps),
        },
        "versions": {
            "fastapi": "present" if "fastapi" in deps else "",
            "flask": "present" if "flask" in deps else "",
            "django": "present" if "django" in deps else "",
            "sqlalchemy": "present" if "sqlalchemy" in deps else "",
            "sqlmodel": "present" if "sqlmodel" in deps else "",
        },
        "reasons": reasons,
        "warnings": warnings,
        "diagnostics": diagnostics,
    }


def apply_python_autodetect(cfg: Dict[str, Any], root: Path) -> Dict[str, Any]:
    report = detect_python_stack(root)
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

    chosen_stack = str(report.get("stack_id", "")).strip()
    if (not explicit_stack or default_java_stack) and chosen_stack:
        stack_cfg["id"] = chosen_stack

    targets = generation.get("targets")
    if isinstance(targets, list) and targets == JAVA_INIT_TARGETS and chosen_stack.startswith("python_"):
        if chosen_stack == "python_fastapi_sqlalchemy":
            generation["targets"] = ["sql", "openapi", "python", "fastapi", "sqlalchemy", "manifest"]
        elif chosen_stack == "python_fastapi_sqlmodel":
            generation["targets"] = ["sql", "openapi", "python", "fastapi", "sqlmodel", "manifest"]
        elif chosen_stack == "python_flask_sqlalchemy":
            generation["targets"] = ["sql", "openapi", "python", "flask", "sqlalchemy", "manifest"]
        elif chosen_stack == "python_flask_sqlmodel":
            generation["targets"] = ["sql", "openapi", "python", "flask", "sqlmodel", "manifest"]
        elif chosen_stack == "python_django_django_orm":
            generation["targets"] = ["sql", "openapi", "python", "django", "django_orm", "manifest"]

    cfg.pop("_python_autodetect_error", None)
    if report.get("enabled") and (not explicit_stack or default_java_stack) and not chosen_stack:
        if str(report.get("confidence")) in {"ambiguous", "low"}:
            warning_list = report.get("warnings", [])
            warning_hint = warning_list[0] if isinstance(warning_list, list) and warning_list else "Unable to infer Python stack."
            cfg["_python_autodetect_error"] = (
                f"{warning_hint} "
                "Set generation.stack.id explicitly to one of: "
                "python_fastapi_sqlalchemy, python_fastapi_sqlmodel, "
                "python_flask_sqlalchemy, python_flask_sqlmodel, python_django_django_orm."
            )

    cfg["_python_autodetect"] = report
    return cfg
