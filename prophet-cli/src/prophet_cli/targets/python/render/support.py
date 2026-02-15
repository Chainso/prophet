from __future__ import annotations

import re
from typing import Any, Dict, List


def _pascal_case(value: str) -> str:
    chunks = [part for part in re.split(r"[_\-\s]+", value) if part]
    return "".join(chunk[:1].upper() + chunk[1:] for chunk in chunks)


def _snake_case(value: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.replace("-", "_").lower()


def _camel_case(value: str) -> str:
    p = _pascal_case(value)
    return p[:1].lower() + p[1:] if p else p


def _pluralize(value: str) -> str:
    if value.endswith("y") and len(value) > 1 and value[-2] not in "aeiou":
        return value[:-1] + "ies"
    if value.endswith("s"):
        return value + "es"
    return value + "s"


def _is_required(field: Dict[str, Any]) -> bool:
    card = field.get("cardinality", {})
    if isinstance(card, dict):
        return int(card.get("min", 0)) > 0
    return False


def _field_index(fields: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {str(item.get("id", "")): item for item in fields if isinstance(item, dict)}


def _object_primary_key_fields(obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    fields = list(obj.get("fields", []))
    by_id = _field_index(fields)
    key_ids = list(obj.get("keys", {}).get("primary", {}).get("field_ids", []))
    return [by_id[fid] for fid in key_ids if fid in by_id]


def _resolve_custom_base(type_by_id: Dict[str, Dict[str, Any]], type_desc: Dict[str, Any]) -> str:
    current = type_desc
    seen: set[str] = set()
    while current.get("kind") == "custom":
        target_id = str(current.get("target_type_id", ""))
        if not target_id or target_id in seen or target_id not in type_by_id:
            return "string"
        seen.add(target_id)
        target = type_by_id[target_id]
        base = str(target.get("base", "string"))
        if base in (
            "string",
            "boolean",
            "int",
            "long",
            "short",
            "byte",
            "double",
            "float",
            "decimal",
            "datetime",
            "date",
            "duration",
        ):
            return base
        current = {"kind": "custom", "target_type_id": target_id}
    return "string"


def _py_base_type(base_name: str) -> str:
    mapping = {
        "string": "str",
        "boolean": "bool",
        "int": "int",
        "long": "int",
        "short": "int",
        "byte": "int",
        "double": "float",
        "float": "float",
        "decimal": "float",
        "datetime": "str",
        "date": "str",
        "duration": "str",
    }
    return mapping.get(base_name, "Any")


def _py_type_for_descriptor(
    type_desc: Dict[str, Any],
    *,
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> str:
    kind = str(type_desc.get("kind", ""))
    if kind == "base":
        return _py_base_type(str(type_desc.get("name", "string")))
    if kind == "custom":
        return _py_base_type(_resolve_custom_base(type_by_id, type_desc))
    if kind == "struct":
        struct_id = str(type_desc.get("target_struct_id", ""))
        if struct_id in struct_by_id:
            return _pascal_case(str(struct_by_id[struct_id].get("name", "Struct")))
        return "Dict[str, Any]"
    if kind == "object_ref":
        object_id = str(type_desc.get("target_object_id", ""))
        if object_id in object_by_id:
            return f"{_pascal_case(str(object_by_id[object_id].get('name', 'Object')))}Ref"
        return "Dict[str, Any]"
    if kind == "list":
        element = type_desc.get("element", {}) if isinstance(type_desc.get("element"), dict) else {}
        return f"List[{_py_type_for_descriptor(element, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id)}]"
    return "Any"


def _render_dataclass_field(
    field: Dict[str, Any],
    *,
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> str:
    name = _camel_case(str(field.get("name", "field")))
    type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
    py_type = _py_type_for_descriptor(
        type_desc,
        type_by_id=type_by_id,
        object_by_id=object_by_id,
        struct_by_id=struct_by_id,
    )
    if _is_required(field):
        return f"    {name}: {py_type}"
    return f"    {name}: Optional[{py_type}] = None"


def _py_id_expr_for_field(field: Dict[str, Any], param_name: str = "id") -> str:
    name = _camel_case(str(field.get("name", "id")))
    return f"{param_name}.{name}"


def _sort_dict_entries(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(items, key=lambda item: str(item.get("id", "")))
