from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Set, Tuple

from prophet_cli.core.errors import ProphetError
from prophet_cli.codegen.stack_manifest import STACK_MANIFEST_DOCUMENT
from prophet_cli.codegen.stack_manifest import validate_stack_manifest_document


@dataclass(frozen=True)
class StackSpec:
    id: str
    language: str
    framework: str
    orm: str
    status: str
    implemented: bool
    description: str
    default_targets: Tuple[str, ...]
    notes: str
    capabilities: Set[str]


def _load_manifest() -> Dict[str, Any]:
    return validate_stack_manifest_document(STACK_MANIFEST_DOCUMENT)


_STACK_MANIFEST = _load_manifest()


def _load_supported_stacks(manifest: Dict[str, Any]) -> Dict[str, StackSpec]:
    supported: Dict[str, StackSpec] = {}
    for entry in manifest.get("stacks", []):
        supported[entry["id"]] = StackSpec(
            id=entry["id"],
            language=entry["language"],
            framework=entry["framework"],
            orm=entry["orm"],
            status=entry["status"],
            implemented=entry["status"] == "implemented",
            description=entry["description"],
            default_targets=tuple(entry["default_targets"]),
            notes=str(entry.get("notes", "")),
            capabilities=set(entry["capabilities"]),
        )
    return supported


SUPPORTED_STACKS: Dict[str, StackSpec] = _load_supported_stacks(_STACK_MANIFEST)


def _cfg_get(cfg: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    cur: Any = cfg
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def resolve_stack_spec(cfg: Dict[str, Any]) -> StackSpec:
    stack_cfg = _cfg_get(cfg, ["generation", "stack"], {})
    if stack_cfg is None:
        stack_cfg = {}
    if not isinstance(stack_cfg, dict):
        raise ProphetError("Invalid config: generation.stack must be a mapping in prophet.yaml.")

    allowed_keys = {"id", "language", "framework", "orm"}
    unknown_keys = sorted(str(k) for k in stack_cfg.keys() if k not in allowed_keys)
    if unknown_keys:
        allowed = ", ".join(sorted(allowed_keys))
        raise ProphetError(
            f"Invalid config keys under generation.stack: {', '.join(unknown_keys)}. "
            f"Allowed keys: {allowed}."
        )

    stack_id = str(stack_cfg.get("id", "")).strip()
    language = str(stack_cfg.get("language", "")).strip()
    framework = str(stack_cfg.get("framework", "")).strip()
    orm = str(stack_cfg.get("orm", "")).strip()

    if not stack_id and not (language or framework or orm):
        return SUPPORTED_STACKS["java_spring_jpa"]

    if stack_id:
        if stack_id not in SUPPORTED_STACKS:
            supported = ", ".join(sorted(SUPPORTED_STACKS.keys()))
            raise ProphetError(
                f"Unsupported generation stack '{stack_id}'. Supported stack ids: {supported}. "
                "Set generation.stack.id in prophet.yaml."
            )
        spec = SUPPORTED_STACKS[stack_id]
        if language and language != spec.language:
            raise ProphetError(
                f"generation.stack.language='{language}' does not match stack id '{stack_id}' "
                f"(expected '{spec.language}')."
            )
        if framework and framework != spec.framework:
            raise ProphetError(
                f"generation.stack.framework='{framework}' does not match stack id '{stack_id}' "
                f"(expected '{spec.framework}')."
            )
        if orm and orm != spec.orm:
            raise ProphetError(
                f"generation.stack.orm='{orm}' does not match stack id '{stack_id}' "
                f"(expected '{spec.orm}')."
            )
        return spec

    if not (language and framework and orm):
        raise ProphetError(
            "generation.stack.id is missing. When id is omitted, generation.stack.language, "
            "generation.stack.framework, and generation.stack.orm must all be provided."
        )

    matches = [spec for spec in SUPPORTED_STACKS.values() if spec.language == language and spec.framework == framework and spec.orm == orm]
    if not matches:
        combos = ", ".join(
            f"{spec.language}/{spec.framework}/{spec.orm}"
            for spec in sorted(SUPPORTED_STACKS.values(), key=lambda item: item.id)
        )
        raise ProphetError(
            "Unsupported generation stack combination "
            f"language='{language}', framework='{framework}', orm='{orm}'. "
            f"Supported combinations: {combos}."
        )
    return matches[0]


def supported_stack_table() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for stack_id in sorted(SUPPORTED_STACKS.keys()):
        spec = SUPPORTED_STACKS[stack_id]
        rows.append(
            {
                "id": spec.id,
                "language": spec.language,
                "framework": spec.framework,
                "orm": spec.orm,
                "status": spec.status,
                "implemented": spec.implemented,
                "description": spec.description,
                "default_targets": list(spec.default_targets),
                "notes": spec.notes,
                "capabilities": sorted(spec.capabilities),
            }
        )
    return rows


def stack_manifest_metadata() -> Dict[str, Any]:
    return {
        "schema_version": _STACK_MANIFEST["schema_version"],
        "capability_catalog": list(_STACK_MANIFEST["capability_catalog"]),
    }
