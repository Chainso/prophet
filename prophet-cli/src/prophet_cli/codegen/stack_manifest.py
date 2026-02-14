from __future__ import annotations

from typing import Any, Dict, Iterable, List

from prophet_cli.core.errors import ProphetError


KNOWN_CAPABILITIES = (
    "action_endpoints",
    "typed_query_filters",
    "pagination",
    "object_refs",
    "nested_lists",
    "structs",
    "extension_hooks",
)

KNOWN_GENERATION_TARGETS = ("sql", "openapi", "spring_boot", "flyway", "liquibase", "manifest")

STACK_MANIFEST_DOCUMENT: Dict[str, Any] = {
    "schema_version": 1,
    "capability_catalog": list(KNOWN_CAPABILITIES),
    "stacks": [
        {
            "id": "java_spring_jpa",
            "language": "java",
            "framework": "spring_boot",
            "orm": "jpa",
            "status": "implemented",
            "description": "Reference stack with Spring Boot REST APIs and Spring Data JPA persistence generation.",
            "capabilities": list(KNOWN_CAPABILITIES),
            "default_targets": ["sql", "openapi", "spring_boot", "flyway", "liquibase", "manifest"],
            "notes": "Golden stack used for deterministic snapshot and runtime validation.",
        },
        {
            "id": "node_express_typeorm",
            "language": "node",
            "framework": "express",
            "orm": "typeorm",
            "status": "planned",
            "description": "Node + Express stack targeting relational persistence via TypeORM.",
            "capabilities": ["action_endpoints", "typed_query_filters", "pagination", "object_refs", "nested_lists", "structs"],
            "default_targets": ["sql", "openapi", "manifest"],
        },
        {
            "id": "node_express_prisma",
            "language": "node",
            "framework": "express",
            "orm": "prisma",
            "status": "planned",
            "description": "Node + Express stack targeting relational persistence via Prisma schema generation.",
            "capabilities": ["action_endpoints", "typed_query_filters", "pagination", "object_refs", "nested_lists", "structs"],
            "default_targets": ["sql", "openapi", "manifest"],
        },
        {
            "id": "node_express_mongoose",
            "language": "node",
            "framework": "express",
            "orm": "mongoose",
            "status": "planned",
            "description": "Node + Express stack targeting document persistence with Mongoose.",
            "capabilities": ["action_endpoints", "typed_query_filters", "pagination", "nested_lists", "structs"],
            "default_targets": ["openapi", "manifest"],
            "notes": "Object reference capability intentionally omitted pending document-model linking strategy.",
        },
        {
            "id": "python_fastapi_sqlalchemy",
            "language": "python",
            "framework": "fastapi",
            "orm": "sqlalchemy",
            "status": "planned",
            "description": "Python + FastAPI stack with SQLAlchemy ORM and pydantic boundary models.",
            "capabilities": ["action_endpoints", "typed_query_filters", "pagination", "object_refs", "nested_lists", "structs"],
            "default_targets": ["sql", "openapi", "manifest"],
        },
        {
            "id": "python_flask_sqlalchemy",
            "language": "python",
            "framework": "flask",
            "orm": "sqlalchemy",
            "status": "planned",
            "description": "Python + Flask stack with SQLAlchemy ORM integration.",
            "capabilities": ["action_endpoints", "typed_query_filters", "pagination", "object_refs", "nested_lists", "structs"],
            "default_targets": ["sql", "openapi", "manifest"],
        },
        {
            "id": "python_django_orm",
            "language": "python",
            "framework": "django",
            "orm": "django_orm",
            "status": "planned",
            "description": "Python + Django stack with native Django ORM models and request routing.",
            "capabilities": ["action_endpoints", "typed_query_filters", "pagination", "object_refs", "nested_lists", "structs"],
            "default_targets": ["openapi", "manifest"],
        },
    ],
}


def _as_str(value: Any, field_name: str, index: int) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ProphetError(f"Invalid stack manifest entry at index {index}: '{field_name}' must be a non-empty string.")
    return text


