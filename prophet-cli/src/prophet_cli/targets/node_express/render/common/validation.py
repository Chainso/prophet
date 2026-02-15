from __future__ import annotations

from typing import Any, Dict

from ..support import _camel_case
from ..support import _object_primary_key_fields
from ..support import _pascal_case
from ..support import _render_zod_property
from ..support import _zod_expr_for_descriptor

def _render_validation(ir: Dict[str, Any]) -> str:
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}
    struct_by_id = {item["id"]: item for item in ir.get("structs", []) if isinstance(item, dict) and "id" in item}

    lines: List[str] = ["// GENERATED FILE: do not edit directly.", "", "import { z } from 'zod';", ""]

    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        lines.append(f"export const {obj_name}RefSchema = z.object({{")
        for field in _object_primary_key_fields(obj):
            lines.append(_render_zod_property(field, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id))
        lines.append("});")
        lines.append("")

    for struct in sorted(ir.get("structs", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(struct, dict):
            continue
        name = _pascal_case(str(struct.get("name", "Struct")))
        lines.append(f"export const {name}Schema = z.object({{")
        for field in list(struct.get("fields", [])):
            if isinstance(field, dict):
                lines.append(_render_zod_property(field, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id))
        lines.append("});")
        lines.append("")

    for shape in sorted(ir.get("action_inputs", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(shape, dict):
            continue
        name = _pascal_case(str(shape.get("name", "ActionInput")))
        lines.append(f"export const {name}Schema = z.object({{")
        for field in list(shape.get("fields", [])):
            if isinstance(field, dict):
                lines.append(_render_zod_property(field, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id))
        lines.append("});")
        lines.append("")

    for shape in sorted(ir.get("action_outputs", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(shape, dict):
            continue
        name = _pascal_case(str(shape.get("name", "ActionOutput")))
        lines.append(f"export const {name}Schema = z.object({{")
        for field in list(shape.get("fields", [])):
            if isinstance(field, dict):
                lines.append(_render_zod_property(field, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id))
        lines.append("});")
        lines.append("")

    for event in sorted(ir.get("events", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(event, dict):
            continue
        if str(event.get("kind", "")) != "signal":
            continue
        name = _pascal_case(str(event.get("name", "Signal")))
        lines.append(f"export const {name}Schema = z.object({{")
        for field in list(event.get("fields", [])):
            if isinstance(field, dict):
                lines.append(_render_zod_property(field, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id))
        lines.append("});")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"

