from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from prophet_cli.codegen.contracts import GenerationContext
from prophet_cli.codegen.stacks import StackSpec
from prophet_cli.core.ir_reader import IRReader


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


def _ts_base_type(base_name: str) -> str:
    mapping = {
        "string": "string",
        "boolean": "boolean",
        "int": "number",
        "long": "number",
        "short": "number",
        "byte": "number",
        "double": "number",
        "float": "number",
        "decimal": "number",
        "datetime": "string",
        "date": "string",
        "duration": "string",
    }
    return mapping.get(base_name, "unknown")


def _zod_base_expr(base_name: str) -> str:
    mapping = {
        "string": "z.string()",
        "boolean": "z.boolean()",
        "int": "z.number().int()",
        "long": "z.number().int()",
        "short": "z.number().int()",
        "byte": "z.number().int()",
        "double": "z.number()",
        "float": "z.number()",
        "decimal": "z.number()",
        "datetime": "z.string()",
        "date": "z.string()",
        "duration": "z.string()",
    }
    return mapping.get(base_name, "z.unknown()")


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
    resolved = [by_id[fid] for fid in key_ids if fid in by_id]
    return resolved


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
        if base in ("string", "boolean", "int", "long", "short", "byte", "double", "float", "decimal", "datetime", "date", "duration"):
            return base
        current = {"kind": "custom", "target_type_id": target_id}
    return "string"


