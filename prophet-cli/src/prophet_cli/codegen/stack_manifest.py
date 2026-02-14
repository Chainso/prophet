from __future__ import annotations

from typing import Any, Dict, Iterable, List

from prophet_cli.core.errors import ProphetError


KNOWN_CAPABILITIES = {
    "action_endpoints",
    "typed_query_filters",
    "pagination",
    "object_refs",
    "nested_lists",
    "structs",
    "extension_hooks",
}

STACK_MANIFEST: List[Dict[str, Any]] = [
    {
        "id": "java_spring_jpa",
        "language": "java",
        "framework": "spring_boot",
        "orm": "jpa",
        "status": "implemented",
        "capabilities": [
            "action_endpoints",
            "typed_query_filters",
            "pagination",
            "object_refs",
            "nested_lists",
            "structs",
            "extension_hooks",
        ],
    },
    {
        "id": "node_express_typeorm",
        "language": "node",
        "framework": "express",
        "orm": "typeorm",
        "status": "planned",
        "capabilities": [
            "action_endpoints",
            "typed_query_filters",
            "pagination",
            "object_refs",
            "nested_lists",
            "structs",
        ],
    },
    {
        "id": "node_express_prisma",
        "language": "node",
        "framework": "express",
        "orm": "prisma",
        "status": "planned",
        "capabilities": [
            "action_endpoints",
            "typed_query_filters",
            "pagination",
            "object_refs",
            "nested_lists",
            "structs",
        ],
    },
    {
        "id": "node_express_mongoose",
        "language": "node",
        "framework": "express",
        "orm": "mongoose",
        "status": "planned",
        "capabilities": [
            "action_endpoints",
            "typed_query_filters",
            "pagination",
            "nested_lists",
            "structs",
        ],
    },
    {
        "id": "python_fastapi_sqlalchemy",
        "language": "python",
        "framework": "fastapi",
        "orm": "sqlalchemy",
        "status": "planned",
        "capabilities": [
            "action_endpoints",
            "typed_query_filters",
            "pagination",
            "object_refs",
            "nested_lists",
            "structs",
        ],
    },
    {
        "id": "python_flask_sqlalchemy",
        "language": "python",
        "framework": "flask",
        "orm": "sqlalchemy",
        "status": "planned",
        "capabilities": [
            "action_endpoints",
            "typed_query_filters",
            "pagination",
            "object_refs",
            "nested_lists",
            "structs",
        ],
    },
    {
        "id": "python_django_orm",
        "language": "python",
        "framework": "django",
        "orm": "django_orm",
        "status": "planned",
        "capabilities": [
            "action_endpoints",
            "typed_query_filters",
            "pagination",
            "object_refs",
            "nested_lists",
            "structs",
        ],
    },
]


def _as_str(value: Any, field_name: str, index: int) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ProphetError(f"Invalid stack manifest entry at index {index}: '{field_name}' must be a non-empty string.")
    return text


def _normalize_capabilities(value: Any, index: int) -> List[str]:
    if not isinstance(value, list) or not value:
        raise ProphetError(
            f"Invalid stack manifest entry at index {index}: 'capabilities' must be a non-empty list."
        )
    normalized = [_as_str(item, "capabilities[]", index) for item in value]
    duplicates = sorted({name for name in normalized if normalized.count(name) > 1})
    if duplicates:
        raise ProphetError(
            f"Invalid stack manifest entry at index {index}: duplicate capabilities: {', '.join(duplicates)}."
        )
    unknown = sorted(name for name in normalized if name not in KNOWN_CAPABILITIES)
    if unknown:
        raise ProphetError(
            f"Invalid stack manifest entry at index {index}: unknown capabilities: {', '.join(unknown)}."
        )
    return normalized


def validate_stack_manifest(entries: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    required = {"id", "language", "framework", "orm", "status", "capabilities"}
    allowed_statuses = {"implemented", "planned"}
    normalized: List[Dict[str, Any]] = []
    seen_ids = set()
    seen_tuple_keys = set()

    for index, raw_entry in enumerate(entries):
        if not isinstance(raw_entry, dict):
            raise ProphetError(f"Invalid stack manifest entry at index {index}: must be a mapping.")

        unknown_keys = sorted(str(k) for k in raw_entry.keys() if k not in required)
        if unknown_keys:
            raise ProphetError(
                f"Invalid stack manifest entry at index {index}: unknown keys: {', '.join(unknown_keys)}."
            )

        missing_keys = sorted(key for key in required if key not in raw_entry)
        if missing_keys:
            raise ProphetError(
                f"Invalid stack manifest entry at index {index}: missing keys: {', '.join(missing_keys)}."
            )

        entry = {
            "id": _as_str(raw_entry.get("id"), "id", index),
            "language": _as_str(raw_entry.get("language"), "language", index),
            "framework": _as_str(raw_entry.get("framework"), "framework", index),
            "orm": _as_str(raw_entry.get("orm"), "orm", index),
            "status": _as_str(raw_entry.get("status"), "status", index),
            "capabilities": _normalize_capabilities(raw_entry.get("capabilities"), index),
        }

        if entry["status"] not in allowed_statuses:
            allowed = ", ".join(sorted(allowed_statuses))
            raise ProphetError(
                f"Invalid stack manifest entry at index {index}: status '{entry['status']}' is not supported. "
                f"Allowed values: {allowed}."
            )

        if entry["id"] in seen_ids:
            raise ProphetError(f"Invalid stack manifest entry at index {index}: duplicate id '{entry['id']}'.")
        seen_ids.add(entry["id"])

        tuple_key = (entry["language"], entry["framework"], entry["orm"])
        if tuple_key in seen_tuple_keys:
            raise ProphetError(
                f"Invalid stack manifest entry at index {index}: duplicate language/framework/orm tuple "
                f"'{entry['language']}/{entry['framework']}/{entry['orm']}'."
            )
        seen_tuple_keys.add(tuple_key)
        normalized.append(entry)

    if not normalized:
        raise ProphetError("Invalid stack manifest: at least one stack entry is required.")

    return normalized
