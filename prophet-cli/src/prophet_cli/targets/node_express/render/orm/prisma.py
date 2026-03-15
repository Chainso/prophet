from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ..support import _camel_case
from ..support import _field_index
from ..support import _is_required
from ..support import _object_primary_key_fields
from ..support import _pascal_case
from ..support import _pluralize
from ..support import _resolve_custom_base
from ..support import _snake_case
from ..support import _ts_type_for_descriptor

def _prisma_scalar_type_for_descriptor(
    type_desc: Dict[str, Any],
    type_by_id: Dict[str, Dict[str, Any]],
    enum_by_id: Dict[str, Dict[str, Any]],
    *,
    provider: str,
) -> str:
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
        return _prisma_scalar_type_for_descriptor({"kind": "base", "name": base}, type_by_id, enum_by_id, provider=provider)
    if kind == "enum":
        if provider == "sqlite":
            return "String"
        enum_id = str(type_desc.get("target_enum_id", ""))
        enum_def = enum_by_id.get(enum_id, {})
        return _pascal_case(str(enum_def.get("name", "Enum")))
    return "String"


def _prisma_column_type_for_field(
    field: Dict[str, Any],
    type_by_id: Dict[str, Dict[str, Any]],
    enum_by_id: Dict[str, Dict[str, Any]],
    *,
    provider: str,
) -> str:
    type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
    kind = str(type_desc.get("kind", ""))
    if kind in {"base", "custom", "enum"}:
        return _prisma_scalar_type_for_descriptor(type_desc, type_by_id, enum_by_id, provider=provider)
    if kind == "struct":
        return "Json" if provider == "postgresql" else "String"
    if kind == "list":
        element = type_desc.get("element", {}) if isinstance(type_desc.get("element"), dict) else {}
        if provider == "postgresql" and str(element.get("kind", "")) in {"base", "custom", "enum"}:
            return f"{_prisma_scalar_type_for_descriptor(element, type_by_id, enum_by_id, provider=provider)}[]"
        return "String"
    return "String"


def _prisma_ref_columns(
    field: Dict[str, Any],
    *,
    object_by_id: Dict[str, Dict[str, Any]],
    type_by_id: Dict[str, Dict[str, Any]],
    enum_by_id: Dict[str, Dict[str, Any]],
    provider: str,
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
        result.append((f"{field_name}_{pk_name}", _prisma_scalar_type_for_descriptor(pk_desc, type_by_id, enum_by_id, provider=provider), pk_name))
    return result


def _state_field_default_annotation(
    field: Dict[str, Any],
    *,
    enum_by_id: Dict[str, Dict[str, Any]],
    provider: str,
) -> str:
    if not bool(field.get("is_state_field")):
        return ""
    type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
    if str(type_desc.get("kind", "")) != "enum":
        return ""
    enum_def = enum_by_id.get(str(type_desc.get("target_enum_id", "")), {})
    initial_value_id = str(field.get("initial_enum_value_id", ""))
    if not initial_value_id:
        return ""
    initial_value = next(
        (
            str(value.get("name", ""))
            for value in enum_def.get("values", [])
            if isinstance(value, dict) and str(value.get("id", "")) == initial_value_id
        ),
        "",
    )
    if not initial_value:
        return ""
    if provider == "sqlite":
        return f' @default("{initial_value}")'
    return f" @default({_pascal_case(initial_value)})"


def _render_prisma_schema(ir: Dict[str, Any], *, provider: str) -> str:
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}
    enum_by_id = {item["id"]: item for item in ir.get("enums", []) if isinstance(item, dict) and "id" in item}
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

    lines = [
        "// Code generated by prophet-cli. DO NOT EDIT.",
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
    if provider != "sqlite":
        for enum_def in sorted(ir.get("enums", []), key=lambda item: str(item.get("id", ""))):
            if not isinstance(enum_def, dict):
                continue
            enum_name = _pascal_case(str(enum_def.get("name", "Enum")))
            lines.append(f"enum {enum_name} {{")
            for value in sorted(
                [item for item in enum_def.get("values", []) if isinstance(item, dict)],
                key=lambda item: str(item.get("id", "")),
            ):
                lines.append(f"  {_pascal_case(str(value.get('name', 'Value')))}")
            lines.append("}")
            lines.append("")
    if ir.get("enums") and provider != "sqlite":
        lines.append("")
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
                ref_cols = _prisma_ref_columns(
                    field,
                    object_by_id=object_by_id,
                    type_by_id=type_by_id,
                    enum_by_id=enum_by_id,
                    provider=provider,
                )
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

            field_type = _prisma_column_type_for_field(field, type_by_id, enum_by_id, provider=provider)
            annotations: List[str] = []
            state_default = _state_field_default_annotation(field, enum_by_id=enum_by_id, provider=provider)
            if len(primary_ids) == 1 and primary_ids[0] == field_id:
                annotations.append("@id")
            if field_type.endswith("[]"):
                if not required:
                    annotations.append("@default([])")
                lines.append(f"  {field_name} {field_type}{(' ' + ' '.join(annotations)) if annotations else ''}")
            else:
                lines.append(
                    f"  {field_name} {field_type}{'' if required else '?'}{state_default}{(' ' + ' '.join(annotations)) if annotations else ''}"
                )
            if field_id in primary_id_set:
                expanded_primary_columns.append(field_name)
            if field_id in display_ids:
                display_columns.append(field_name)

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
    enum_by_id = {item["id"]: item for item in ir.get("enums", []) if isinstance(item, dict) and "id" in item}
    struct_by_id = {item["id"]: item for item in ir.get("structs", []) if isinstance(item, dict) and "id" in item}
    query_contract_by_object_id = {
        str(item.get("object_id", "")): item
        for item in ir.get("query_contracts", [])
        if isinstance(item, dict)
    }

    lines = [
        "// Code generated by prophet-cli. DO NOT EDIT.",
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
        "export class PrismaRepositories implements Persistence.Repositories {",
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

            field = fields_by_id.get(field_id, {})
            if not field:
                continue
            field_name = str(field.get("name", "field"))
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            if str(type_desc.get("kind", "")) == "object_ref":
                ref_cols = _prisma_ref_columns(
                    field,
                    object_by_id=object_by_id,
                    type_by_id=type_by_id,
                    enum_by_id=enum_by_id,
                    provider=provider,
                )
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
                ref_cols = _prisma_ref_columns(
                    pk_field,
                    object_by_id=object_by_id,
                    type_by_id=type_by_id,
                    enum_by_id=enum_by_id,
                    provider=provider,
                )
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

        lines.append(f"function {repo_var}PrimaryWhere(id: Persistence.{obj_name}Id): any {{")
        if unique_parts:
            lines.append("  return {")
            for col, expr in unique_parts:
                lines.append(f"    {col}: {expr},")
            lines.append("  };")
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
                ref_cols = _prisma_ref_columns(
                    field,
                    object_by_id=object_by_id,
                    type_by_id=type_by_id,
                    enum_by_id=enum_by_id,
                    provider=provider,
                )
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
                    enum_by_id=enum_by_id,
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
                ref_cols = _prisma_ref_columns(
                    field,
                    object_by_id=object_by_id,
                    type_by_id=type_by_id,
                    enum_by_id=enum_by_id,
                    provider=provider,
                )
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
        lines.append("  };")
        lines.append("}")
        lines.append("")

        lines.append(f"class {obj_name}PrismaRepository implements Persistence.{obj_name}Repository {{")
        lines.append("  private readonly delegate: any;")
        lines.append("")
        lines.append("  constructor(private readonly client: PrismaClient) {")
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
