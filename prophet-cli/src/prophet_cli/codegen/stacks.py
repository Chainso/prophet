from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Set

from prophet_cli.core.errors import ProphetError


@dataclass(frozen=True)
class StackSpec:
    id: str
    language: str
    framework: str
    orm: str
    implemented: bool
    capabilities: Set[str]


SUPPORTED_STACKS: Dict[str, StackSpec] = {
    "java_spring_jpa": StackSpec(
        id="java_spring_jpa",
        language="java",
        framework="spring_boot",
        orm="jpa",
        implemented=True,
        capabilities={
            "action_endpoints",
            "typed_query_filters",
            "pagination",
            "object_refs",
            "nested_lists",
            "structs",
            "extension_hooks",
        },
    ),
    "node_express_typeorm": StackSpec(
        id="node_express_typeorm",
        language="node",
        framework="express",
        orm="typeorm",
        implemented=False,
        capabilities={"action_endpoints", "typed_query_filters", "pagination", "object_refs", "nested_lists", "structs"},
    ),
    "node_express_prisma": StackSpec(
        id="node_express_prisma",
        language="node",
        framework="express",
        orm="prisma",
        implemented=False,
        capabilities={"action_endpoints", "typed_query_filters", "pagination", "object_refs", "nested_lists", "structs"},
    ),
    "node_express_mongoose": StackSpec(
        id="node_express_mongoose",
        language="node",
        framework="express",
        orm="mongoose",
        implemented=False,
        capabilities={"action_endpoints", "typed_query_filters", "pagination", "nested_lists", "structs"},
    ),
    "python_fastapi_sqlalchemy": StackSpec(
        id="python_fastapi_sqlalchemy",
        language="python",
        framework="fastapi",
        orm="sqlalchemy",
        implemented=False,
        capabilities={"action_endpoints", "typed_query_filters", "pagination", "object_refs", "nested_lists", "structs"},
    ),
    "python_flask_sqlalchemy": StackSpec(
        id="python_flask_sqlalchemy",
        language="python",
        framework="flask",
        orm="sqlalchemy",
        implemented=False,
        capabilities={"action_endpoints", "typed_query_filters", "pagination", "object_refs", "nested_lists", "structs"},
    ),
    "python_django_orm": StackSpec(
        id="python_django_orm",
        language="python",
        framework="django",
        orm="django_orm",
        implemented=False,
        capabilities={"action_endpoints", "typed_query_filters", "pagination", "object_refs", "nested_lists", "structs"},
    ),
}


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
                "implemented": spec.implemented,
                "capabilities": sorted(spec.capabilities),
            }
        )
    return rows
