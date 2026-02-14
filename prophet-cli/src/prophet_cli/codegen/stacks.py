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
    capabilities: Set[str]


SUPPORTED_STACKS: Dict[str, StackSpec] = {
    "java_spring_jpa": StackSpec(
        id="java_spring_jpa",
        language="java",
        framework="spring_boot",
        orm="jpa",
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
        capabilities={"action_endpoints", "typed_query_filters", "pagination", "object_refs", "nested_lists", "structs"},
    ),
    "node_express_prisma": StackSpec(
        id="node_express_prisma",
        language="node",
        framework="express",
        orm="prisma",
        capabilities={"action_endpoints", "typed_query_filters", "pagination", "object_refs", "nested_lists", "structs"},
    ),
    "node_express_mongoose": StackSpec(
        id="node_express_mongoose",
        language="node",
        framework="express",
        orm="mongoose",
        capabilities={"action_endpoints", "typed_query_filters", "pagination", "nested_lists", "structs"},
    ),
    "python_fastapi_sqlalchemy": StackSpec(
        id="python_fastapi_sqlalchemy",
        language="python",
        framework="fastapi",
        orm="sqlalchemy",
        capabilities={"action_endpoints", "typed_query_filters", "pagination", "object_refs", "nested_lists", "structs"},
    ),
    "python_flask_sqlalchemy": StackSpec(
        id="python_flask_sqlalchemy",
        language="python",
        framework="flask",
        orm="sqlalchemy",
        capabilities={"action_endpoints", "typed_query_filters", "pagination", "object_refs", "nested_lists", "structs"},
    ),
    "python_django_orm": StackSpec(
        id="python_django_orm",
        language="python",
        framework="django",
        orm="django_orm",
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
    stack_id = str(_cfg_get(cfg, ["generation", "stack", "id"], "java_spring_jpa")).strip()
    if not stack_id:
        stack_id = "java_spring_jpa"

    if stack_id not in SUPPORTED_STACKS:
        supported = ", ".join(sorted(SUPPORTED_STACKS.keys()))
        raise ProphetError(
            f"Unsupported generation stack '{stack_id}'. Supported stack ids: {supported}. "
            "Set generation.stack.id in prophet.yaml."
        )
    return SUPPORTED_STACKS[stack_id]


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
                "capabilities": sorted(spec.capabilities),
            }
        )
    return rows

