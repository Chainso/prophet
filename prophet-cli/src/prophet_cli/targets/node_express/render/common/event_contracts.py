from __future__ import annotations

from typing import Any, Dict, List, Set

from ..support import _camel_case
from ..support import _is_required
from ..support import _pascal_case
from ..support import _ts_type_for_descriptor


def _event_ts_type_for_descriptor(
    type_desc: Dict[str, Any],
    *,
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> str:
    kind = str(type_desc.get("kind", ""))
    if kind == "object_ref":
        object_id = str(type_desc.get("target_object_id", ""))
        if object_id in object_by_id:
            return f"{_pascal_case(str(object_by_id[object_id].get('name', 'Object')))}RefOrObject"
        return "Record<string, unknown>"
    if kind == "list":
        element = type_desc.get("element", {}) if isinstance(type_desc.get("element"), dict) else {}
        return f"{_event_ts_type_for_descriptor(element, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id)}[]"
    return _ts_type_for_descriptor(
        type_desc,
        type_by_id=type_by_id,
        object_by_id=object_by_id,
        struct_by_id=struct_by_id,
    )


def _render_event_property(
    field: Dict[str, Any],
    *,
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> str:
    name = _camel_case(str(field.get("name", "field")))
    type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
    ts_type = _event_ts_type_for_descriptor(
        type_desc,
        type_by_id=type_by_id,
        object_by_id=object_by_id,
        struct_by_id=struct_by_id,
    )
    optional = "?" if not _is_required(field) else ""
    return f"  {name}{optional}: {ts_type};"


def _collect_domain_symbols_for_type(
    type_desc: Dict[str, Any],
    *,
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> Set[str]:
    kind = str(type_desc.get("kind", ""))
    if kind == "object_ref":
        object_id = str(type_desc.get("target_object_id", ""))
        target = object_by_id.get(object_id)
        if not isinstance(target, dict):
            return set()
        name = _pascal_case(str(target.get("name", "Object")))
        return {name, f"{name}Ref"}
    if kind == "struct":
        struct_id = str(type_desc.get("target_struct_id", ""))
        target = struct_by_id.get(struct_id)
        if not isinstance(target, dict):
            return set()
        return {_pascal_case(str(target.get("name", "Struct")))}
    if kind == "list":
        element = type_desc.get("element", {}) if isinstance(type_desc.get("element"), dict) else {}
        return _collect_domain_symbols_for_type(
            element,
            object_by_id=object_by_id,
            struct_by_id=struct_by_id,
        )
    return set()


def _collect_event_object_names_for_type(
    type_desc: Dict[str, Any],
    *,
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> Set[str]:
    kind = str(type_desc.get("kind", ""))
    if kind == "object_ref":
        object_id = str(type_desc.get("target_object_id", ""))
        target = object_by_id.get(object_id)
        if not isinstance(target, dict):
            return set()
        return {_pascal_case(str(target.get("name", "Object")))}
    if kind == "struct":
        struct_id = str(type_desc.get("target_struct_id", ""))
        struct = struct_by_id.get(struct_id)
        if not isinstance(struct, dict):
            return set()
        names: Set[str] = set()
        for field in list(struct.get("fields", [])):
            if not isinstance(field, dict):
                continue
            field_type = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            names.update(
                _collect_event_object_names_for_type(
                    field_type,
                    object_by_id=object_by_id,
                    struct_by_id=struct_by_id,
                )
            )
        return names
    if kind == "list":
        element = type_desc.get("element", {}) if isinstance(type_desc.get("element"), dict) else {}
        return _collect_event_object_names_for_type(
            element,
            object_by_id=object_by_id,
            struct_by_id=struct_by_id,
        )
    return set()


def _render_event_contracts(ir: Dict[str, Any]) -> str:
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}
    output_by_id = {item["id"]: item for item in ir.get("action_outputs", []) if isinstance(item, dict) and "id" in item}
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}
    struct_by_id = {item["id"]: item for item in ir.get("structs", []) if isinstance(item, dict) and "id" in item}
    action_output_names = sorted(
        {
            _pascal_case(str(item.get("name", "Shape")))
            for item in ir.get("action_outputs", [])
            if isinstance(item, dict)
        }
    )
    action_output_aliases = {name: f"{name}ActionOutput" for name in action_output_names}
    event_object_names: Set[str] = set()
    domain_symbols: Set[str] = set()

    for event in sorted(ir.get("events", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(event, dict):
            continue
        kind = str(event.get("kind", ""))
        if kind == "signal":
            for field in list(event.get("fields", [])):
                if not isinstance(field, dict):
                    continue
                type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
                domain_symbols.update(
                    _collect_domain_symbols_for_type(
                        type_desc,
                        object_by_id=object_by_id,
                        struct_by_id=struct_by_id,
                    )
                )
                event_object_names.update(
                    _collect_event_object_names_for_type(
                        type_desc,
                        object_by_id=object_by_id,
                        struct_by_id=struct_by_id,
                    )
                )
        elif kind == "transition":
            object_id = str(event.get("object_id", ""))
            target = object_by_id.get(object_id)
            if isinstance(target, dict):
                object_name = _pascal_case(str(target.get("name", "Object")))
                event_object_names.add(object_name)
                domain_symbols.update({object_name, f"{object_name}Ref"})

    lines: List[str] = [
        "// Code generated by prophet-cli. DO NOT EDIT.",
        "",
    ]

    if domain_symbols:
        lines.extend(
            [
                "import type {",
                "  " + ",\n  ".join(sorted(domain_symbols)),
                "} from './domain';",
            ]
        )

    if action_output_names:
        lines.extend(
            [
                "import type {",
                "  " + ",\n  ".join(
                    [f"{name} as {action_output_aliases[name]}" for name in action_output_names]
                ),
                "} from './actions';",
                "",
            ]
        )
    else:
        lines.append("")

    for object_name in sorted(event_object_names):
        lines.append(f"export type {object_name}RefOrObject = {object_name}Ref | {object_name};")
    if event_object_names:
        lines.append("")

    for event in sorted(ir.get("events", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(event, dict):
            continue
        kind = str(event.get("kind", ""))
        event_name = _pascal_case(str(event.get("name", "Event")))
        if kind == "signal":
            lines.append(f"export interface {event_name} {{")
            for field in list(event.get("fields", [])):
                if isinstance(field, dict):
                    lines.append(
                        _render_event_property(
                            field,
                            type_by_id=type_by_id,
                            object_by_id=object_by_id,
                            struct_by_id=struct_by_id,
                        )
                    )
            lines.append("}")
            lines.append("")
        elif kind == "action_output":
            output_id = str(event.get("output_shape_id", ""))
            alias = _pascal_case(str(output_by_id.get(output_id, {}).get("name", event_name)))
            aliased_import = action_output_aliases.get(alias, alias)
            lines.append(f"export type {event_name} = {aliased_import};")
            lines.append("")
        elif kind == "transition":
            object_id = str(event.get("object_id", ""))
            obj = object_by_id.get(object_id, {})
            obj_name = _pascal_case(str(obj.get("name", "Object")))
            lines.append(f"export interface {event_name} {{")
            lines.append(f"  object: {obj_name}RefOrObject;")
            lines.append("}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"
