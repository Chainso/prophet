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

_TS_FROM_SPEC_RE = re.compile(r"(from\s+['\"])(\.\.?/[^'\"]+)(['\"])")


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


def _append_js_extensions_to_relative_imports(ts_source: str) -> str:
    def repl(match: re.Match[str]) -> str:
        prefix, module_path, suffix = match.groups()
        if module_path.endswith((".js", ".mjs", ".cjs", ".json", ".node")):
            return match.group(0)
        return f"{prefix}{module_path}.js{suffix}"

    return _TS_FROM_SPEC_RE.sub(repl, ts_source)


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
    action_output_names = sorted(
        {
            _pascal_case(str(item.get("name", "Shape")))
            for item in ir.get("action_outputs", [])
            if isinstance(item, dict)
        }
    )
    action_output_aliases = {name: f"{name}ActionOutput" for name in action_output_names}

    lines: List[str] = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import type {",
        "  " + ",\n  ".join(sorted({
            f"{_pascal_case(str(item.get('name', 'Object')))}Ref" for item in ir.get("objects", []) if isinstance(item, dict)
        })),
        "} from './domain';",
    ]
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
            aliased_import = action_output_aliases.get(alias, alias)
            lines.append(f"export type {event_name} = {aliased_import};")
            lines.append("")
        elif kind == "transition":
            object_id = str(event.get("object_id", ""))
            obj = object_by_id.get(object_id, {})
            obj_name = _pascal_case(str(obj.get("name", "Object")))
            lines.append(f"export interface {event_name} {{")
            lines.append(f"  object: {obj_name}Ref;")
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
    lines: List[str] = ["// GENERATED FILE: do not edit directly.", ""]

    domain_imports = sorted(
        {
            f"{_pascal_case(str(item.get('name', 'Object')))}Ref"
            for item in ir.get("objects", [])
            if isinstance(item, dict)
        }
        | {
            f"{_pascal_case(str(item.get('name', 'Object')))}State"
            for item in ir.get("objects", [])
            if isinstance(item, dict) and item.get("states")
        }
    )
    if domain_imports:
        lines.extend(
            [
                "import type {",
                "  " + ",\n  ".join(domain_imports),
                "} from './domain';",
                "",
            ]
        )

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
            ops = [str(op) for op in item.get("operators", []) if isinstance(op, str)]
            lines.append(f"  {field_name}?: {{")
            if "eq" in ops:
                lines.append(f"    eq?: {ts_type};")
            if "in" in ops:
                lines.append(f"    in?: {ts_type}[];")
            if "contains" in ops:
                lines.append("    contains?: string;")
            if "gte" in ops:
                lines.append(f"    gte?: {ts_type};")
            if "lte" in ops:
                lines.append(f"    lte?: {ts_type};")
            lines.append("  };")
        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_persistence_contracts(ir: Dict[str, Any]) -> str:
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}
    struct_by_id = {item["id"]: item for item in ir.get("structs", []) if isinstance(item, dict) and "id" in item}

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
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            field_type = _ts_type_for_descriptor(
                type_desc,
                type_by_id=type_by_id,
                object_by_id=object_by_id,
                struct_by_id=struct_by_id,
            )
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
        pk_fields = _object_primary_key_fields(obj)
        pk_props = [_camel_case(str(field.get("name", "id"))) for field in pk_fields]

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
        if params and len(params) == 1 and params[0] == "id" and len(pk_props) == 1:
            lines.append("      const id = {")
            lines.append(f"        {pk_props[0]}: String(req.params['id']),")
            lines.append("      };")
        elif params:
            lines.append("      const id = {")
            for idx, param in enumerate(params):
                prop = _camel_case(param)
                if idx < len(pk_props):
                    prop = pk_props[idx]
                lines.append(f"        {prop}: String(req.params['{param}']),")
            lines.append("      };")
        else:
            if pk_props:
                lines.append("      const id = {")
                lines.append(f"        {pk_props[0]}: String(req.params.id),")
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


def _prisma_scalar_type_for_descriptor(type_desc: Dict[str, Any], type_by_id: Dict[str, Dict[str, Any]]) -> str:
    kind = str(type_desc.get("kind", ""))
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
        return base_map.get(str(type_desc.get("name", "string")), "String")
    if kind == "custom":
        base = _resolve_custom_base(type_by_id, type_desc)
        return _prisma_scalar_type_for_descriptor({"kind": "base", "name": base}, type_by_id)
    return "String"


def _prisma_column_type_for_field(
    field: Dict[str, Any],
    type_by_id: Dict[str, Dict[str, Any]],
    *,
    provider: str,
) -> str:
    type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
    kind = str(type_desc.get("kind", ""))
    if kind in {"base", "custom"}:
        return _prisma_scalar_type_for_descriptor(type_desc, type_by_id)
    if kind == "struct":
        return "Json" if provider == "postgresql" else "String"
    if kind == "list":
        element = type_desc.get("element", {}) if isinstance(type_desc.get("element"), dict) else {}
        if provider == "postgresql" and str(element.get("kind", "")) in {"base", "custom"}:
            return f"{_prisma_scalar_type_for_descriptor(element, type_by_id)}[]"
        return "String"
    return "String"


def _prisma_ref_columns(
    field: Dict[str, Any],
    *,
    object_by_id: Dict[str, Dict[str, Any]],
    type_by_id: Dict[str, Dict[str, Any]],
) -> List[Tuple[str, str, str]]:
    type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
    target_id = str(type_desc.get("target_object_id", ""))
    target_obj = object_by_id.get(target_id, {})
    target_pk_fields = _object_primary_key_fields(target_obj)
    field_name = str(field.get("name", "ref"))

    result: List[Tuple[str, str, str]] = []
    for pk_field in target_pk_fields:
        pk_name = str(pk_field.get("name", "id"))
        pk_desc = pk_field.get("type", {}) if isinstance(pk_field.get("type"), dict) else {"kind": "base", "name": "string"}
        result.append((f"{field_name}_{pk_name}", _prisma_scalar_type_for_descriptor(pk_desc, type_by_id), pk_name))
    return result