def _ts_type_for_descriptor(
    type_desc: Dict[str, Any],
    *,
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> str:
    kind = str(type_desc.get("kind", ""))
    if kind == "base":
        return _ts_base_type(str(type_desc.get("name", "string")))
    if kind == "custom":
        base = _resolve_custom_base(type_by_id, type_desc)
        return _ts_base_type(base)
    if kind == "struct":
        struct_id = str(type_desc.get("target_struct_id", ""))
        if struct_id in struct_by_id:
            return _pascal_case(str(struct_by_id[struct_id].get("name", "Struct")))
        return "Record<string, unknown>"
    if kind == "object_ref":
        object_id = str(type_desc.get("target_object_id", ""))
        if object_id in object_by_id:
            return f"{_pascal_case(str(object_by_id[object_id].get('name', 'Object')))}Ref"
        return "Record<string, unknown>"
    if kind == "list":
        element = type_desc.get("element", {}) if isinstance(type_desc.get("element"), dict) else {}
        return f"{_ts_type_for_descriptor(element, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id)}[]"
    return "unknown"


def _zod_expr_for_descriptor(
    type_desc: Dict[str, Any],
    *,
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> str:
    kind = str(type_desc.get("kind", ""))
    if kind == "base":
        return _zod_base_expr(str(type_desc.get("name", "string")))
    if kind == "custom":
        base = _resolve_custom_base(type_by_id, type_desc)
        return _zod_base_expr(base)
    if kind == "struct":
        struct_id = str(type_desc.get("target_struct_id", ""))
        if struct_id in struct_by_id:
            return f"{_pascal_case(str(struct_by_id[struct_id].get('name', 'Struct')))}Schema"
        return "z.record(z.string(), z.unknown())"
    if kind == "object_ref":
        object_id = str(type_desc.get("target_object_id", ""))
        if object_id in object_by_id:
            return f"{_pascal_case(str(object_by_id[object_id].get('name', 'Object')))}RefSchema"
        return "z.record(z.string(), z.unknown())"
    if kind == "list":
        element = type_desc.get("element", {}) if isinstance(type_desc.get("element"), dict) else {}
        return f"z.array({_zod_expr_for_descriptor(element, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id)})"
    return "z.unknown()"


def _render_property(
    field: Dict[str, Any],
    *,
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> str:
    name = _camel_case(str(field.get("name", "field")))
    type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
    ts_type = _ts_type_for_descriptor(type_desc, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id)
    optional = "?" if not _is_required(field) else ""
    return f"  {name}{optional}: {ts_type};"


def _render_zod_property(
    field: Dict[str, Any],
    *,
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> str:
    name = _camel_case(str(field.get("name", "field")))
    type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
    expr = _zod_expr_for_descriptor(type_desc, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id)
    if not _is_required(field):
        expr = f"{expr}.optional()"
    return f"  {name}: {expr},"


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


def _render_action_contracts(ir: Dict[str, Any]) -> str:
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}
    struct_by_id = {item["id"]: item for item in ir.get("structs", []) if isinstance(item, dict) and "id" in item}

    lines: List[str] = ["// GENERATED FILE: do not edit directly.", "", "import type {", "  " + ",\n  ".join(sorted({
        f"{_pascal_case(str(item.get('name', 'Object')))}Ref" for item in ir.get("objects", []) if isinstance(item, dict)
    } | {
        _pascal_case(str(item.get("name", "Struct"))) for item in ir.get("structs", []) if isinstance(item, dict)
    } | {
        _pascal_case(str(item.get("name", "CustomType"))) for item in ir.get("types", []) if isinstance(item, dict)
    })) if (ir.get("objects") or ir.get("structs") or ir.get("types")) else "", "} from './domain';", ""]

    for shape in sorted(ir.get("action_inputs", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(shape, dict):
            continue
        name = _pascal_case(str(shape.get("name", "ActionInput")))
        lines.append(f"export interface {name} {{")
        for field in list(shape.get("fields", [])):
            if isinstance(field, dict):
                lines.append(_render_property(field, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id))
        lines.append("}")
        lines.append("")

    for shape in sorted(ir.get("action_outputs", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(shape, dict):
            continue
        name = _pascal_case(str(shape.get("name", "ActionOutput")))
        lines.append(f"export interface {name} {{")
        for field in list(shape.get("fields", [])):
            if isinstance(field, dict):
                lines.append(_render_property(field, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id))
        lines.append("}")
        lines.append("")

    return "\n".join(lines).replace("import type {\n  \n} from './domain';\n\n", "")


def _render_event_contracts(ir: Dict[str, Any]) -> str:
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}
    output_by_id = {item["id"]: item for item in ir.get("action_outputs", []) if isinstance(item, dict) and "id" in item}
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}
    struct_by_id = {item["id"]: item for item in ir.get("structs", []) if isinstance(item, dict) and "id" in item}

    lines: List[str] = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import type {",
        "  " + ",\n  ".join(sorted({
            f"{_pascal_case(str(item.get('name', 'Object')))}Ref" for item in ir.get("objects", []) if isinstance(item, dict)
        } | {
            f"{_pascal_case(str(item.get('name', 'Object')))}State" for item in ir.get("objects", []) if isinstance(item, dict) and item.get("states")
        })),
        "} from './domain';",
        "import type {",
        "  " + ",\n  ".join(sorted({_pascal_case(str(item.get("name", "Shape"))) for item in ir.get("action_outputs", []) if isinstance(item, dict)})),
        "} from './actions';",
        "",
    ]

    for event in sorted(ir.get("events", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(event, dict):
            continue
        kind = str(event.get("kind", ""))
        event_name = _pascal_case(str(event.get("name", "Event")))
        if kind == "signal":
            lines.append(f"export interface {event_name} {{")
            for field in list(event.get("fields", [])):
                if isinstance(field, dict):
                    lines.append(_render_property(field, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id))
            lines.append("}")
            lines.append("")
        elif kind == "action_output":
            output_id = str(event.get("output_shape_id", ""))
            alias = _pascal_case(str(output_by_id.get(output_id, {}).get("name", event_name)))
            lines.append(f"export type {event_name} = {alias};")
            lines.append("")
        elif kind == "transition":
            object_id = str(event.get("object_id", ""))
            obj = object_by_id.get(object_id, {})
            obj_name = _pascal_case(str(obj.get("name", "Object")))
            lines.append(f"export interface {event_name} {{")
            lines.append(f"  object: {obj_name}Ref;")
            lines.append(f"  fromState: {obj_name}State;")
            lines.append(f"  toState: {obj_name}State;")
            lines.append("}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


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


def _render_query_filters(ir: Dict[str, Any]) -> str:
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}
    struct_by_id = {item["id"]: item for item in ir.get("structs", []) if isinstance(item, dict) and "id" in item}

    lines: List[str] = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import type {",
        "  " + ",\n  ".join(sorted({
            f"{_pascal_case(str(item.get('name', 'Object')))}Ref" for item in ir.get("objects", []) if isinstance(item, dict)
        } | {
            f"{_pascal_case(str(item.get('name', 'Object')))}State" for item in ir.get("objects", []) if isinstance(item, dict) and item.get("states")
        })),
        "} from './domain';",
        "",
        "export interface BaseFilter<T> {",
        "  eq?: T;",
        "  in?: T[];",
        "  contains?: T extends string ? string : never;",
        "  gte?: T;",
        "  lte?: T;",
        "}",
        "",
    ]

    for contract in sorted(ir.get("query_contracts", []), key=lambda item: str(item.get("object_id", ""))):
        if not isinstance(contract, dict):
            continue
        object_id = str(contract.get("object_id", ""))
        obj = object_by_id.get(object_id, {})
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        fields_by_id = _field_index(list(obj.get("fields", [])))

        lines.append(f"export interface {obj_name}QueryFilter {{")
        for item in list(contract.get("filters", [])):
            if not isinstance(item, dict):
                continue
            field_id = str(item.get("field_id", ""))
            field_name = _camel_case(str(item.get("field_name", "field")))
            if field_id == "__current_state__":
                ts_type = f"{obj_name}State"
            else:
                field = fields_by_id.get(field_id, {})
                type_desc = field.get("type", {}) if isinstance(field, dict) and isinstance(field.get("type"), dict) else {}
                ts_type = _ts_type_for_descriptor(type_desc, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id)
            lines.append(f"  {field_name}?: BaseFilter<{ts_type}>;")
        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_persistence_contracts(ir: Dict[str, Any]) -> str:
    lines: List[str] = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import type * as Domain from './domain';",
        "import type * as Filters from './query';",
        "",
        "export interface Page<T> {",
        "  items: T[];",
        "  page: number;",
        "  size: number;",
        "  totalElements: number;",
        "  totalPages: number;",
        "}",
        "",
    ]

    object_contracts: List[Tuple[str, str]] = []
    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        id_name = f"{obj_name}Id"
        repo_name = f"{obj_name}Repository"
        object_contracts.append((obj_name, repo_name))

        lines.append(f"export interface {id_name} {{")
        for field in _object_primary_key_fields(obj):
            field_name = _camel_case(str(field.get("name", "id")))
            field_type = "string"
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            if str(type_desc.get("kind", "")) == "base":
                field_type = _ts_base_type(str(type_desc.get("name", "string")))
            lines.append(f"  {field_name}: {field_type};")
        lines.append("}")
        lines.append("")

        lines.append(f"export interface {repo_name} {{")
        lines.append(f"  list(page: number, size: number): Promise<Page<Domain.{obj_name}>>;")
        lines.append(f"  getById(id: {id_name}): Promise<Domain.{obj_name} | null>;")
        lines.append(f"  query(filter: Filters.{obj_name}QueryFilter, page: number, size: number): Promise<Page<Domain.{obj_name}>>;")
        lines.append(f"  save(item: Domain.{obj_name}): Promise<Domain.{obj_name}>;")
        lines.append("}")
        lines.append("")

    lines.append("export interface GeneratedRepositories {")
    for obj_name, repo_name in object_contracts:
        lines.append(f"  {_camel_case(obj_name)}: {repo_name};")
    lines.append("}")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_action_handlers(ir: Dict[str, Any]) -> str:
    shape_in_by_id = {item["id"]: item for item in ir.get("action_inputs", []) if isinstance(item, dict) and "id" in item}
    shape_out_by_id = {item["id"]: item for item in ir.get("action_outputs", []) if isinstance(item, dict) and "id" in item}

    lines: List[str] = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import type * as Actions from './actions';",
        "import type { GeneratedRepositories } from './persistence';",
        "import type { GeneratedEventEmitter } from './events';",
        "",
        "export interface GeneratedActionContext {",
        "  repositories: GeneratedRepositories;",
        "  eventEmitter: GeneratedEventEmitter;",
        "}",
        "",
    ]

    for action in sorted(ir.get("actions", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(action, dict):
            continue
        action_name = _pascal_case(str(action.get("name", "Action")))
        input_name = _pascal_case(str(shape_in_by_id.get(str(action.get("input_shape_id", "")), {}).get("name", "Input")))
        output_name = _pascal_case(str(shape_out_by_id.get(str(action.get("output_shape_id", "")), {}).get("name", "Output")))

        iface = f"{action_name}ActionHandler"
        lines.append(f"export interface {iface} {{")
        lines.append(f"  handle(input: Actions.{input_name}, context: GeneratedActionContext): Promise<Actions.{output_name}>;")
        lines.append("}")
        lines.append("")

        default_impl = f"{iface}Default"
        lines.append(f"export class {default_impl} implements {iface} {{")
        lines.append(f"  async handle(_input: Actions.{input_name}): Promise<Actions.{output_name}> {{")
        lines.append(
            f"    throw new Error('No implementation registered for action: {str(action.get('name', 'action'))}');"
        )
        lines.append("  }")
        lines.append("}")
        lines.append("")

    lines.append("export interface GeneratedActionHandlers {")
    for action in sorted(ir.get("actions", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(action, dict):
            continue
        action_name = _pascal_case(str(action.get("name", "Action")))
        lines.append(f"  {_camel_case(str(action.get('name', 'action')))}: {action_name}ActionHandler;")
    lines.append("}")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_event_emitter(ir: Dict[str, Any]) -> str:
    output_by_id = {item["id"]: item for item in ir.get("action_outputs", []) if isinstance(item, dict) and "id" in item}

    imported_action_types = sorted({_pascal_case(str(item.get("name", "Output"))) for item in ir.get("action_outputs", []) if isinstance(item, dict)})
    signal_types = sorted({_pascal_case(str(item.get("name", "Signal"))) for item in ir.get("events", []) if isinstance(item, dict) and str(item.get("kind", "")) == "signal"})
    transition_types = sorted({_pascal_case(str(item.get("name", "Transition"))) for item in ir.get("events", []) if isinstance(item, dict) and str(item.get("kind", "")) == "transition"})

    lines: List[str] = ["// GENERATED FILE: do not edit directly.", ""]

    if imported_action_types:
        lines.extend([
            "import type {",
            "  " + ",\n  ".join(imported_action_types),
            "} from './actions';",
            "",
        ])
    if signal_types or transition_types:
        lines.extend([
            "import type {",
            "  " + ",\n  ".join(signal_types + transition_types),
            "} from './event-contracts';",
            "",
        ])

    lines.append("export interface GeneratedEventEmitter {")
    for event in sorted(ir.get("events", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(event, dict):
            continue
        event_name = _pascal_case(str(event.get("name", "Event")))
        kind = str(event.get("kind", ""))
        event_type = event_name
        if kind == "action_output":
            shape_id = str(event.get("output_shape_id", ""))
            event_type = _pascal_case(str(output_by_id.get(shape_id, {}).get("name", event_name)))
        lines.append(f"  emit{event_name}(event: {event_type}): Promise<void>;")
    lines.append("}")
    lines.append("")

    lines.append("export class GeneratedEventEmitterNoOp implements GeneratedEventEmitter {")
    for event in sorted(ir.get("events", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(event, dict):
            continue
        event_name = _pascal_case(str(event.get("name", "Event")))
        kind = str(event.get("kind", ""))
        event_type = event_name
        if kind == "action_output":
            shape_id = str(event.get("output_shape_id", ""))
            event_type = _pascal_case(str(output_by_id.get(shape_id, {}).get("name", event_name)))
        lines.append(f"  async emit{event_name}(_event: {event_type}): Promise<void> {{")
        lines.append("    return;")
        lines.append("  }")
    lines.append("}")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_action_service(ir: Dict[str, Any]) -> str:
    action_input_by_id = {item["id"]: item for item in ir.get("action_inputs", []) if isinstance(item, dict) and "id" in item}
    action_output_by_id = {item["id"]: item for item in ir.get("action_outputs", []) if isinstance(item, dict) and "id" in item}

    lines: List[str] = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import type * as Actions from './actions';",
        "import type { GeneratedActionContext, GeneratedActionHandlers } from './action-handlers';",
        "import type { GeneratedEventEmitter } from './events';",
        "",
        "export class GeneratedActionExecutionService {",
        "  constructor(",
        "    private readonly handlers: GeneratedActionHandlers,",
        "    private readonly eventEmitter: GeneratedEventEmitter,",
        "  ) {}",
        "",
    ]

    for action in sorted(ir.get("actions", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(action, dict):
            continue
        action_name = str(action.get("name", "action"))
        pascal = _pascal_case(action_name)
        camel = _camel_case(action_name)
        input_name = _pascal_case(str(action_input_by_id.get(str(action.get("input_shape_id", "")), {}).get("name", "Input")))
        output_name = _pascal_case(str(action_output_by_id.get(str(action.get("output_shape_id", "")), {}).get("name", "Output")))

        lines.append(f"  async {camel}(input: Actions.{input_name}, context: GeneratedActionContext): Promise<Actions.{output_name}> {{")
        lines.append(f"    const output = await this.handlers.{camel}.handle(input, context);")
        lines.append(f"    await this.eventEmitter.emit{output_name}(output);")
        lines.append("    return output;")
        lines.append("  }")
        lines.append("")

    lines.append("}")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_action_routes(ir: Dict[str, Any]) -> str:
    action_input_by_id = {item["id"]: item for item in ir.get("action_inputs", []) if isinstance(item, dict) and "id" in item}

    lines: List[str] = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import { Router, type Request, type Response, type NextFunction } from 'express';",
        "import { GeneratedActionExecutionService } from './action-service';",
        "import type { GeneratedActionContext } from './action-handlers';",
        "import * as Schemas from './validation';",
        "",
        "export function buildGeneratedActionRouter(",
        "  service: GeneratedActionExecutionService,",
        "  context: GeneratedActionContext,",
        "): Router {",
        "  const router = Router();",
        "",
    ]

    for action in sorted(ir.get("actions", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(action, dict):
            continue
        action_name = str(action.get("name", "action"))
        camel = _camel_case(action_name)
        input_name = _pascal_case(str(action_input_by_id.get(str(action.get("input_shape_id", "")), {}).get("name", "Input")))
        lines.append(f"  router.post('/actions/{action_name}', async (req: Request, res: Response, next: NextFunction) => {{")
        lines.append(f"    const parsed = Schemas.{input_name}Schema.safeParse(req.body ?? {{}});")
        lines.append("    if (!parsed.success) {")
        lines.append("      res.status(400).json({ error: 'invalid_request', details: parsed.error.format() });")
        lines.append("      return;")
        lines.append("    }")
        lines.append("    try {")
        lines.append(f"      const output = await service.{camel}(parsed.data, context);")
        lines.append("      res.json(output);")
        lines.append("    } catch (error) {")
        lines.append("      next(error);")
        lines.append("    }")
        lines.append("  });")
        lines.append("")

    lines.extend(["  return router;", "}", ""])
    return "\n".join(lines).rstrip() + "\n"


def _extract_path_params(path: str) -> List[str]:
    return [match.group(1) for match in re.finditer(r"\{([^{}]+)\}", path)]


def _express_path(path: str) -> str:
    return re.sub(r"\{([^{}]+)\}", r":\1", path)


def _render_query_routes(ir: Dict[str, Any]) -> str:
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}

    lines: List[str] = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import { Router, type Request, type Response, type NextFunction } from 'express';",
        "import type { GeneratedRepositories } from './persistence';",
        "import type * as Filters from './query';",
        "",
        "function parsePage(value: unknown, fallback: number): number {",
        "  const n = Number(value);",
        "  if (!Number.isFinite(n) || n < 0) return fallback;",
        "  return Math.trunc(n);",
        "}",
        "",
        "export function buildGeneratedQueryRouter(repositories: GeneratedRepositories): Router {",
        "  const router = Router();",
        "",
    ]

    for contract in sorted(ir.get("query_contracts", []), key=lambda item: str(item.get("object_id", ""))):
        if not isinstance(contract, dict):
            continue
        object_id = str(contract.get("object_id", ""))
        obj = object_by_id.get(object_id, {})
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        repo_prop = _camel_case(obj_name)
        filter_type = f"Filters.{obj_name}QueryFilter"

        paths = contract.get("paths", {}) if isinstance(contract.get("paths"), dict) else {}
        list_path = str(paths.get("list", f"/{_pluralize(_snake_case(obj_name))}"))
        get_by_id_path = str(paths.get("get_by_id", f"/{_pluralize(_snake_case(obj_name))}/{{id}}"))
        typed_query_path = str(paths.get("typed_query", f"/{_pluralize(_snake_case(obj_name))}/query"))

        default_size = int(contract.get("pageable", {}).get("default_size", 20))

        lines.append(f"  router.get('{_express_path(list_path)}', async (req: Request, res: Response, next: NextFunction) => {{")
        lines.append("    try {")
        lines.append("      const page = parsePage(req.query.page, 0);")
        lines.append(f"      const size = parsePage(req.query.size, {default_size});")
        lines.append(f"      const result = await repositories.{repo_prop}.list(page, size);")
        lines.append("      res.json(result);")
        lines.append("    } catch (error) {")
        lines.append("      next(error);")
        lines.append("    }")
        lines.append("  });")
        lines.append("")

        params = _extract_path_params(get_by_id_path)
        lines.append(f"  router.get('{_express_path(get_by_id_path)}', async (req: Request, res: Response, next: NextFunction) => {{")
        lines.append("    try {")
        if params:
            lines.append("      const id = {")
            for param in params:
                lines.append(f"        {_camel_case(param)}: String(req.params['{param}']),")
            lines.append("      };")
        else:
            lines.append("      const id = { id: String(req.params.id) };")
        lines.append(f"      const item = await repositories.{repo_prop}.getById(id);")
        lines.append("      if (!item) {")
        lines.append("        res.status(404).json({ error: 'not_found' });")
        lines.append("        return;")
        lines.append("      }")
        lines.append("      res.json(item);")
        lines.append("    } catch (error) {")
        lines.append("      next(error);")
        lines.append("    }")
        lines.append("  });")
        lines.append("")

        lines.append(f"  router.post('{_express_path(typed_query_path)}', async (req: Request, res: Response, next: NextFunction) => {{")
        lines.append("    try {")
        lines.append("      const page = parsePage(req.query.page, 0);")
        lines.append(f"      const size = parsePage(req.query.size, {default_size});")
        lines.append(f"      const filter = (req.body ?? {{}}) as {filter_type};")
        lines.append(f"      const result = await repositories.{repo_prop}.query(filter, page, size);")
        lines.append("      res.json(result);")
        lines.append("    } catch (error) {")
        lines.append("      next(error);")
        lines.append("    }")
        lines.append("  });")
        lines.append("")

    lines.extend(["  return router;", "}", ""])
    return "\n".join(lines).rstrip() + "\n"


def _render_index_file(ir: Dict[str, Any]) -> str:
    lines = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import type { Application } from 'express';",
        "import { buildGeneratedActionRouter } from './action-routes';",
        "import { buildGeneratedQueryRouter } from './query-routes';",
        "import { GeneratedActionExecutionService } from './action-service';",
        "import { GeneratedEventEmitterNoOp, type GeneratedEventEmitter } from './events';",
        "import type { GeneratedActionContext, GeneratedActionHandlers } from './action-handlers';",
        "import type { GeneratedRepositories } from './persistence';",
        "",
        "export interface GeneratedMountDependencies {",
        "  repositories: GeneratedRepositories;",
        "  handlers: GeneratedActionHandlers;",
        "  eventEmitter?: GeneratedEventEmitter;",
        "}",
        "",
        "export function mountProphet(app: Application, deps: GeneratedMountDependencies): void {",
        "  const eventEmitter = deps.eventEmitter ?? new GeneratedEventEmitterNoOp();",
        "  const context: GeneratedActionContext = {",
        "    repositories: deps.repositories,",
        "    eventEmitter,",
        "  };",
        "  const service = new GeneratedActionExecutionService(deps.handlers, eventEmitter);",
        "  app.use(buildGeneratedActionRouter(service, context));",
        "  app.use(buildGeneratedQueryRouter(deps.repositories));",
        "}",
        "",
    ]
    return "\n".join(lines)


def _prisma_type_for_field(
    field: Dict[str, Any],
    *,
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
) -> Tuple[str, List[str]]:
    type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
    kind = str(type_desc.get("kind", ""))
    required = _is_required(field)

    if kind == "base":
        base_map = {
            "string": "String",
            "boolean": "Boolean",
            "int": "Int",
            "long": "Int",
            "short": "Int",
            "byte": "Int",
            "double": "Float",
            "float": "Float",
            "decimal": "Decimal",
            "datetime": "DateTime",
            "date": "DateTime",
            "duration": "String",
        }
        prisma_type = base_map.get(str(type_desc.get("name", "string")), "String")
        return (prisma_type, [])

    if kind == "custom":
        base = _resolve_custom_base(type_by_id, type_desc)
        return _prisma_type_for_field({"type": {"kind": "base", "name": base}, "cardinality": field.get("cardinality")}, type_by_id=type_by_id, object_by_id=object_by_id)

    if kind == "struct":
        return ("Json", [])

    if kind == "list":
        element = type_desc.get("element", {}) if isinstance(type_desc.get("element"), dict) else {}
        element_kind = str(element.get("kind", ""))
        if element_kind in {"base", "custom"}:
            elem_type, _ = _prisma_type_for_field({"type": element, "cardinality": {"min": 1, "max": 1}}, type_by_id=type_by_id, object_by_id=object_by_id)
            return (f"{elem_type}[]", [])
        return ("Json", [])

    if kind == "object_ref":
        target_id = str(type_desc.get("target_object_id", ""))
        target = object_by_id.get(target_id, {})
        target_name = _pascal_case(str(target.get("name", "Object")))
        target_pk = _object_primary_key_fields(target)
        if not target_pk:
            return ("String", [])
        target_pk_field = target_pk[0]
        target_pk_name = str(target_pk_field.get("name", "id"))
        fk_name = f"{str(field.get('name', 'ref'))}_{target_pk_name}"
        fk_desc = target_pk_field.get("type", {}) if isinstance(target_pk_field.get("type"), dict) else {"kind": "base", "name": "string"}
        fk_type, _ = _prisma_type_for_field({"type": fk_desc, "cardinality": {"min": 1, "max": 1}}, type_by_id=type_by_id, object_by_id=object_by_id)
        relation_line = f"  {str(field.get('name', 'ref'))} {target_name}{'' if required else '?'} @relation(fields: [{fk_name}], references: [{target_pk_name}])"
        fk_line = f"  {fk_name} {fk_type}{'' if required else '?'}"
        return ("<ref>", [fk_line, relation_line])

    return ("String", [])


def _render_prisma_schema(ir: Dict[str, Any]) -> str:
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}

    lines = [
        "// GENERATED FILE: do not edit directly.",
        "generator client {",
        "  provider = \"prisma-client-js\"",
        "}",
        "",
        "datasource db {",
        "  provider = \"postgresql\"",
        "  url      = env(\"DATABASE_URL\")",
        "}",
        "",
    ]

    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        model_name = _pascal_case(str(obj.get("name", "Object")))
        lines.append(f"model {model_name} {{")

        extra_lines: List[str] = []
        primary_ids = set(obj.get("keys", {}).get("primary", {}).get("field_ids", []))
        for field in list(obj.get("fields", [])):
            if not isinstance(field, dict):
                continue
            field_name = str(field.get("name", "field"))
            field_type, relation_lines = _prisma_type_for_field(field, type_by_id=type_by_id, object_by_id=object_by_id)
            if field_type != "<ref>":
                required = _is_required(field)
                suffix = "" if required else "?"
                annotations: List[str] = []
                if str(field.get("id", "")) in primary_ids and len(primary_ids) == 1:
                    annotations.append("@id")
                lines.append(f"  {field_name} {field_type}{suffix}{(' ' + ' '.join(annotations)) if annotations else ''}")
            extra_lines.extend(relation_lines)

        for relation_line in extra_lines:
            lines.append(relation_line)

        if len(primary_ids) > 1:
            by_id = _field_index(list(obj.get("fields", [])))
            cols = [by_id[item]["name"] for item in obj.get("keys", {}).get("primary", {}).get("field_ids", []) if item in by_id]
            lines.append(f"  @@id([{', '.join(cols)}])")

        display_ids = list(obj.get("keys", {}).get("display", {}).get("field_ids", []))
        if display_ids:
            by_id = _field_index(list(obj.get("fields", [])))
            cols = [by_id[item]["name"] for item in display_ids if item in by_id]
            if cols:
                lines.append(f"  @@index([{', '.join(cols)}], map: \"idx_{_snake_case(model_name)}_display\")")

        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_prisma_adapter(ir: Dict[str, Any]) -> str:
    lines = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import type * as Domain from './domain';",
        "import type * as Filters from './query';",
        "import type * as Persistence from './persistence';",
        "",
        "export class PrismaGeneratedRepositories implements Persistence.GeneratedRepositories {",
    ]

    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        repo_name = f"{obj_name}PrismaRepository"
        lines.append(f"  {_camel_case(obj_name)}: Persistence.{obj_name}Repository = new {repo_name}();")
    lines.append("}")
    lines.append("")

    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        lines.append(f"class {obj_name}PrismaRepository implements Persistence.{obj_name}Repository {{")
        lines.append(f"  async list(_page: number, _size: number): Promise<Persistence.Page<Domain.{obj_name}>> {{")
        lines.append("    throw new Error('Prisma adapter scaffolding generated; implement repository binding logic.');")
        lines.append("  }")
        lines.append(f"  async getById(_id: Persistence.{obj_name}Id): Promise<Domain.{obj_name} | null> {{")
        lines.append("    throw new Error('Prisma adapter scaffolding generated; implement repository binding logic.');")
        lines.append("  }")
        lines.append(f"  async query(_filter: Filters.{obj_name}QueryFilter, _page: number, _size: number): Promise<Persistence.Page<Domain.{obj_name}>> {{")
        lines.append("    throw new Error('Prisma adapter scaffolding generated; implement repository binding logic.');")
        lines.append("  }")
        lines.append(f"  async save(_item: Domain.{obj_name}): Promise<Domain.{obj_name}> {{")
        lines.append("    throw new Error('Prisma adapter scaffolding generated; implement repository binding logic.');")
        lines.append("  }")
        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _typeorm_column_type(field: Dict[str, Any], type_by_id: Dict[str, Dict[str, Any]]) -> str:
    type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
    kind = str(type_desc.get("kind", ""))
    if kind == "base":
        base = str(type_desc.get("name", "string"))
    elif kind == "custom":
        base = _resolve_custom_base(type_by_id, type_desc)
    elif kind == "list":
        return "simple-json"
    elif kind == "struct":
        return "simple-json"
    elif kind == "object_ref":
        return "varchar"
    else:
        return "varchar"

    mapping = {
        "string": "varchar",
        "boolean": "boolean",
        "int": "integer",
        "long": "integer",
        "short": "integer",
        "byte": "integer",
        "double": "double precision",
        "float": "double precision",
        "decimal": "numeric",
        "datetime": "timestamp",
        "date": "date",
        "duration": "varchar",
    }
    return mapping.get(base, "varchar")


def _render_typeorm_entities(ir: Dict[str, Any]) -> str:
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}

    lines = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import { Column, Entity, JoinColumn, ManyToOne, PrimaryColumn } from 'typeorm';",
        "",
    ]

    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        table_name = _pluralize(_snake_case(str(obj.get("name", "object"))))
        primary_ids = set(obj.get("keys", {}).get("primary", {}).get("field_ids", []))

        lines.append(f"@Entity('{table_name}')")
        lines.append(f"export class {obj_name}Entity {{")

        for field in list(obj.get("fields", [])):
            if not isinstance(field, dict):
                continue
            field_name_raw = str(field.get("name", "field"))
            field_name = _camel_case(field_name_raw)
            nullable = "true" if not _is_required(field) else "false"
            col_type = _typeorm_column_type(field, type_by_id)
            is_primary = str(field.get("id", "")) in primary_ids

            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            if str(type_desc.get("kind", "")) == "object_ref":
                target_id = str(type_desc.get("target_object_id", ""))
                target_obj = object_by_id.get(target_id, {})
                target_name = _pascal_case(str(target_obj.get("name", "Object")))
                target_pk_fields = _object_primary_key_fields(target_obj)
                target_pk = target_pk_fields[0] if target_pk_fields else {"name": "id"}
                fk_name = f"{field_name}{_pascal_case(str(target_pk.get('name', 'id')))}"
                lines.append(f"  @Column({{ type: '{col_type}', nullable: {nullable}, name: '{_snake_case(fk_name)}' }})")
                lines.append(f"  {fk_name}!: string;")
                lines.append("")
                lines.append(f"  @ManyToOne(() => {target_name}Entity, {{ nullable: {nullable} }})")
                lines.append(
                    f"  @JoinColumn({{ name: '{_snake_case(fk_name)}', referencedColumnName: '{_camel_case(str(target_pk.get('name', 'id')))}' }})"
                )
                lines.append(f"  {field_name}!: {target_name}Entity;")
                lines.append("")
                continue

            if is_primary:
                lines.append(f"  @PrimaryColumn({{ type: '{col_type}', name: '{field_name_raw}' }})")
            else:
                lines.append(f"  @Column({{ type: '{col_type}', nullable: {nullable}, name: '{field_name_raw}' }})")
            lines.append(f"  {field_name}{'?' if not _is_required(field) else ''}: {_ts_base_type('string') if col_type == 'varchar' else 'unknown'};")
            lines.append("")

        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_typeorm_adapter(ir: Dict[str, Any]) -> str:
    lines = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import type * as Domain from './domain';",
        "import type * as Filters from './query';",
        "import type * as Persistence from './persistence';",
        "",
        "export class TypeOrmGeneratedRepositories implements Persistence.GeneratedRepositories {",
    ]
    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        repo_name = f"{obj_name}TypeOrmRepository"
        lines.append(f"  {_camel_case(obj_name)}: Persistence.{obj_name}Repository = new {repo_name}();")
    lines.append("}")
    lines.append("")

    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        lines.append(f"class {obj_name}TypeOrmRepository implements Persistence.{obj_name}Repository {{")
        lines.append(f"  async list(_page: number, _size: number): Promise<Persistence.Page<Domain.{obj_name}>> {{")
        lines.append("    throw new Error('TypeORM adapter scaffolding generated; implement repository binding logic.');")
        lines.append("  }")
        lines.append(f"  async getById(_id: Persistence.{obj_name}Id): Promise<Domain.{obj_name} | null> {{")
        lines.append("    throw new Error('TypeORM adapter scaffolding generated; implement repository binding logic.');")
        lines.append("  }")
        lines.append(f"  async query(_filter: Filters.{obj_name}QueryFilter, _page: number, _size: number): Promise<Persistence.Page<Domain.{obj_name}>> {{")
        lines.append("    throw new Error('TypeORM adapter scaffolding generated; implement repository binding logic.');")
        lines.append("  }")
        lines.append(f"  async save(_item: Domain.{obj_name}): Promise<Domain.{obj_name}> {{")
        lines.append("    throw new Error('TypeORM adapter scaffolding generated; implement repository binding logic.');")
        lines.append("  }")
        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_node_package_json(stack: StackSpec) -> str:
    deps = {
        "express": "^4.19.2",
        "zod": "^3.23.8",
    }
    if stack.orm == "prisma":
        deps["@prisma/client"] = "^5.22.0"
    if stack.orm == "typeorm":
        deps["typeorm"] = "^0.3.20"
        deps["reflect-metadata"] = "^0.2.2"

    payload = {
        "name": "prophet-generated-node-express",
        "private": True,
        "type": "module",
        "scripts": {
            "build": "tsc -p tsconfig.json",
            "check": "tsc -p tsconfig.json --noEmit",
        },
        "dependencies": deps,
        "devDependencies": {
            "@types/express": "^4.17.21",
            "typescript": "^5.6.3",
        },
    }
    return "// GENERATED FILE: do not edit directly.\n" + json.dumps(payload, indent=2, sort_keys=False) + "\n"


def _render_node_tsconfig() -> str:
    payload = {
        "compilerOptions": {
            "target": "ES2022",
            "module": "NodeNext",
            "moduleResolution": "NodeNext",
            "strict": True,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "forceConsistentCasingInFileNames": True,
            "outDir": "dist",
        },
        "include": ["src/**/*.ts"],
    }
    return "// GENERATED FILE: do not edit directly.\n" + json.dumps(payload, indent=2, sort_keys=False) + "\n"


def _render_detection_report(cfg: Dict[str, Any]) -> Optional[str]:
    autodetect_payload = cfg.get("_autodetect")
    if not isinstance(autodetect_payload, dict):
        return None
    return json.dumps(autodetect_payload, indent=2, sort_keys=False) + "\n"


@dataclass(frozen=True)
class NodeExpressDeps:
    cfg_get: Callable[[Dict[str, Any], List[str], Any], Any]
    resolve_stack_spec: Callable[[Dict[str, Any]], StackSpec]
    render_sql: Callable[[IRReader], str]
    render_openapi: Callable[[IRReader], str]
    toolchain_version: str


def generate_outputs(context: GenerationContext, deps: NodeExpressDeps) -> Dict[str, str]:
    cfg = context.cfg
    out_dir = str(deps.cfg_get(cfg, ["generation", "out_dir"], "gen"))
    stack = deps.resolve_stack_spec(cfg)
    targets = deps.cfg_get(cfg, ["generation", "targets"], list(stack.default_targets))
    if not isinstance(targets, list):
        targets = list(stack.default_targets)

    ir = context.ir_reader.as_dict()
    outputs: Dict[str, str] = {}

    if "sql" in targets:
        outputs[f"{out_dir}/sql/schema.sql"] = deps.render_sql(context.ir_reader)

    if "openapi" in targets:
        outputs[f"{out_dir}/openapi/openapi.yaml"] = deps.render_openapi(context.ir_reader)

    node_prefix = f"{out_dir}/node-express"
    if "node_express" in targets:
        outputs[f"{node_prefix}/package.json"] = _render_node_package_json(stack)
        outputs[f"{node_prefix}/tsconfig.json"] = _render_node_tsconfig()
        outputs[f"{node_prefix}/src/generated/domain.ts"] = _render_domain_types(ir)
        outputs[f"{node_prefix}/src/generated/actions.ts"] = _render_action_contracts(ir)
        outputs[f"{node_prefix}/src/generated/event-contracts.ts"] = _render_event_contracts(ir)
        outputs[f"{node_prefix}/src/generated/validation.ts"] = _render_validation(ir)
        outputs[f"{node_prefix}/src/generated/query.ts"] = _render_query_filters(ir)
        outputs[f"{node_prefix}/src/generated/persistence.ts"] = _render_persistence_contracts(ir)
        outputs[f"{node_prefix}/src/generated/action-handlers.ts"] = _render_action_handlers(ir)
        outputs[f"{node_prefix}/src/generated/events.ts"] = _render_event_emitter(ir)
        outputs[f"{node_prefix}/src/generated/action-service.ts"] = _render_action_service(ir)
        outputs[f"{node_prefix}/src/generated/action-routes.ts"] = _render_action_routes(ir)
        outputs[f"{node_prefix}/src/generated/query-routes.ts"] = _render_query_routes(ir)
        outputs[f"{node_prefix}/src/generated/index.ts"] = _render_index_file(ir)

    if stack.orm == "prisma" and "prisma" in targets:
        outputs[f"{node_prefix}/prisma/schema.prisma"] = _render_prisma_schema(ir)
        outputs[f"{node_prefix}/src/generated/prisma-adapters.ts"] = _render_prisma_adapter(ir)

    if stack.orm == "typeorm" and "typeorm" in targets:
        outputs[f"{node_prefix}/src/generated/typeorm-entities.ts"] = _render_typeorm_entities(ir)
        outputs[f"{node_prefix}/src/generated/typeorm-adapters.ts"] = _render_typeorm_adapter(ir)

    extension_hooks = []
    for action in sorted(context.ir_reader.action_contracts(), key=lambda item: item.name):
        action_name = action.name
        handler_name = f"{_pascal_case(action_name)}ActionHandler"
        extension_hooks.append(
            {
                "kind": "action_handler",
                "action_id": action.id,
                "action_name": action_name,
                "typescript_interface": f"generated.{handler_name}",
                "default_implementation": f"generated.{handler_name}Default",
            }
        )

    outputs[f"{out_dir}/manifest/extension-hooks.json"] = json.dumps(
        {
            "schema_version": 1,
            "stack": stack.id,
            "hooks": extension_hooks,
        },
        indent=2,
        sort_keys=False,
    ) + "\n"

    detection_report = _render_detection_report(cfg)
    if detection_report is not None:
        outputs[f"{out_dir}/manifest/node-autodetect.json"] = detection_report

    manifest_rel = f"{out_dir}/manifest/generated-files.json"
    hashed_outputs = {
        rel: hashlib.sha256(content.encode("utf-8")).hexdigest()
        for rel, content in sorted(outputs.items())
    }
    manifest_payload = {
        "schema_version": 1,
        "toolchain_version": deps.toolchain_version,
        "stack": {
            "id": stack.id,
            "language": stack.language,
            "framework": stack.framework,
            "orm": stack.orm,
        },
        "ir_hash": context.ir_reader.ir_hash,
        "outputs": [{"path": rel, "sha256": digest} for rel, digest in sorted(hashed_outputs.items())],
    }
    outputs[manifest_rel] = json.dumps(manifest_payload, indent=2, sort_keys=False) + "\n"

    return outputs