def _normalize_string_list(
    value: Any,
    *,
    field_name: str,
    index: int,
    allow_empty: bool = False,
) -> List[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        qualifier = "a list" if allow_empty else "a non-empty list"
        raise ProphetError(f"Invalid stack manifest entry at index {index}: '{field_name}' must be {qualifier}.")
    normalized = [_as_str(item, f"{field_name}[]", index) for item in value]
    duplicates = sorted({name for name in normalized if normalized.count(name) > 1})
    if duplicates:
        raise ProphetError(
            f"Invalid stack manifest entry at index {index}: duplicate values in '{field_name}': {', '.join(duplicates)}."
        )
    return normalized


def _normalize_capability_catalog(value: Any) -> List[str]:
    if not isinstance(value, list) or not value:
        raise ProphetError("Invalid stack manifest document: 'capability_catalog' must be a non-empty list.")
    normalized = [str(item).strip() for item in value]
    if any(not item for item in normalized):
        raise ProphetError("Invalid stack manifest document: capability_catalog entries must be non-empty strings.")
    duplicates = sorted({name for name in normalized if normalized.count(name) > 1})
    if duplicates:
        raise ProphetError(
            f"Invalid stack manifest document: duplicate capabilities in capability_catalog: {', '.join(duplicates)}."
        )
    return normalized


def _validate_default_targets(targets: Iterable[str], index: int) -> List[str]:
    normalized = [str(item).strip() for item in targets]
    unknown = sorted(name for name in normalized if name not in KNOWN_GENERATION_TARGETS)
    if unknown:
        allowed = ", ".join(KNOWN_GENERATION_TARGETS)
        raise ProphetError(
            f"Invalid stack manifest entry at index {index}: unknown default_targets values: {', '.join(unknown)}. "
            f"Allowed values: {allowed}."
        )
    return normalized


def validate_stack_manifest_document(document: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(document, dict):
        raise ProphetError("Invalid stack manifest document: expected a mapping.")

    required_document_keys = {"schema_version", "capability_catalog", "stacks"}
    unknown_document_keys = sorted(str(k) for k in document.keys() if k not in required_document_keys)
    if unknown_document_keys:
        raise ProphetError(
            "Invalid stack manifest document: unknown keys: " + ", ".join(unknown_document_keys) + "."
        )

    missing_document_keys = sorted(key for key in required_document_keys if key not in document)
    if missing_document_keys:
        raise ProphetError(
            "Invalid stack manifest document: missing keys: " + ", ".join(missing_document_keys) + "."
        )

    schema_version = document.get("schema_version")
    if not isinstance(schema_version, int) or schema_version != 1:
        raise ProphetError("Invalid stack manifest document: schema_version must be integer value 1.")

    capability_catalog = _normalize_capability_catalog(document.get("capability_catalog"))

    raw_stacks = document.get("stacks")
    if not isinstance(raw_stacks, list) or not raw_stacks:
        raise ProphetError("Invalid stack manifest document: 'stacks' must be a non-empty list.")

    required_stack_keys = {"id", "language", "framework", "orm", "status", "description", "capabilities", "default_targets"}
    optional_stack_keys = {"notes"}
    allowed_stack_keys = required_stack_keys | optional_stack_keys
    allowed_statuses = {"implemented", "planned"}
    normalized_stacks: List[Dict[str, Any]] = []
    seen_ids = set()
    seen_tuple_keys = set()

    for index, raw_entry in enumerate(raw_stacks):
        if not isinstance(raw_entry, dict):
            raise ProphetError(f"Invalid stack manifest entry at index {index}: must be a mapping.")

        unknown_keys = sorted(str(k) for k in raw_entry.keys() if k not in allowed_stack_keys)
        if unknown_keys:
            raise ProphetError(
                f"Invalid stack manifest entry at index {index}: unknown keys: {', '.join(unknown_keys)}."
            )

        missing_keys = sorted(key for key in required_stack_keys if key not in raw_entry)
        if missing_keys:
            raise ProphetError(
                f"Invalid stack manifest entry at index {index}: missing keys: {', '.join(missing_keys)}."
            )

        capabilities = _normalize_string_list(raw_entry.get("capabilities"), field_name="capabilities", index=index)
        unknown_capabilities = sorted(name for name in capabilities if name not in capability_catalog)
        if unknown_capabilities:
            raise ProphetError(
                f"Invalid stack manifest entry at index {index}: unknown capabilities: {', '.join(unknown_capabilities)}."
            )

        default_targets = _normalize_string_list(
            raw_entry.get("default_targets"),
            field_name="default_targets",
            index=index,
        )
        default_targets = _validate_default_targets(default_targets, index)

        entry = {
            "id": _as_str(raw_entry.get("id"), "id", index),
            "language": _as_str(raw_entry.get("language"), "language", index),
            "framework": _as_str(raw_entry.get("framework"), "framework", index),
            "orm": _as_str(raw_entry.get("orm"), "orm", index),
            "status": _as_str(raw_entry.get("status"), "status", index),
            "description": _as_str(raw_entry.get("description"), "description", index),
            "capabilities": capabilities,
            "default_targets": default_targets,
        }
        if "notes" in raw_entry:
            entry["notes"] = _as_str(raw_entry.get("notes"), "notes", index)

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
        normalized_stacks.append(entry)

    return {
        "schema_version": schema_version,
        "capability_catalog": capability_catalog,
        "stacks": normalized_stacks,
    }