def _render_prisma_schema(ir: Dict[str, Any], *, provider: str) -> str:
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}
    target_field_names_by_id: Dict[str, set[str]] = {}
    for obj in ir.get("objects", []):
        if not isinstance(obj, dict):
            continue
        oid = str(obj.get("id", ""))
        target_field_names_by_id[oid] = {
            str(field.get("name", "field"))
            for field in obj.get("fields", [])
            if isinstance(field, dict)
        }
        target_field_names_by_id[oid].add("current_state")

    lines = [
        "// GENERATED FILE: do not edit directly.",
        "generator client {",
        "  provider = \"prisma-client-js\"",
        "}",
        "",
        "datasource db {",
        f"  provider = \"{provider}\"",
        "  url      = env(\"DATABASE_URL\")",
        "}",
        "",
    ]
    inbound_relations: Dict[str, List[Tuple[str, str, str]]] = {}
    source_relation_name: Dict[Tuple[str, str], str] = {}
    used_names_by_target: Dict[str, set[str]] = {
        key: set(value) for key, value in target_field_names_by_id.items()
    }
    for source_obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(source_obj, dict):
            continue
        source_object_id = str(source_obj.get("id", ""))
        source_model_name = _pascal_case(str(source_obj.get("name", "Object")))
        for field in source_obj.get("fields", []):
            if not isinstance(field, dict):
                continue
            field_id = str(field.get("id", ""))
            field_name = str(field.get("name", "field"))
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            if str(type_desc.get("kind", "")) != "object_ref":
                continue
            target_object_id = str(type_desc.get("target_object_id", ""))
            target_obj = object_by_id.get(target_object_id, {})
            target_model_name = _pascal_case(str(target_obj.get("name", "Object")))
            relation_name = f"{source_model_name}_{field_name}_{target_model_name}"
            source_relation_name[(source_object_id, field_id)] = relation_name

            back_base = f"{_camel_case(_pluralize(source_model_name))}By{_pascal_case(field_name)}"
            used_names = used_names_by_target.setdefault(target_object_id, set())
            candidate = back_base
            suffix = 2
            while candidate in used_names:
                candidate = f"{back_base}{suffix}"
                suffix += 1
            used_names.add(candidate)
            inbound_relations.setdefault(target_object_id, []).append((candidate, source_model_name, relation_name))

    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        object_id = str(obj.get("id", ""))
        model_name = _pascal_case(str(obj.get("name", "Object")))
        lines.append(f"model {model_name} {{")

        relation_lines: List[str] = []
        primary_ids = list(obj.get("keys", {}).get("primary", {}).get("field_ids", []))
        primary_id_set = set(primary_ids)
        display_ids = set(obj.get("keys", {}).get("display", {}).get("field_ids", []))
        expanded_primary_columns: List[str] = []
        display_columns: List[str] = []
        for field in list(obj.get("fields", [])):
            if not isinstance(field, dict):
                continue
            field_id = str(field.get("id", ""))
            field_name = str(field.get("name", "field"))
            required = _is_required(field)
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            if str(type_desc.get("kind", "")) == "object_ref":
                ref_cols = _prisma_ref_columns(field, object_by_id=object_by_id, type_by_id=type_by_id)
                target_object_id = str(type_desc.get("target_object_id", ""))
                target_obj = object_by_id.get(target_object_id, {})
                target_name = _pascal_case(str(target_obj.get("name", "Object")))
                fk_cols = [item[0] for item in ref_cols]
                ref_keys = [item[2] for item in ref_cols]
                relation_name = source_relation_name.get((object_id, field_id), f"{model_name}_{field_name}_{target_name}")
                for fk_col, fk_type, _ in ref_cols:
                    lines.append(f"  {fk_col} {fk_type}{'' if required else '?'}")
                    if field_id in primary_id_set:
                        expanded_primary_columns.append(fk_col)
                    if field_id in display_ids:
                        display_columns.append(fk_col)
                relation_lines.append(
                    f"  {field_name} {target_name}{'' if required else '?'} @relation(\"{relation_name}\", fields: [{', '.join(fk_cols)}], references: [{', '.join(ref_keys)}])"
                )
                continue

            field_type = _prisma_column_type_for_field(field, type_by_id, provider=provider)
            annotations: List[str] = []
            if len(primary_ids) == 1 and primary_ids[0] == field_id:
                annotations.append("@id")
            if field_type.endswith("[]"):
                if not required:
                    annotations.append("@default([])")
                lines.append(f"  {field_name} {field_type}{(' ' + ' '.join(annotations)) if annotations else ''}")
            else:
                lines.append(f"  {field_name} {field_type}{'' if required else '?'}{(' ' + ' '.join(annotations)) if annotations else ''}")
            if field_id in primary_id_set:
                expanded_primary_columns.append(field_name)
            if field_id in display_ids:
                display_columns.append(field_name)

        if obj.get("states"):
            initial_state = next(
                (str(state.get("name", "")) for state in obj.get("states", []) if isinstance(state, dict) and bool(state.get("initial"))),
                "",
            )
            default_hint = f' @default("{initial_state}")' if initial_state else ""
            lines.append(f"  current_state String{default_hint}")

        for relation_line in relation_lines:
            lines.append(relation_line)
        for back_field, source_model, relation_name in inbound_relations.get(object_id, []):
            lines.append(f"  {back_field} {source_model}[] @relation(\"{relation_name}\")")

        if len(primary_ids) != 1 and expanded_primary_columns:
            lines.append(f"  @@id([{', '.join(expanded_primary_columns)}])")
        if display_columns:
            lines.append(f"  @@index([{', '.join(display_columns)}], map: \"idx_{_snake_case(model_name)}_display\")")

        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_prisma_adapter(ir: Dict[str, Any], *, provider: str) -> str:
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}
    struct_by_id = {item["id"]: item for item in ir.get("structs", []) if isinstance(item, dict) and "id" in item}
    query_contract_by_object_id = {
        str(item.get("object_id", "")): item
        for item in ir.get("query_contracts", [])
        if isinstance(item, dict)
    }

    lines = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import type { PrismaClient } from '@prisma/client';",
        "import type * as Domain from './domain';",
        "import type * as Filters from './query';",
        "import type * as Persistence from './persistence';",
        "",
        "function normalizePage(page: number, size: number): { page: number; size: number } {",
        "  const normalizedPage = Number.isFinite(page) && page >= 0 ? Math.trunc(page) : 0;",
        "  const normalizedSize = Number.isFinite(size) && size > 0 ? Math.trunc(size) : 20;",
        "  return { page: normalizedPage, size: normalizedSize };",
        "}",
        "",
        "function totalPages(totalElements: number, size: number): number {",
        "  if (size <= 0) return 0;",
        "  return Math.ceil(totalElements / size);",
        "}",
        "",
        "function parseJsonValue<T>(value: unknown): T | undefined {",
        "  if (value === null || value === undefined) return undefined;",
        "  if (typeof value === 'string') {",
        "    try {",
        "      return JSON.parse(value) as T;",
        "    } catch {",
        "      return undefined;",
        "    }",
        "  }",
        "  return value as T;",
        "}",
        "",
        "export class PrismaGeneratedRepositories implements Persistence.GeneratedRepositories {",
    ]
    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        lines.append(f"  {_camel_case(obj_name)}: Persistence.{obj_name}Repository;")
    lines.append("")
    lines.append("  constructor(private readonly client: PrismaClient) {")
    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        repo_name = f"{obj_name}PrismaRepository"
        lines.append(f"    this.{_camel_case(obj_name)} = new {repo_name}(client);")
    lines.append("  }")
    lines.append("}")
    lines.append("")

    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_id = str(obj.get("id", ""))
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        repo_var = _camel_case(obj_name)
        pk_fields = _object_primary_key_fields(obj)
        fields_by_id = _field_index(list(obj.get("fields", [])))
        query_contract = query_contract_by_object_id.get(obj_id, {})
        query_filters = list(query_contract.get("filters", [])) if isinstance(query_contract, dict) else []

        lines.append(f"function {repo_var}Where(filter: Filters.{obj_name}QueryFilter | undefined): any {{")
        lines.append("  if (!filter) return {};")
        lines.append("  const and: any[] = [];")
        for filter_item in query_filters:
            if not isinstance(filter_item, dict):
                continue
            field_id = str(filter_item.get("field_id", ""))
            filter_name = _camel_case(str(filter_item.get("field_name", "field")))
            operators = [str(op) for op in filter_item.get("operators", []) if isinstance(op, str)]
            lines.append(f"  const {filter_name}Filter = filter.{filter_name};")

            if field_id == "__current_state__":
                if "eq" in operators:
                    lines.append(f"  if ({filter_name}Filter?.eq !== undefined) and.push({{ current_state: {filter_name}Filter.eq }});")
                if "in" in operators:
                    lines.append(f"  if ({filter_name}Filter?.in?.length) and.push({{ current_state: {{ in: {filter_name}Filter.in }} }});")
                continue

            field = fields_by_id.get(field_id, {})
            if not field:
                continue
            field_name = str(field.get("name", "field"))
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            if str(type_desc.get("kind", "")) == "object_ref":
                ref_cols = _prisma_ref_columns(field, object_by_id=object_by_id, type_by_id=type_by_id)
                if "eq" in operators:
                    lines.append(f"  if ({filter_name}Filter?.eq !== undefined) {{")
                    where_pairs = ", ".join([f"{col}: {filter_name}Filter.eq.{_camel_case(pk_name)}" for col, _, pk_name in ref_cols])
                    lines.append(f"    and.push({{ {where_pairs} }});")
                    lines.append("  }")
                if "in" in operators:
                    lines.append(f"  if ({filter_name}Filter?.in?.length) {{")
                    lines.append("    and.push({")
                    lines.append(f"      OR: {filter_name}Filter.in.map((entry: any) => ({{")
                    for col, _, pk_name in ref_cols:
                        lines.append(f"        {col}: entry.{_camel_case(pk_name)},")
                    lines.append("      })),")
                    lines.append("    });")
                    lines.append("  }")
                continue

            if "eq" in operators:
                lines.append(f"  if ({filter_name}Filter?.eq !== undefined) and.push({{ {field_name}: {filter_name}Filter.eq }});")
            if "in" in operators:
                lines.append(f"  if ({filter_name}Filter?.in?.length) and.push({{ {field_name}: {{ in: {filter_name}Filter.in }} }});")
            if "contains" in operators:
                lines.append(
                    f"  if (typeof {filter_name}Filter?.contains === 'string' && {filter_name}Filter.contains.length > 0) "
                    f"and.push({{ {field_name}: {{ contains: {filter_name}Filter.contains }} }});"
                )
            if "gte" in operators:
                lines.append(f"  if ({filter_name}Filter?.gte !== undefined) and.push({{ {field_name}: {{ gte: {filter_name}Filter.gte }} }});")
            if "lte" in operators:
                lines.append(f"  if ({filter_name}Filter?.lte !== undefined) and.push({{ {field_name}: {{ lte: {filter_name}Filter.lte }} }});")
        lines.append("  if (and.length === 0) return {};")
        lines.append("  return { AND: and };")
        lines.append("}")
        lines.append("")

        lines.append(f"function {repo_var}IdFromDomain(item: Domain.{obj_name}): Persistence.{obj_name}Id {{")
        lines.append("  return {")
        for pk_field in pk_fields:
            pk_name = _camel_case(str(pk_field.get("name", "id")))
            lines.append(f"    {pk_name}: item.{pk_name},")
        lines.append("  };")
        lines.append("}")
        lines.append("")

        unique_parts: List[Tuple[str, str]] = []
        for pk_field in pk_fields:
            pk_name_raw = str(pk_field.get("name", "id"))
            pk_name = _camel_case(pk_name_raw)
            pk_type_desc = pk_field.get("type", {}) if isinstance(pk_field.get("type"), dict) else {}
            if str(pk_type_desc.get("kind", "")) == "object_ref":
                ref_cols = _prisma_ref_columns(pk_field, object_by_id=object_by_id, type_by_id=type_by_id)
                for col, _, ref_pk in ref_cols:
                    unique_parts.append((col, f"id.{pk_name}.{_camel_case(ref_pk)}"))
            else:
                unique_parts.append((pk_name_raw, f"id.{pk_name}"))

        lines.append(f"function {repo_var}UniqueWhere(id: Persistence.{obj_name}Id): any {{")
        if len(unique_parts) == 1:
            lines.append(f"  return {{ {unique_parts[0][0]}: {unique_parts[0][1]} }};")
        elif unique_parts:
            alias = "_".join([part[0] for part in unique_parts])
            lines.append(f"  return {{ {alias}: {{")
            for col, expr in unique_parts:
                lines.append(f"    {col}: {expr},")
            lines.append("  } };")
        else:
            lines.append("  return {};")
        lines.append("}")
        lines.append("")

        lines.append(f"function {repo_var}RowToDomain(row: any): Domain.{obj_name} {{")
        lines.append("  return {")
        for field in list(obj.get("fields", [])):
            if not isinstance(field, dict):
                continue
            field_name = str(field.get("name", "field"))
            prop_name = _camel_case(field_name)
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            required = _is_required(field)
            if str(type_desc.get("kind", "")) == "object_ref":
                ref_cols = _prisma_ref_columns(field, object_by_id=object_by_id, type_by_id=type_by_id)
                null_guard = " and ".join([f"row.{col} == null" for col, _, _ in ref_cols]) if ref_cols else "false"
                if required:
                    lines.append(f"    {prop_name}: {{")
                    for col, _, pk_name in ref_cols:
                        lines.append(f"      {_camel_case(pk_name)}: row.{col},")
                    lines.append("    },")
                else:
                    lines.append(f"    {prop_name}: {null_guard} ? undefined : {{")
                    for col, _, pk_name in ref_cols:
                        lines.append(f"      {_camel_case(pk_name)}: row.{col},")
                    lines.append("    },")
                continue
            kind = str(type_desc.get("kind", ""))
            if provider != "postgresql" and kind in {"list", "struct"}:
                ts_type = _ts_type_for_descriptor(
                    type_desc,
                    type_by_id=type_by_id,
                    object_by_id=object_by_id,
                    struct_by_id=struct_by_id,
                )
                if required:
                    if kind == "list":
                        lines.append(f"    {prop_name}: (parseJsonValue(row.{field_name}) ?? []) as any,")
                    else:
                        lines.append(f"    {prop_name}: (parseJsonValue(row.{field_name}) ?? {{}}) as any,")
                else:
                    lines.append(f"    {prop_name}: parseJsonValue(row.{field_name}) as any,")
                continue
            if required:
                lines.append(f"    {prop_name}: row.{field_name},")
            else:
                lines.append(f"    {prop_name}: row.{field_name} ?? undefined,")
        if obj.get("states"):
            lines.append("    currentState: row.current_state,")
        lines.append("  };")
        lines.append("}")
        lines.append("")

        lines.append(f"function {repo_var}DomainToRow(item: Domain.{obj_name}): any {{")
        lines.append("  return {")
        for field in list(obj.get("fields", [])):
            if not isinstance(field, dict):
                continue
            field_name = str(field.get("name", "field"))
            prop_name = _camel_case(field_name)
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            required = _is_required(field)
            if str(type_desc.get("kind", "")) == "object_ref":
                ref_cols = _prisma_ref_columns(field, object_by_id=object_by_id, type_by_id=type_by_id)
                for col, _, pk_name in ref_cols:
                    if required:
                        lines.append(f"    {col}: item.{prop_name}.{_camel_case(pk_name)},")
                    else:
                        lines.append(f"    {col}: item.{prop_name}?.{_camel_case(pk_name)} ?? null,")
                continue
            kind = str(type_desc.get("kind", ""))
            if provider != "postgresql" and kind in {"list", "struct"}:
                if required:
                    lines.append(f"    {field_name}: JSON.stringify(item.{prop_name}),")
                else:
                    lines.append(f"    {field_name}: item.{prop_name} === undefined ? null : JSON.stringify(item.{prop_name}),")
                continue
            if required:
                lines.append(f"    {field_name}: item.{prop_name},")
            else:
                lines.append(f"    {field_name}: item.{prop_name} ?? null,")
        if obj.get("states"):
            lines.append("    current_state: item.currentState,")
        lines.append("  };")
        lines.append("}")
        lines.append("")

        lines.append(f"class {obj_name}PrismaRepository implements Persistence.{obj_name}Repository {{")
        lines.append("  private readonly delegate: any;")
        lines.append("")
        lines.append("  constructor(client: PrismaClient) {")
        lines.append(f"    this.delegate = (client as any).{repo_var};")
        lines.append("  }")
        lines.append("")
        lines.append(f"  async list(page: number, size: number): Promise<Persistence.Page<Domain.{obj_name}>> {{")
        lines.append("    const normalized = normalizePage(page, size);")
        lines.append("    const [rows, totalElements] = await Promise.all([")
        lines.append("      this.delegate.findMany({")
        lines.append("        skip: normalized.page * normalized.size,")
        lines.append("        take: normalized.size,")
        if unique_parts:
            lines.append("        orderBy: [")
            for col, _ in unique_parts:
                lines.append(f"          {{ {col}: 'asc' }},")
            lines.append("        ],")
        lines.append("      }),")
        lines.append("      this.delegate.count(),")
        lines.append("    ]);")
        lines.append("    return {")
        lines.append(f"      items: rows.map({repo_var}RowToDomain),")
        lines.append("      page: normalized.page,")
        lines.append("      size: normalized.size,")
        lines.append("      totalElements,")
        lines.append("      totalPages: totalPages(totalElements, normalized.size),")
        lines.append("    };")
        lines.append("  }")
        lines.append("")
        lines.append(f"  async getById(id: Persistence.{obj_name}Id): Promise<Domain.{obj_name} | null> {{")
        lines.append(f"    const row = await this.delegate.findUnique({{ where: {repo_var}UniqueWhere(id) }});")
        lines.append(f"    return row ? {repo_var}RowToDomain(row) : null;")
        lines.append("  }")
        lines.append("")
        lines.append(f"  async query(filter: Filters.{obj_name}QueryFilter, page: number, size: number): Promise<Persistence.Page<Domain.{obj_name}>> {{")
        lines.append("    const normalized = normalizePage(page, size);")
        lines.append(f"    const where = {repo_var}Where(filter);")
        lines.append("    const [rows, totalElements] = await Promise.all([")
        lines.append("      this.delegate.findMany({")
        lines.append("        where,")
        lines.append("        skip: normalized.page * normalized.size,")
        lines.append("        take: normalized.size,")
        if unique_parts:
            lines.append("        orderBy: [")
            for col, _ in unique_parts:
                lines.append(f"          {{ {col}: 'asc' }},")
            lines.append("        ],")
        lines.append("      }),")
        lines.append("      this.delegate.count({ where }),")
        lines.append("    ]);")
        lines.append("    return {")
        lines.append(f"      items: rows.map({repo_var}RowToDomain),")
        lines.append("      page: normalized.page,")
        lines.append("      size: normalized.size,")
        lines.append("      totalElements,")
        lines.append("      totalPages: totalPages(totalElements, normalized.size),")
        lines.append("    };")
        lines.append("  }")
        lines.append("")
        lines.append(f"  async save(item: Domain.{obj_name}): Promise<Domain.{obj_name}> {{")
        lines.append(f"    const payload = {repo_var}DomainToRow(item);")
        lines.append(
            f"    const persisted = await this.delegate.upsert({{ where: {repo_var}UniqueWhere({repo_var}IdFromDomain(item)), create: payload, update: payload }});"
        )
        lines.append(f"    return {repo_var}RowToDomain(persisted);")
        lines.append("  }")
        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _ts_scalar_type_for_descriptor(type_desc: Dict[str, Any], type_by_id: Dict[str, Dict[str, Any]]) -> str:
    kind = str(type_desc.get("kind", ""))
    if kind == "base":
        return _ts_base_type(str(type_desc.get("name", "string")))
    if kind == "custom":
        base = _resolve_custom_base(type_by_id, type_desc)
        return _ts_base_type(base)
    return "string"


