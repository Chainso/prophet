from __future__ import annotations

from typing import Any, Dict, List

from ..support import _camel_case
from ..support import _object_primary_key_fields
from ..support import _pascal_case
from ..support import _render_property
from ..support import _ts_base_type
from ..support import _ts_type_for_descriptor

def _render_domain_types(ir: Dict[str, Any]) -> str:
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}
    struct_by_id = {item["id"]: item for item in ir.get("structs", []) if isinstance(item, dict) and "id" in item}

    lines: List[str] = ["// GENERATED FILE: do not edit directly.", ""]

    for custom in sorted(ir.get("types", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(custom, dict):
            continue
        name = _pascal_case(str(custom.get("name", "CustomType")))
        ts_base = _ts_base_type(str(custom.get("base", "string")))
        lines.append(f"export type {name} = {ts_base};")
    if ir.get("types"):
        lines.append("")

    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        pk_fields = _object_primary_key_fields(obj)
        lines.append(f"export interface {obj_name}Ref {{")
        for field in pk_fields:
            lines.append(_render_property(field, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id))
        lines.append("}")
        lines.append("")

    for struct in sorted(ir.get("structs", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(struct, dict):
            continue
        name = _pascal_case(str(struct.get("name", "Struct")))
        lines.append(f"export interface {name} {{")
        for field in list(struct.get("fields", [])):
            if isinstance(field, dict):
                lines.append(_render_property(field, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id))
        lines.append("}")
        lines.append("")

    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        states = list(obj.get("states", []))
        if states:
            members = " | ".join(f'"{str(item.get("name", ""))}"' for item in states if isinstance(item, dict))
            lines.append(f"export type {obj_name}State = {members};")
            lines.append("")

        lines.append(f"export interface {obj_name} {{")
        for field in list(obj.get("fields", [])):
            if isinstance(field, dict):
                lines.append(_render_property(field, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id))
        if states:
            lines.append(f"  currentState: {obj_name}State;")
        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
