from __future__ import annotations

from typing import Any, Dict, List

from ..support import _pascal_case
from ..support import _render_dataclass_field
from ..support import _sort_dict_entries


def render_event_contracts(ir: Dict[str, Any]) -> str:
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}
    struct_by_id = {item["id"]: item for item in ir.get("structs", []) if isinstance(item, dict) and "id" in item}

    lines: List[str] = [
        "# GENERATED FILE: do not edit directly.",
        "from __future__ import annotations",
        "",
        "from dataclasses import dataclass",
        "from typing import Optional, List",
        "",
        "from .domain import *",
        "",
    ]

    for event in _sort_dict_entries([item for item in ir.get("events", []) if isinstance(item, dict)]):
        name = _pascal_case(str(event.get("name", "Event")))
        lines.append("@dataclass")
        lines.append(f"class {name}:")
        fields = [field for field in event.get("fields", []) if isinstance(field, dict)]
        if not fields:
            lines.append("    pass")
        else:
            for field in fields:
                lines.append(
                    _render_dataclass_field(
                        field,
                        type_by_id=type_by_id,
                        object_by_id=object_by_id,
                        struct_by_id=struct_by_id,
                    )
                )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