def _typeorm_column_type_for_descriptor(type_desc: Dict[str, Any], type_by_id: Dict[str, Dict[str, Any]]) -> str:
    kind = str(type_desc.get("kind", ""))
    if kind == "base":
        base = str(type_desc.get("name", "string"))
    elif kind == "custom":
        base = _resolve_custom_base(type_by_id, type_desc)
    elif kind in {"list", "struct"}:
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
            field_id = str(field.get("id", ""))
            field_name_raw = str(field.get("name", "field"))
            field_name = _camel_case(field_name_raw)
            required = _is_required(field)
            nullable = "true" if not required else "false"
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            kind = str(type_desc.get("kind", ""))

            if kind == "object_ref":
                target_obj = object_by_id.get(str(type_desc.get("target_object_id", "")), {})
                target_name = _pascal_case(str(target_obj.get("name", "Object")))
                target_pk_fields = _object_primary_key_fields(target_obj)
                join_defs: List[str] = []
                for target_pk in target_pk_fields:
                    target_pk_name = str(target_pk.get("name", "id"))
                    fk_col_raw = f"{field_name_raw}_{target_pk_name}"
                    fk_prop = _camel_case(fk_col_raw)
                    fk_desc = target_pk.get("type", {}) if isinstance(target_pk.get("type"), dict) else {"kind": "base", "name": "string"}
                    fk_type = _typeorm_column_type_for_descriptor(fk_desc, type_by_id)
                    fk_ts_type = _ts_scalar_type_for_descriptor(fk_desc, type_by_id)
                    if field_id in primary_ids:
                        lines.append(f"  @PrimaryColumn({{ type: '{fk_type}', name: '{fk_col_raw}' }})")
                    else:
                        lines.append(f"  @Column({{ type: '{fk_type}', nullable: {nullable}, name: '{fk_col_raw}' }})")
                    if required:
                        lines.append(f"  {fk_prop}!: {fk_ts_type};")
                    else:
                        lines.append(f"  {fk_prop}?: {fk_ts_type} | null;")
                    lines.append("")
                    join_defs.append(f"    {{ name: '{fk_col_raw}', referencedColumnName: '{_camel_case(target_pk_name)}' }},")
                lines.append(f"  @ManyToOne(() => {target_name}Entity, {{ nullable: {nullable} }})")
                lines.append("  @JoinColumn([")
                lines.extend(join_defs)
                lines.append("  ])")
                lines.append(f"  {field_name}{'?' if not required else '!'}: {target_name}Entity;")
                lines.append("")
                continue

            col_type = _typeorm_column_type_for_descriptor(type_desc, type_by_id)
            ts_type = _ts_scalar_type_for_descriptor(type_desc, type_by_id)
            if col_type == "simple-json":
                ts_type = "unknown"
            if field_id in primary_ids:
                lines.append(f"  @PrimaryColumn({{ type: '{col_type}', name: '{field_name_raw}' }})")
            else:
                lines.append(f"  @Column({{ type: '{col_type}', nullable: {nullable}, name: '{field_name_raw}' }})")
            if required:
                lines.append(f"  {field_name}!: {ts_type};")
            else:
                lines.append(f"  {field_name}?: {ts_type} | null;")
            lines.append("")

        if obj.get("states"):
            lines.append("  @Column({ type: 'varchar', nullable: false, name: 'current_state' })")
            lines.append("  currentState!: string;")
            lines.append("")

        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_typeorm_adapter(ir: Dict[str, Any]) -> str:
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}
    query_contract_by_object_id = {
        str(item.get("object_id", "")): item
        for item in ir.get("query_contracts", [])
        if isinstance(item, dict)
    }
    entity_imports = sorted(
        {
            f"{_pascal_case(str(item.get('name', 'Object')))}Entity"
            for item in ir.get("objects", [])
            if isinstance(item, dict)
        }
    )

    lines = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import { DataSource, type Repository, type SelectQueryBuilder } from 'typeorm';",
        "import type * as Domain from './domain';",
        "import type * as Filters from './query';",
        "import type * as Persistence from './persistence';",
        "import {",
        "  " + ",\n  ".join(entity_imports),
        "} from './typeorm-entities';",
        "",
        "function normalizePage(page: number, size: number): { page: number; size: number } {",
        "  const normalizedPage = Number.isFinite(page) && page >= 0 ? Math.trunc(page) : 0;",
        "  const normalizedSize = Number.isFinite(size) && size > 0 ? Math.trunc(size) : 20;",
        "  return { page: normalizedPage, size: normalizedSize };",
        "}",
        "",
        "function totalPages(totalElements: number, size: number): number {",
        "  if (size <= 0) return 0;",
        "  return Math.ceil(totalElements / size);",
        "}",
        "",
        "export class TypeOrmGeneratedRepositories implements Persistence.GeneratedRepositories {",
    ]
    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        lines.append(f"  {_camel_case(obj_name)}: Persistence.{obj_name}Repository;")
    lines.append("")
    lines.append("  constructor(private readonly dataSource: DataSource) {")
    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        lines.append(f"    this.{_camel_case(obj_name)} = new {obj_name}TypeOrmRepository(dataSource);")
    lines.append("  }")
    lines.append("}")
    lines.append("")

    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_id = str(obj.get("id", ""))
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        entity_name = f"{obj_name}Entity"
        repo_var = _camel_case(obj_name)
        fields_by_id = _field_index(list(obj.get("fields", [])))
        pk_fields = _object_primary_key_fields(obj)
        query_contract = query_contract_by_object_id.get(obj_id, {})
        query_filters = list(query_contract.get("filters", [])) if isinstance(query_contract, dict) else []

        lines.append(f"function {repo_var}EntityToDomain(entity: any): Domain.{obj_name} {{")
        lines.append("  return {")
        for field in list(obj.get("fields", [])):
            if not isinstance(field, dict):
                continue
            field_name = str(field.get("name", "field"))
            prop_name = _camel_case(field_name)
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            required = _is_required(field)
            if str(type_desc.get("kind", "")) == "object_ref":
                target_obj = object_by_id.get(str(type_desc.get("target_object_id", "")), {})
                target_pk_fields = _object_primary_key_fields(target_obj)
                fk_props = [_camel_case(f"{field_name}_{str(pk.get('name', 'id'))}") for pk in target_pk_fields]
                null_guard = " and ".join([f"entity.{fk_prop} == null" for fk_prop in fk_props]) if fk_props else "false"
                if required:
                    lines.append(f"    {prop_name}: {{")
                    for pk_field, fk_prop in zip(target_pk_fields, fk_props):
                        lines.append(f"      {_camel_case(str(pk_field.get('name', 'id')))}: entity.{fk_prop},")
                    lines.append("    },")
                else:
                    lines.append(f"    {prop_name}: {null_guard} ? undefined : {{")
                    for pk_field, fk_prop in zip(target_pk_fields, fk_props):
                        lines.append(f"      {_camel_case(str(pk_field.get('name', 'id')))}: entity.{fk_prop},")
                    lines.append("    },")
                continue
            if required:
                lines.append(f"    {prop_name}: entity.{prop_name},")
            else:
                lines.append(f"    {prop_name}: entity.{prop_name} ?? undefined,")
        if obj.get("states"):
            lines.append("    currentState: entity.currentState,")
        lines.append("  };")
        lines.append("}")
        lines.append("")

        lines.append(f"function {repo_var}DomainToEntity(item: Domain.{obj_name}): {entity_name} {{")
        lines.append(f"  const entity = new {entity_name}();")
        for field in list(obj.get("fields", [])):
            if not isinstance(field, dict):
                continue
            field_name = str(field.get("name", "field"))
            prop_name = _camel_case(field_name)
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            required = _is_required(field)
            if str(type_desc.get("kind", "")) == "object_ref":
                target_obj = object_by_id.get(str(type_desc.get("target_object_id", "")), {})
                target_pk_fields = _object_primary_key_fields(target_obj)
                for target_pk in target_pk_fields:
                    target_prop = _camel_case(str(target_pk.get("name", "id")))
                    fk_prop = _camel_case(f"{field_name}_{str(target_pk.get('name', 'id'))}")
                    if required:
                        lines.append(f"  entity.{fk_prop} = item.{prop_name}.{target_prop};")
                    else:
                        lines.append(f"  entity.{fk_prop} = item.{prop_name}?.{target_prop} ?? null;")
                continue
            lines.append(f"  entity.{prop_name} = item.{prop_name}{'' if required else ' ?? null'};")
        if obj.get("states"):
            lines.append("  entity.currentState = item.currentState;")
        lines.append("  return entity;")
        lines.append("}")
        lines.append("")

        lines.append(f"function {repo_var}PrimaryWhere(id: Persistence.{obj_name}Id): Record<string, unknown> {{")
        lines.append("  return {")
        for pk_field in pk_fields:
            pk_name = str(pk_field.get("name", "id"))
            pk_prop = _camel_case(pk_name)
            pk_desc = pk_field.get("type", {}) if isinstance(pk_field.get("type"), dict) else {}
            if str(pk_desc.get("kind", "")) == "object_ref":
                target_obj = object_by_id.get(str(pk_desc.get("target_object_id", "")), {})
                target_pk_fields = _object_primary_key_fields(target_obj)
                for target_pk in target_pk_fields:
                    target_prop = _camel_case(str(target_pk.get("name", "id")))
                    fk_col_name = f"{pk_name}_{str(target_pk.get('name', 'id'))}"
                    fk_prop = _camel_case(fk_col_name)
                    lines.append(f"    {fk_prop}: id.{pk_prop}.{target_prop},")
            else:
                lines.append(f"    {pk_prop}: id.{pk_prop},")
        lines.append("  };")
        lines.append("}")
        lines.append("")

        lines.append(f"function {repo_var}ApplyFilter(qb: SelectQueryBuilder<{entity_name}>, filter: Filters.{obj_name}QueryFilter | undefined): void {{")
        lines.append("  if (!filter) return;")
        for filter_item in query_filters:
            if not isinstance(filter_item, dict):
                continue
            field_id = str(filter_item.get("field_id", ""))
            filter_name = _camel_case(str(filter_item.get("field_name", "field")))
            operators = [str(op) for op in filter_item.get("operators", []) if isinstance(op, str)]
            lines.append(f"  const {filter_name}Filter = filter.{filter_name};")

            if field_id == "__current_state__":
                if "eq" in operators:
                    lines.append(
                        f"  if ({filter_name}Filter?.eq !== undefined) qb.andWhere('record.current_state = :{filter_name}_eq', {{ {filter_name}_eq: {filter_name}Filter.eq }});"
                    )
                if "in" in operators:
                    lines.append(
                        f"  if ({filter_name}Filter?.in?.length) qb.andWhere('record.current_state IN (:...{filter_name}_in)', {{ {filter_name}_in: {filter_name}Filter.in }});"
                    )
                continue

            field = fields_by_id.get(field_id, {})
            if not field:
                continue
            field_name = str(field.get("name", "field"))
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}

            if str(type_desc.get("kind", "")) == "object_ref":
                target_obj = object_by_id.get(str(type_desc.get("target_object_id", "")), {})
                target_pk_fields = _object_primary_key_fields(target_obj)
                if "eq" in operators:
                    lines.append(f"  if ({filter_name}Filter?.eq !== undefined) {{")
                    for target_pk in target_pk_fields:
                        target_prop = _camel_case(str(target_pk.get("name", "id")))
                        fk_col = f"{field_name}_{str(target_pk.get('name', 'id'))}"
                        param = f"{filter_name}_eq_{target_prop}"
                        lines.append(
                            f"    qb.andWhere('record.{fk_col} = :{param}', {{ {param}: {filter_name}Filter.eq.{target_prop} }});"
                        )
                    lines.append("  }")
                if "in" in operators:
                    lines.append(f"  if ({filter_name}Filter?.in?.length) {{")
                    lines.append("    const clauses: string[] = [];")
                    lines.append("    const params: Record<string, unknown> = {};")
                    lines.append(f"    {filter_name}Filter.in.forEach((entry: any, idx: number) => {{")
                    lines.append("      const inner: string[] = [];")
                    for target_pk in target_pk_fields:
                        target_prop = _camel_case(str(target_pk.get("name", "id")))
                        fk_col = f"{field_name}_{str(target_pk.get('name', 'id'))}"
                        lines.append(f"      inner.push(`record.{fk_col} = :{filter_name}_in_${{idx}}_{target_prop}`);")
                        lines.append(f"      params['{filter_name}_in_' + idx + '_{target_prop}'] = entry.{target_prop};")
                    lines.append("      clauses.push('(' + inner.join(' AND ') + ')');")
                    lines.append("    });")
                    lines.append("    if (clauses.length > 0) qb.andWhere('(' + clauses.join(' OR ') + ')', params);")
                    lines.append("  }")
                continue

            if "eq" in operators:
                lines.append(
                    f"  if ({filter_name}Filter?.eq !== undefined) qb.andWhere('record.{field_name} = :{filter_name}_eq', {{ {filter_name}_eq: {filter_name}Filter.eq }});"
                )
            if "in" in operators:
                lines.append(
                    f"  if ({filter_name}Filter?.in?.length) qb.andWhere('record.{field_name} IN (:...{filter_name}_in)', {{ {filter_name}_in: {filter_name}Filter.in }});"
                )
            if "contains" in operators:
                lines.append(
                    f"  if (typeof {filter_name}Filter?.contains === 'string' && {filter_name}Filter.contains.length > 0) "
                    f"qb.andWhere('record.{field_name} LIKE :{filter_name}_contains', {{ {filter_name}_contains: `%${{{filter_name}Filter.contains}}%` }});"
                )
            if "gte" in operators:
                lines.append(
                    f"  if ({filter_name}Filter?.gte !== undefined) qb.andWhere('record.{field_name} >= :{filter_name}_gte', {{ {filter_name}_gte: {filter_name}Filter.gte }});"
                )
            if "lte" in operators:
                lines.append(
                    f"  if ({filter_name}Filter?.lte !== undefined) qb.andWhere('record.{field_name} <= :{filter_name}_lte', {{ {filter_name}_lte: {filter_name}Filter.lte }});"
                )
        lines.append("}")
        lines.append("")

        lines.append(f"function {repo_var}ApplyOrderBy(qb: SelectQueryBuilder<{entity_name}>): void {{")
        for pk_field in pk_fields:
            pk_name = str(pk_field.get("name", "id"))
            pk_desc = pk_field.get("type", {}) if isinstance(pk_field.get("type"), dict) else {}
            if str(pk_desc.get("kind", "")) == "object_ref":
                target_obj = object_by_id.get(str(pk_desc.get("target_object_id", "")), {})
                target_pks = _object_primary_key_fields(target_obj)
                for target_pk in target_pks:
                    lines.append(f"  qb.addOrderBy('record.{pk_name}_{str(target_pk.get('name', 'id'))}', 'ASC');")
            else:
                lines.append(f"  qb.addOrderBy('record.{pk_name}', 'ASC');")
        lines.append("}")
        lines.append("")

        lines.append(f"class {obj_name}TypeOrmRepository implements Persistence.{obj_name}Repository {{")
        lines.append(f"  private readonly repo: Repository<{entity_name}>;")
        lines.append("")
        lines.append("  constructor(private readonly dataSource: DataSource) {")
        lines.append(f"    this.repo = dataSource.getRepository({entity_name});")
        lines.append("  }")
        lines.append("")
        lines.append(f"  async list(page: number, size: number): Promise<Persistence.Page<Domain.{obj_name}>> {{")
        lines.append("    const normalized = normalizePage(page, size);")
        lines.append("    const qb = this.repo.createQueryBuilder('record');")
        lines.append(f"    {repo_var}ApplyOrderBy(qb);")
        lines.append("    qb.skip(normalized.page * normalized.size).take(normalized.size);")
        lines.append("    const [rows, totalElements] = await qb.getManyAndCount();")
        lines.append("    return {")
        lines.append(f"      items: rows.map({repo_var}EntityToDomain),")
        lines.append("      page: normalized.page,")
        lines.append("      size: normalized.size,")
        lines.append("      totalElements,")
        lines.append("      totalPages: totalPages(totalElements, normalized.size),")
        lines.append("    };")
        lines.append("  }")
        lines.append("")
        lines.append(f"  async getById(id: Persistence.{obj_name}Id): Promise<Domain.{obj_name} | null> {{")
        lines.append(f"    const row = await this.repo.findOneBy({repo_var}PrimaryWhere(id) as any);")
        lines.append(f"    return row ? {repo_var}EntityToDomain(row) : null;")
        lines.append("  }")
        lines.append("")
        lines.append(f"  async query(filter: Filters.{obj_name}QueryFilter, page: number, size: number): Promise<Persistence.Page<Domain.{obj_name}>> {{")
        lines.append("    const normalized = normalizePage(page, size);")
        lines.append("    const qb = this.repo.createQueryBuilder('record');")
        lines.append(f"    {repo_var}ApplyFilter(qb, filter);")
        lines.append(f"    {repo_var}ApplyOrderBy(qb);")
        lines.append("    qb.skip(normalized.page * normalized.size).take(normalized.size);")
        lines.append("    const [rows, totalElements] = await qb.getManyAndCount();")
        lines.append("    return {")
        lines.append(f"      items: rows.map({repo_var}EntityToDomain),")
        lines.append("      page: normalized.page,")
        lines.append("      size: normalized.size,")
        lines.append("      totalElements,")
        lines.append("      totalPages: totalPages(totalElements, normalized.size),")
        lines.append("    };")
        lines.append("  }")
        lines.append("")
        lines.append(f"  async save(item: Domain.{obj_name}): Promise<Domain.{obj_name}> {{")
        lines.append(f"    const entity = {repo_var}DomainToEntity(item);")
        lines.append("    const saved = await this.repo.save(entity as any);")
        lines.append(f"    return {repo_var}EntityToDomain(saved);")
        lines.append("  }")
        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _js_object_key(name: str) -> str:
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        return name
    return f"'{name}'"


def _mongoose_schema_type_for_descriptor(type_desc: Dict[str, Any], type_by_id: Dict[str, Dict[str, Any]]) -> str:
    kind = str(type_desc.get("kind", ""))
    if kind == "base":
        base = str(type_desc.get("name", "string"))
    elif kind == "custom":
        base = _resolve_custom_base(type_by_id, type_desc)
    elif kind == "struct":
        return "Schema.Types.Mixed"
    elif kind == "object_ref":
        return "Schema.Types.Mixed"
    elif kind == "list":
        element = type_desc.get("element", {}) if isinstance(type_desc.get("element"), dict) else {}
        return f"[{_mongoose_schema_type_for_descriptor(element, type_by_id)}]"
    else:
        return "Schema.Types.Mixed"

    mapping = {
        "string": "String",
        "boolean": "Boolean",
        "int": "Number",
        "long": "Number",
        "short": "Number",
        "byte": "Number",
        "double": "Number",
        "float": "Number",
        "decimal": "Number",
        "datetime": "String",
        "date": "String",
        "duration": "String",
    }
    return mapping.get(base, "Schema.Types.Mixed")


def _ts_type_for_mongoose_document_descriptor(
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
            return f"Domain.{_pascal_case(str(struct_by_id[struct_id].get('name', 'Struct')))}"
        return "Record<string, unknown>"
    if kind == "object_ref":
        object_id = str(type_desc.get("target_object_id", ""))
        if object_id in object_by_id:
            return f"Domain.{_pascal_case(str(object_by_id[object_id].get('name', 'Object')))}Ref"
        return "Record<string, unknown>"
    if kind == "list":
        element = type_desc.get("element", {}) if isinstance(type_desc.get("element"), dict) else {}
        return (
            f"{_ts_type_for_mongoose_document_descriptor(element, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id)}[]"
        )
    return "unknown"


def _mongoose_ref_paths_for_field(
    field: Dict[str, Any],
    *,
    object_by_id: Dict[str, Dict[str, Any]],
) -> List[Tuple[str, str]]:
    type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
    if str(type_desc.get("kind", "")) != "object_ref":
        return []
    target_object_id = str(type_desc.get("target_object_id", ""))
    target_obj = object_by_id.get(target_object_id, {})
    field_prop = _camel_case(str(field.get("name", "field")))
    refs: List[Tuple[str, str]] = []
    for target_pk in _object_primary_key_fields(target_obj):
        target_prop = _camel_case(str(target_pk.get("name", "id")))
        refs.append((f"{field_prop}.{target_prop}", target_prop))
    return refs


def _render_mongoose_models(ir: Dict[str, Any]) -> str:
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}
    struct_by_id = {item["id"]: item for item in ir.get("structs", []) if isinstance(item, dict) and "id" in item}

    lines = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import { Schema, model, type Model } from 'mongoose';",
        "import type * as Domain from './domain';",
        "",
    ]

    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        table_name = _pluralize(_snake_case(str(obj.get("name", "object"))))

        lines.append(f"export interface {obj_name}Document extends Record<string, unknown> {{")
        for field in list(obj.get("fields", [])):
            if not isinstance(field, dict):
                continue
            field_name = _camel_case(str(field.get("name", "field")))
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            ts_type = _ts_type_for_mongoose_document_descriptor(
                type_desc,
                type_by_id=type_by_id,
                object_by_id=object_by_id,
                struct_by_id=struct_by_id,
            )
            if _is_required(field):
                lines.append(f"  {field_name}: {ts_type};")
            else:
                lines.append(f"  {field_name}?: {ts_type};")
        if obj.get("states"):
            lines.append(f"  currentState: Domain.{obj_name}State;")
        lines.append("}")
        lines.append("")

        lines.append(f"const {obj_name}Schema = new Schema<{obj_name}Document>({{")
        for field in list(obj.get("fields", [])):
            if not isinstance(field, dict):
                continue
            field_name = _camel_case(str(field.get("name", "field")))
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            schema_type = _mongoose_schema_type_for_descriptor(type_desc, type_by_id)
            required = "true" if _is_required(field) else "false"
            lines.append(f"  {field_name}: {{ type: {schema_type}, required: {required} }},")
        if obj.get("states"):
            initial_state = next(
                (str(state.get("name", "")) for state in obj.get("states", []) if isinstance(state, dict) and bool(state.get("initial"))),
                "",
            )
            if initial_state:
                escaped_state = initial_state.replace("\\", "\\\\").replace("'", "\\'")
                lines.append(f"  currentState: {{ type: String, required: true, default: '{escaped_state}' }},")
            else:
                lines.append("  currentState: { type: String, required: true },")
        lines.append(f"}}, {{ collection: '{table_name}', strict: false }});")

        primary_ids = set(obj.get("keys", {}).get("primary", {}).get("field_ids", []))
        primary_paths: List[str] = []
        for field in list(obj.get("fields", [])):
            if not isinstance(field, dict):
                continue
            if str(field.get("id", "")) not in primary_ids:
                continue
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            if str(type_desc.get("kind", "")) == "object_ref":
                primary_paths.extend([path for path, _ in _mongoose_ref_paths_for_field(field, object_by_id=object_by_id)])
            else:
                primary_paths.append(_camel_case(str(field.get("name", "field"))))
        if primary_paths:
            unique_spec = ", ".join([f"{_js_object_key(path)}: 1" for path in primary_paths])
            lines.append(f"{obj_name}Schema.index({{ {unique_spec} }}, {{ unique: true }});")

        display_ids = set(obj.get("keys", {}).get("display", {}).get("field_ids", []))
        display_paths: List[str] = []
        for field in list(obj.get("fields", [])):
            if not isinstance(field, dict):
                continue
            if str(field.get("id", "")) not in display_ids:
                continue
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            if str(type_desc.get("kind", "")) == "object_ref":
                display_paths.extend([path for path, _ in _mongoose_ref_paths_for_field(field, object_by_id=object_by_id)])
            else:
                display_paths.append(_camel_case(str(field.get("name", "field"))))
        if display_paths:
            display_paths = list(dict.fromkeys(display_paths))
            display_spec = ", ".join([f"{_js_object_key(path)}: 1" for path in display_paths])
            lines.append(f"{obj_name}Schema.index({{ {display_spec} }});")

        lines.append(f"export const {obj_name}Model: Model<{obj_name}Document> = model<{obj_name}Document>('{obj_name}', {obj_name}Schema);")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_mongoose_adapter(ir: Dict[str, Any]) -> str:
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}
    query_contract_by_object_id = {
        str(item.get("object_id", "")): item
        for item in ir.get("query_contracts", [])
        if isinstance(item, dict)
    }

    model_imports = sorted(
        {
            f"{_pascal_case(str(item.get('name', 'Object')))}Model"
            for item in ir.get("objects", [])
            if isinstance(item, dict)
        }
    )
    model_type_imports = sorted(
        {
            f"{_pascal_case(str(item.get('name', 'Object')))}Document"
            for item in ir.get("objects", [])
            if isinstance(item, dict)
        }
    )

    lines = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import type { FilterQuery, Model } from 'mongoose';",
        "import type * as Domain from './domain';",
        "import type * as Filters from './query';",
        "import type * as Persistence from './persistence';",
        "import {",
        "  " + ",\n  ".join(model_imports),
        "} from './mongoose-models';",
        "import type {",
        "  " + ",\n  ".join(model_type_imports),
        "} from './mongoose-models';",
        "",
        "function normalizePage(page: number, size: number): { page: number; size: number } {",
        "  const normalizedPage = Number.isFinite(page) && page >= 0 ? Math.trunc(page) : 0;",
        "  const normalizedSize = Number.isFinite(size) && size > 0 ? Math.trunc(size) : 20;",
        "  return { page: normalizedPage, size: normalizedSize };",
        "}",
        "",
        "function totalPages(totalElements: number, size: number): number {",
        "  if (size <= 0) return 0;",
        "  return Math.ceil(totalElements / size);",
        "}",
        "",
        "function escapeRegex(value: string): string {",
        "  return value.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');",
        "}",
        "",
        "export interface MongooseGeneratedModels {",
    ]

    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        lines.append(f"  {_camel_case(obj_name)}?: Model<{obj_name}Document>;")
    lines.append("}")
    lines.append("")

    lines.append("export class MongooseGeneratedRepositories implements Persistence.GeneratedRepositories {")
    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        lines.append(f"  {_camel_case(obj_name)}: Persistence.{obj_name}Repository;")
    lines.append("")
    lines.append("  constructor(models: MongooseGeneratedModels = {}) {")
    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        repo_var = _camel_case(obj_name)
        lines.append(f"    this.{repo_var} = new {obj_name}MongooseRepository(models.{repo_var} ?? {obj_name}Model);")
    lines.append("  }")
    lines.append("}")
    lines.append("")

    for obj in sorted(ir.get("objects", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        obj_id = str(obj.get("id", ""))
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        doc_type = f"{obj_name}Document"
        repo_var = _camel_case(obj_name)
        fields_by_id = _field_index(list(obj.get("fields", [])))
        pk_fields = _object_primary_key_fields(obj)
        query_contract = query_contract_by_object_id.get(obj_id, {})
        query_filters = list(query_contract.get("filters", [])) if isinstance(query_contract, dict) else []

        lines.append(f"function {repo_var}Where(filter: Filters.{obj_name}QueryFilter | undefined): FilterQuery<{doc_type}> {{")
        lines.append("  if (!filter) return {};")
        lines.append("  const and: Record<string, unknown>[] = [];")
        for filter_item in query_filters:
            if not isinstance(filter_item, dict):
                continue
            field_id = str(filter_item.get("field_id", ""))
            filter_name = _camel_case(str(filter_item.get("field_name", "field")))
            operators = [str(op) for op in filter_item.get("operators", []) if isinstance(op, str)]
            lines.append(f"  const {filter_name}Filter = filter.{filter_name};")

            if field_id == "__current_state__":
                if "eq" in operators:
                    lines.append(f"  if ({filter_name}Filter?.eq !== undefined) and.push({{ currentState: {filter_name}Filter.eq }});")
                if "in" in operators:
                    lines.append(f"  if ({filter_name}Filter?.in?.length) and.push({{ currentState: {{ $in: {filter_name}Filter.in }} }});")
                continue

            field = fields_by_id.get(field_id, {})
            if not field:
                continue
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            field_prop = _camel_case(str(field.get("name", "field")))
            if str(type_desc.get("kind", "")) == "object_ref":
                ref_paths = _mongoose_ref_paths_for_field(field, object_by_id=object_by_id)
                if "eq" in operators:
                    lines.append(f"  if ({filter_name}Filter?.eq !== undefined) {{")
                    if ref_paths:
                        eq_pairs = ", ".join(
                            [f"{_js_object_key(path)}: {filter_name}Filter.eq.{target_prop}" for path, target_prop in ref_paths]
                        )
                        lines.append(f"    and.push({{ {eq_pairs} }});")
                    lines.append("  }")
                if "in" in operators:
                    lines.append(f"  if ({filter_name}Filter?.in?.length) {{")
                    lines.append("    and.push({")
                    lines.append(f"      $or: {filter_name}Filter.in.map((entry: any) => ({{")
                    for path, target_prop in ref_paths:
                        lines.append(f"        {_js_object_key(path)}: entry.{target_prop},")
                    lines.append("      })),")
                    lines.append("    });")
                    lines.append("  }")
                continue

            if "eq" in operators:
                lines.append(f"  if ({filter_name}Filter?.eq !== undefined) and.push({{ {field_prop}: {filter_name}Filter.eq }});")
            if "in" in operators:
                lines.append(f"  if ({filter_name}Filter?.in?.length) and.push({{ {field_prop}: {{ $in: {filter_name}Filter.in }} }});")
            if "contains" in operators:
                lines.append(
                    f"  if (typeof {filter_name}Filter?.contains === 'string' && {filter_name}Filter.contains.length > 0) "
                    f"and.push({{ {field_prop}: {{ $regex: escapeRegex({filter_name}Filter.contains), $options: 'i' }} }});"
                )
            if "gte" in operators:
                lines.append(f"  if ({filter_name}Filter?.gte !== undefined) and.push({{ {field_prop}: {{ $gte: {filter_name}Filter.gte }} }});")
            if "lte" in operators:
                lines.append(f"  if ({filter_name}Filter?.lte !== undefined) and.push({{ {field_prop}: {{ $lte: {filter_name}Filter.lte }} }});")
        lines.append("  if (and.length === 0) return {};")
        lines.append("  return { $and: and };")
        lines.append("}")
        lines.append("")

        lines.append(f"function {repo_var}IdFromDomain(item: Domain.{obj_name}): Persistence.{obj_name}Id {{")
        lines.append("  return {")
        for pk_field in pk_fields:
            pk_prop = _camel_case(str(pk_field.get("name", "id")))
            lines.append(f"    {pk_prop}: item.{pk_prop},")
        lines.append("  };")
        lines.append("}")
        lines.append("")

        lines.append(f"function {repo_var}PrimaryFilter(id: Persistence.{obj_name}Id): Record<string, unknown> {{")
        lines.append("  return {")
        for pk_field in pk_fields:
            pk_prop = _camel_case(str(pk_field.get("name", "id")))
            pk_desc = pk_field.get("type", {}) if isinstance(pk_field.get("type"), dict) else {}
            if str(pk_desc.get("kind", "")) == "object_ref":
                ref_paths = _mongoose_ref_paths_for_field(pk_field, object_by_id=object_by_id)
                for path, target_prop in ref_paths:
                    lines.append(f"    {_js_object_key(path)}: id.{pk_prop}.{target_prop},")
            else:
                lines.append(f"    {pk_prop}: id.{pk_prop},")
        lines.append("  };")
        lines.append("}")
        lines.append("")

        lines.append(f"function {repo_var}Sort(): Record<string, 1> {{")
        lines.append("  return {")
        for pk_field in pk_fields:
            pk_prop = _camel_case(str(pk_field.get("name", "id")))
            pk_desc = pk_field.get("type", {}) if isinstance(pk_field.get("type"), dict) else {}
            if str(pk_desc.get("kind", "")) == "object_ref":
                ref_paths = _mongoose_ref_paths_for_field(pk_field, object_by_id=object_by_id)
                for path, _ in ref_paths:
                    lines.append(f"    {_js_object_key(path)}: 1,")
            else:
                lines.append(f"    {pk_prop}: 1,")
        lines.append("  };")
        lines.append("}")
        lines.append("")

        lines.append(f"function {repo_var}DocumentToDomain(doc: any): Domain.{obj_name} {{")
        lines.append("  return {")
        for field in list(obj.get("fields", [])):
            if not isinstance(field, dict):
                continue
            prop_name = _camel_case(str(field.get("name", "field")))
            if _is_required(field):
                lines.append(f"    {prop_name}: doc.{prop_name},")
            else:
                lines.append(f"    {prop_name}: doc.{prop_name} ?? undefined,")
        if obj.get("states"):
            lines.append("    currentState: doc.currentState,")
        lines.append("  };")
        lines.append("}")
        lines.append("")

        lines.append(f"function {repo_var}DomainToDocument(item: Domain.{obj_name}): Record<string, unknown> {{")
        lines.append("  return {")
        for field in list(obj.get("fields", [])):
            if not isinstance(field, dict):
                continue
            prop_name = _camel_case(str(field.get("name", "field")))
            if _is_required(field):
                lines.append(f"    {prop_name}: item.{prop_name},")
            else:
                lines.append(f"    {prop_name}: item.{prop_name} ?? null,")
        if obj.get("states"):
            lines.append("    currentState: item.currentState,")
        lines.append("  };")
        lines.append("}")
        lines.append("")

        lines.append(f"class {obj_name}MongooseRepository implements Persistence.{obj_name}Repository {{")
        lines.append(f"  constructor(private readonly model: Model<{doc_type}>) {{}}")
        lines.append("")
        lines.append(f"  async list(page: number, size: number): Promise<Persistence.Page<Domain.{obj_name}>> {{")
        lines.append("    const normalized = normalizePage(page, size);")
        lines.append("    const [rows, totalElements] = await Promise.all([")
        lines.append(f"      this.model.find({{}}).sort({repo_var}Sort()).skip(normalized.page * normalized.size).limit(normalized.size).lean().exec(),")
        lines.append("      this.model.countDocuments({}).exec(),")
        lines.append("    ]);")
        lines.append("    return {")
        lines.append(f"      items: rows.map({repo_var}DocumentToDomain),")
        lines.append("      page: normalized.page,")
        lines.append("      size: normalized.size,")
        lines.append("      totalElements,")
        lines.append("      totalPages: totalPages(totalElements, normalized.size),")
        lines.append("    };")
        lines.append("  }")
        lines.append("")
        lines.append(f"  async getById(id: Persistence.{obj_name}Id): Promise<Domain.{obj_name} | null> {{")
        lines.append(f"    const row = await this.model.findOne({repo_var}PrimaryFilter(id)).lean().exec();")
        lines.append(f"    return row ? {repo_var}DocumentToDomain(row) : null;")
        lines.append("  }")
        lines.append("")
        lines.append(f"  async query(filter: Filters.{obj_name}QueryFilter, page: number, size: number): Promise<Persistence.Page<Domain.{obj_name}>> {{")
        lines.append("    const normalized = normalizePage(page, size);")
        lines.append(f"    const where = {repo_var}Where(filter);")
        lines.append("    const [rows, totalElements] = await Promise.all([")
        lines.append(f"      this.model.find(where).sort({repo_var}Sort()).skip(normalized.page * normalized.size).limit(normalized.size).lean().exec(),")
        lines.append("      this.model.countDocuments(where).exec(),")
        lines.append("    ]);")
        lines.append("    return {")
        lines.append(f"      items: rows.map({repo_var}DocumentToDomain),")
        lines.append("      page: normalized.page,")
        lines.append("      size: normalized.size,")
        lines.append("      totalElements,")
        lines.append("      totalPages: totalPages(totalElements, normalized.size),")
        lines.append("    };")
        lines.append("  }")
        lines.append("")
        lines.append(f"  async save(item: Domain.{obj_name}): Promise<Domain.{obj_name}> {{")
        lines.append(f"    const id = {repo_var}IdFromDomain(item);")
        lines.append(f"    const payload = {repo_var}DomainToDocument(item);")
        lines.append(
            f"    const persisted = await this.model.findOneAndUpdate({repo_var}PrimaryFilter(id), {{ $set: payload }}, {{ upsert: true, new: true, setDefaultsOnInsert: true, lean: true }}).exec();"
        )
        lines.append(f"    if (!persisted) return {repo_var}DocumentToDomain(payload);")
        lines.append(f"    return {repo_var}DocumentToDomain(persisted);")
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
    if stack.orm == "mongoose":
        deps["mongoose"] = "^8.7.0"

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
    return json.dumps(payload, indent=2, sort_keys=False) + "\n"


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
        configured_provider = str(
            deps.cfg_get(cfg, ["generation", "node_express", "prisma", "provider"], "sqlite")
        ).strip()
        supported_providers = {"sqlite", "postgresql", "mysql", "sqlserver", "cockroachdb"}
        prisma_provider = configured_provider if configured_provider in supported_providers else "sqlite"
        outputs[f"{node_prefix}/prisma/schema.prisma"] = _render_prisma_schema(ir, provider=prisma_provider)
        outputs[f"{node_prefix}/src/generated/prisma-adapters.ts"] = _render_prisma_adapter(ir, provider=prisma_provider)

    if stack.orm == "typeorm" and "typeorm" in targets:
        outputs[f"{node_prefix}/src/generated/typeorm-entities.ts"] = _render_typeorm_entities(ir)
        outputs[f"{node_prefix}/src/generated/typeorm-adapters.ts"] = _render_typeorm_adapter(ir)

    if stack.orm == "mongoose" and "mongoose" in targets:
        outputs[f"{node_prefix}/src/generated/mongoose-models.ts"] = _render_mongoose_models(ir)
        outputs[f"{node_prefix}/src/generated/mongoose-adapters.ts"] = _render_mongoose_adapter(ir)

    for rel, content in list(outputs.items()):
        if rel.startswith(f"{node_prefix}/src/generated/") and rel.endswith(".ts"):
            outputs[rel] = _append_js_extensions_to_relative_imports(content)

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
