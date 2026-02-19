from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from prophet_cli.core.compatibility import classify_type_change
from prophet_cli.core.compatibility import describe_type_descriptor
from prophet_cli.core.config import cfg_get

def snake_case(value: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.replace("-", "_").lower()


def pascal_case(value: str) -> str:
    parts = re.split(r"[_\-\s]+", value)
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def camel_case(value: str) -> str:
    p = pascal_case(value)
    return p[:1].lower() + p[1:] if p else p


def pluralize(value: str) -> str:
    if value.endswith("y") and len(value) > 1 and value[-2] not in "aeiou":
        return value[:-1] + "ies"
    if value.endswith("s"):
        return value + "es"
    return value + "s"


def sql_type_for_field(field: Dict[str, Any], type_by_id: Dict[str, Dict[str, Any]]) -> str:
    t = field["type"]
    if t["kind"] == "list":
        return "text"
    if t["kind"] == "base":
        name = t["name"]
    elif t["kind"] == "custom":
        name = type_by_id[t["target_type_id"]]["base"]
    else:
        return "text"

    return {
        "string": "text",
        "int": "integer",
        "long": "bigint",
        "short": "smallint",
        "byte": "smallint",
        "double": "double precision",
        "float": "real",
        "decimal": "numeric(18,2)",
        "boolean": "boolean",
        "datetime": "timestamptz",
        "date": "date",
        "duration": "interval",
    }.get(name, "text")


def object_ref_target_ids_for_type(type_desc: Dict[str, Any]) -> List[str]:
    if type_desc.get("kind") == "object_ref":
        return [type_desc["target_object_id"]]
    if type_desc.get("kind") == "list":
        return object_ref_target_ids_for_type(type_desc["element"])
    return []


def json_schema_for_field(
    field: Dict[str, Any],
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    t = field["type"]
    if t["kind"] == "list":
        item_schema = json_schema_for_field({"type": t["element"]}, type_by_id, object_by_id, struct_by_id)
        return {"type": "array", "items": item_schema}
    if t["kind"] == "object_ref":
        target = object_by_id[t["target_object_id"]]
        return {"$ref": f"#/components/schemas/{target['name']}Ref"}
    if t["kind"] == "struct":
        target = struct_by_id[t["target_struct_id"]]
        return {"$ref": f"#/components/schemas/{target['name']}"}

    if t["kind"] == "base":
        base = t["name"]
    else:
        base = type_by_id[t["target_type_id"]]["base"]

    if base in {"string", "duration"}:
        return {"type": "string"}
    if base in {"int", "long", "short", "byte"}:
        return {"type": "integer"}
    if base in {"double", "float", "decimal"}:
        if base == "decimal":
            return {"type": "string", "description": "Decimal encoded as string"}
        return {"type": "number"}
    if base == "boolean":
        return {"type": "boolean"}
    if base == "date":
        return {"type": "string", "format": "date"}
    if base == "datetime":
        return {"type": "string", "format": "date-time"}

    return {"type": "string"}


def yaml_dump_stable(value: Any) -> str:
    return yaml.safe_dump(value, sort_keys=False, default_flow_style=False).rstrip() + "\n"


def render_sql(ir: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("-- GENERATED FILE: do not edit directly.")
    lines.append("-- Source: configured ontology file (project.ontology_file)")
    lines.append("")

    objects = ir["objects"]
    type_by_id = {t["id"]: t for t in ir.get("types", [])}

    has_states = any(o.get("states") for o in objects)
    if has_states:
        lines.extend(
            [
                "create table if not exists prophet_state_catalog (",
                "  object_model_id text not null,",
                "  state_id text not null,",
                "  state_name text not null,",
                "  is_initial boolean not null,",
                "  primary key (object_model_id, state_id),",
                "  unique (object_model_id, state_name)",
                ");",
                "",
                "create table if not exists prophet_transition_catalog (",
                "  object_model_id text not null,",
                "  transition_id text not null,",
                "  from_state_id text not null,",
                "  to_state_id text not null,",
                "  primary key (object_model_id, transition_id)",
                ");",
                "",
            ]
        )

        state_values: List[str] = []
        transition_values: List[str] = []
        for obj in objects:
            for state in obj.get("states", []):
                initial = "true" if state.get("initial") else "false"
                state_values.append(
                    f"  ('{obj['id']}', '{state['id']}', '{state['name']}', {initial})"
                )
            for tr in obj.get("transitions", []):
                transition_values.append(
                    f"  ('{obj['id']}', '{tr['id']}', '{tr['from_state_id']}', '{tr['to_state_id']}')"
                )

        if state_values:
            lines.append("insert into prophet_state_catalog (object_model_id, state_id, state_name, is_initial)")
            lines.append("values")
            lines.append(",\n".join(state_values))
            lines.append("on conflict do nothing;")
            lines.append("")

        if transition_values:
            lines.append("insert into prophet_transition_catalog (object_model_id, transition_id, from_state_id, to_state_id)")
            lines.append("values")
            lines.append(",\n".join(transition_values))
            lines.append("on conflict do nothing;")
            lines.append("")

    object_by_id = {o["id"]: o for o in objects}

    for obj in objects:
        table = pluralize(snake_case(obj["name"]))
        fields = obj.get("fields", [])
        pk_fields = primary_key_fields_for_object(obj)
        pk_field_ids = {f.get("id") for f in pk_fields}
        pk_column_by_field_id: Dict[str, str] = {}

        column_lines: List[str] = []
        fk_lines: List[str] = []

        for field in fields:
            col_name = snake_case(field["name"])
            required = field.get("cardinality", {}).get("min", 0) > 0
            not_null = " not null" if required else ""
            sql_type = sql_type_for_field(field, type_by_id)
            if field["type"]["kind"] == "object_ref":
                target_obj = object_by_id[field["type"]["target_object_id"]]
                target_pk = primary_key_field_for_object(target_obj)
                target_table = pluralize(snake_case(target_obj["name"]))
                target_pk_col = snake_case(target_pk["name"])
                col_name = f"{col_name}_{target_pk_col}"
                sql_type = sql_type_for_field(target_pk, type_by_id)
                fk_name = f"fk_{table}_{col_name}"
                fk_lines.append(
                    f"  constraint {fk_name} foreign key ({col_name}) references {target_table}({target_pk_col})"
                )

            if field.get("id") in pk_field_ids:
                pk_column_by_field_id[str(field.get("id"))] = col_name
            extra = ""
            if sql_type.startswith("numeric"):
                extra = " check ({0} >= 0)".format(col_name)
            column_lines.append(f"  {col_name} {sql_type}{not_null}{extra}")

        pk_columns = [pk_column_by_field_id.get(str(f.get("id"))) for f in pk_fields]
        pk_columns = [col for col in pk_columns if col]
        if pk_columns:
            fk_lines.append(f"  primary key ({', '.join(pk_columns)})")

        if obj.get("states"):
            enum_vals = ", ".join(f"'{s['name'].upper()}'" for s in obj["states"])
            column_lines.append(f"  __prophet_state text not null check (__prophet_state in ({enum_vals}))")

        column_lines.extend(
            [
                "  row_version bigint not null default 0",
                "  created_at timestamptz not null default now()",
                "  updated_at timestamptz not null default now()",
            ]
        )

        lines.append(f"create table if not exists {table} (")
        all_defs = column_lines + fk_lines
        for idx, c in enumerate(all_defs):
            suffix = "," if idx < len(all_defs) - 1 else ""
            lines.append(c + suffix)
        lines.append(");")
        lines.append("")

        for field in fields:
            if field["type"]["kind"] == "object_ref":
                target_obj = object_by_id[field["type"]["target_object_id"]]
                target_pk = primary_key_field_for_object(target_obj)
                idx_col = f"{snake_case(field['name'])}_{snake_case(target_pk['name'])}"
                idx_name = f"idx_{table}_{idx_col}"
                lines.append(f"create index if not exists {idx_name} on {table} ({idx_col});")

        display_columns = display_index_columns_for_object(obj, type_by_id, object_by_id)
        if display_columns:
            idx_display = display_index_name_for_object(obj)
            lines.append(f"create index if not exists {idx_display} on {table} ({', '.join(display_columns)});")

        if obj.get("states"):
            idx_state = f"idx_{table}___prophet_state"
            lines.append(f"create index if not exists {idx_state} on {table} (__prophet_state);")

            history_table = f"{snake_case(obj['name'])}_state_history"
            history_pk_columns: List[str] = []
            history_fk_cols: List[str] = []
            for pk_field in pk_fields:
                pk_col_name, pk_sql_type, _, _ = field_sql_column_details(pk_field, type_by_id, object_by_id)
                history_pk_columns.append(f"  {pk_col_name} {pk_sql_type} not null,")
                history_fk_cols.append(pk_col_name)
            fk_columns_clause = ", ".join(history_fk_cols)
            lines.extend(
                [
                    "",
                    f"create table if not exists {history_table} (",
                    "  history_id bigserial primary key,",
                    *history_pk_columns,
                    "  transition_id text not null,",
                    "  from_state text not null,",
                    "  to_state text not null,",
                    "  changed_at timestamptz not null default now(),",
                    "  changed_by text,",
                    f"  constraint fk_{history_table}_entity foreign key ({fk_columns_clause}) references {table}({fk_columns_clause})",
                    ");",
                    f"create index if not exists idx_{history_table}_entity on {history_table} ({fk_columns_clause});",
                    f"create index if not exists idx_{history_table}_changed_at on {history_table} (changed_at);",
                ]
            )

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def table_name_for_object(obj: Dict[str, Any]) -> str:
    return pluralize(snake_case(obj["name"]))


def primary_key_fields_for_object(obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    fields = list(obj.get("fields", []))
    if not fields:
        return []
    field_by_id = {f.get("id"): f for f in fields}
    key_field_ids = (
        obj.get("keys", {})
        .get("primary", {})
        .get("field_ids", [])
        if isinstance(obj.get("keys"), dict)
        else []
    )
    if isinstance(key_field_ids, list) and key_field_ids:
        resolved = [field_by_id[fid] for fid in key_field_ids if fid in field_by_id]
        if resolved:
            return resolved
    legacy = [f for f in fields if f.get("key") == "primary"]
    if legacy:
        return legacy
    return [fields[0]]


def primary_key_field_for_object(obj: Dict[str, Any]) -> Dict[str, Any]:
    fields = primary_key_fields_for_object(obj)
    return fields[0]


def display_key_fields_for_object(obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    fields = list(obj.get("fields", []))
    if not fields:
        return []
    field_by_id = {f.get("id"): f for f in fields}
    key_field_ids = (
        obj.get("keys", {})
        .get("display", {})
        .get("field_ids", [])
        if isinstance(obj.get("keys"), dict)
        else []
    )
    if isinstance(key_field_ids, list) and key_field_ids:
        resolved = [field_by_id[fid] for fid in key_field_ids if fid in field_by_id]
        if resolved:
            return resolved
    legacy = [f for f in fields if f.get("key") == "display"]
    if legacy:
        return legacy
    return []


def field_sql_column_details(
    field: Dict[str, Any],
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
) -> Tuple[str, str, Optional[Tuple[str, str]], Optional[str]]:
    col_name = snake_case(field["name"])
    sql_type = sql_type_for_field(field, type_by_id)
    fk_ref: Optional[Tuple[str, str]] = None
    idx_col: Optional[str] = None
    if field["type"]["kind"] == "object_ref":
        target_obj = object_by_id[field["type"]["target_object_id"]]
        target_pk = primary_key_field_for_object(target_obj)
        target_table = table_name_for_object(target_obj)
        target_pk_col = snake_case(target_pk["name"])
        col_name = f"{col_name}_{target_pk_col}"
        sql_type = sql_type_for_field(target_pk, type_by_id)
        fk_ref = (target_table, target_pk_col)
        idx_col = col_name
    return col_name, sql_type, fk_ref, idx_col


def key_column_names_for_fields(
    key_fields: List[Dict[str, Any]],
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
) -> List[str]:
    columns: List[str] = []
    for field in key_fields:
        col_name, _, _, _ = field_sql_column_details(field, type_by_id, object_by_id)
        if col_name not in columns:
            columns.append(col_name)
    return columns


def display_index_columns_for_object(
    obj: Dict[str, Any],
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
) -> List[str]:
    display_columns = key_column_names_for_fields(display_key_fields_for_object(obj), type_by_id, object_by_id)
    if not display_columns:
        return []
    primary_columns = key_column_names_for_fields(primary_key_fields_for_object(obj), type_by_id, object_by_id)
    if display_columns == primary_columns:
        return []
    return display_columns


def display_index_name_for_object(obj: Dict[str, Any]) -> str:
    return f"idx_{table_name_for_object(obj)}_display"


def render_create_table_statements_for_object(
    obj: Dict[str, Any],
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
) -> List[str]:
    table = table_name_for_object(obj)
    fields = obj.get("fields", [])
    pk_fields = primary_key_fields_for_object(obj)
    pk_field_ids = {f.get("id") for f in pk_fields}
    pk_column_by_field_id: Dict[str, str] = {}

    column_lines: List[str] = []
    fk_lines: List[str] = []
    index_lines: List[str] = []
    for field in fields:
        col_name, sql_type, fk_ref, idx_col = field_sql_column_details(field, type_by_id, object_by_id)
        required = field.get("cardinality", {}).get("min", 0) > 0
        not_null = " not null" if required else ""
        if field.get("id") in pk_field_ids:
            pk_column_by_field_id[str(field.get("id"))] = col_name
        extra = ""
        if sql_type.startswith("numeric"):
            extra = f" check ({col_name} >= 0)"
        column_lines.append(f"  {col_name} {sql_type}{not_null}{extra}")
        if fk_ref is not None:
            fk_name = f"fk_{table}_{col_name}"
            fk_lines.append(
                f"  constraint {fk_name} foreign key ({col_name}) references {fk_ref[0]}({fk_ref[1]})"
            )
        if idx_col is not None:
            idx_name = f"idx_{table}_{idx_col}"
            index_lines.append(f"create index if not exists {idx_name} on {table} ({idx_col});")

    display_columns = display_index_columns_for_object(obj, type_by_id, object_by_id)
    if display_columns:
        idx_display = display_index_name_for_object(obj)
        index_lines.append(f"create index if not exists {idx_display} on {table} ({', '.join(display_columns)});")

    if obj.get("states"):
        enum_vals = ", ".join(f"'{s['name'].upper()}'" for s in obj["states"])
        column_lines.append(f"  __prophet_state text not null check (__prophet_state in ({enum_vals}))")

    column_lines.extend(
        [
            "  row_version bigint not null default 0",
            "  created_at timestamptz not null default now()",
            "  updated_at timestamptz not null default now()",
        ]
    )
    pk_columns = [pk_column_by_field_id.get(str(f.get("id"))) for f in pk_fields]
    pk_columns = [col for col in pk_columns if col]
    if pk_columns:
        fk_lines.append(f"  primary key ({', '.join(pk_columns)})")

    statements: List[str] = []
    statements.append(f"create table if not exists {table} (")
    for idx, col in enumerate(column_lines + fk_lines):
        suffix = "," if idx < len(column_lines + fk_lines) - 1 else ""
        statements.append(col + suffix)
    statements.append(");")
    statements.extend(index_lines)
    if obj.get("states"):
        idx_state = f"idx_{table}___prophet_state"
        statements.append(f"create index if not exists {idx_state} on {table} (__prophet_state);")
        history_table = f"{snake_case(obj['name'])}_state_history"
        history_pk_columns: List[str] = []
        history_fk_cols: List[str] = []
        for pk_field in pk_fields:
            pk_col_name, pk_sql_type, _, _ = field_sql_column_details(pk_field, type_by_id, object_by_id)
            history_pk_columns.append(f"  {pk_col_name} {pk_sql_type} not null,")
            history_fk_cols.append(pk_col_name)
        fk_columns_clause = ", ".join(history_fk_cols)
        statements.extend(
            [
                f"create table if not exists {history_table} (",
                "  history_id bigserial primary key,",
                *history_pk_columns,
                "  transition_id text not null,",
                "  from_state text not null,",
                "  to_state text not null,",
                "  changed_at timestamptz not null default now(),",
                "  changed_by text,",
                f"  constraint fk_{history_table}_entity foreign key ({fk_columns_clause}) references {table}({fk_columns_clause})",
                ");",
                f"create index if not exists idx_{history_table}_entity on {history_table} ({fk_columns_clause});",
                f"create index if not exists idx_{history_table}_changed_at on {history_table} (changed_at);",
            ]
        )
    return statements


def render_delta_migration(
    old_ir: Dict[str, Any], new_ir: Dict[str, Any]
) -> Tuple[str, List[str], bool, Dict[str, Any]]:
    old_objects = {o["id"]: o for o in old_ir.get("objects", [])}
    new_objects = {o["id"]: o for o in new_ir.get("objects", [])}
    old_type_by_id = {t["id"]: t for t in old_ir.get("types", [])}
    type_by_id = {t["id"]: t for t in new_ir.get("types", [])}
    old_object_by_id = {o["id"]: o for o in old_ir.get("objects", [])}
    object_by_id = {o["id"]: o for o in new_ir.get("objects", [])}

    statements: List[str] = []
    warnings: List[str] = []
    findings: List[Dict[str, Any]] = []
    destructive_changes = False
    backfill_required = False
    safe_auto_apply_count = 0
    manual_review_count = 0
    destructive_count = 0

    def add_finding(kind: str, classification: str, message: str, suggestion: Optional[str] = None) -> None:
        nonlocal safe_auto_apply_count, manual_review_count, destructive_count
        entry: Dict[str, Any] = {
            "kind": kind,
            "classification": classification,
            "message": message,
        }
        if suggestion:
            entry["suggestion"] = suggestion
        findings.append(entry)
        if classification == "safe_auto_apply":
            safe_auto_apply_count += 1
        elif classification == "destructive":
            destructive_count += 1
        else:
            manual_review_count += 1

    new_only_ids = sorted(set(new_objects) - set(old_objects))
    old_only_ids = sorted(set(old_objects) - set(new_objects))

    for oid in new_only_ids:
        obj = new_objects[oid]
        statements.append(f"-- object added: {obj['name']} ({oid})")
        statements.extend(render_create_table_statements_for_object(obj, type_by_id, object_by_id))
        statements.append("")
        add_finding(
            "object_added",
            "safe_auto_apply",
            f"object added: {obj['name']} ({oid})",
        )

    for oid in old_only_ids:
        obj = old_objects[oid]
        table = table_name_for_object(obj)
        warnings.append(f"destructive: object removed ({obj['name']}); manual drop for table '{table}' required.")
        destructive_changes = True
        add_finding(
            "object_removed",
            "destructive",
            f"object removed: {obj['name']} ({oid})",
            f"manual drop for table '{table}' required",
        )

    # Heuristic object rename hints: removed+added objects with same PK SQL type and overlapping field names.
    for old_oid in old_only_ids:
        old_obj = old_objects[old_oid]
        old_pk = primary_key_field_for_object(old_obj)
        old_pk_sql = sql_type_for_field(old_pk, type_by_id)
        old_field_names = {f["name"] for f in old_obj.get("fields", [])}
        best: Optional[Tuple[float, Dict[str, Any]]] = None
        for new_oid in new_only_ids:
            new_obj = new_objects[new_oid]
            new_pk = primary_key_field_for_object(new_obj)
            new_pk_sql = sql_type_for_field(new_pk, type_by_id)
            if old_pk_sql != new_pk_sql:
                continue
            new_field_names = {f["name"] for f in new_obj.get("fields", [])}
            union = old_field_names.union(new_field_names)
            if not union:
                continue
            score = len(old_field_names.intersection(new_field_names)) / len(union)
            if best is None or score > best[0]:
                best = (score, new_obj)
        if best is not None and best[0] >= 0.5:
            target = best[1]
            hint = (
                f"rename_hint: object '{old_obj['name']}' may have been renamed to '{target['name']}' "
                "(high field overlap, matching PK type)"
            )
            warnings.append(hint)
            add_finding("object_rename_hint", "manual_review", hint)

    for oid in sorted(set(old_objects).intersection(new_objects)):
        old_obj = old_objects[oid]
        new_obj = new_objects[oid]
        table = table_name_for_object(new_obj)
        old_fields = {f["id"]: f for f in old_obj.get("fields", [])}
        new_fields = {f["id"]: f for f in new_obj.get("fields", [])}
        added_field_ids = sorted(set(new_fields) - set(old_fields))
        removed_field_ids = sorted(set(old_fields) - set(new_fields))

        for fid in added_field_ids:
            new_field = new_fields[fid]
            col_name, sql_type, fk_ref, idx_col = field_sql_column_details(new_field, type_by_id, object_by_id)
            required = new_field.get("cardinality", {}).get("min", 0) > 0
            not_null = "" if required else ""
            extra = f" check ({col_name} >= 0)" if sql_type.startswith("numeric") else ""
            statements.append(f"alter table {table} add column if not exists {col_name} {sql_type}{not_null}{extra};")
            if required:
                add_finding(
                    "column_added_required",
                    "manual_review",
                    f"required field added: {new_obj['name']}.{new_field['name']}",
                    f"populate '{table}.{col_name}' then enforce NOT NULL manually",
                )
            else:
                add_finding(
                    "column_added_optional",
                    "safe_auto_apply",
                    f"optional field added: {new_obj['name']}.{new_field['name']}",
                )
            if fk_ref is not None:
                fk_name = f"fk_{table}_{col_name}"
                statements.append(
                    f"alter table {table} add constraint {fk_name} foreign key ({col_name}) references {fk_ref[0]}({fk_ref[1]});"
                )
            if idx_col is not None:
                idx_name = f"idx_{table}_{idx_col}"
                statements.append(f"create index if not exists {idx_name} on {table} ({idx_col});")
            if required:
                warnings.append(
                    f"backfill_required: required field added ({new_obj['name']}.{new_field['name']}); "
                    f"populate '{table}.{col_name}' then enforce NOT NULL manually."
                )
                backfill_required = True

        for fid in removed_field_ids:
            old_field = old_fields[fid]
            col_name, _, _, _ = field_sql_column_details(old_field, type_by_id, object_by_id)
            warnings.append(
                f"destructive: field removed ({old_obj['name']}.{old_field['name']}); manual drop for '{table}.{col_name}' required."
            )
            destructive_changes = True
            add_finding(
                "column_removed",
                "destructive",
                f"field removed: {old_obj['name']}.{old_field['name']}",
                f"manual drop for '{table}.{col_name}' required",
            )

        # Heuristic column rename hints within same object by SQL type.
        for old_fid in removed_field_ids:
            old_field = old_fields[old_fid]
            old_col, old_sql, _, _ = field_sql_column_details(old_field, type_by_id, object_by_id)
            old_min = int(old_field.get("cardinality", {}).get("min", 0))
            for new_fid in added_field_ids:
                new_field = new_fields[new_fid]
                new_col, new_sql, _, _ = field_sql_column_details(new_field, type_by_id, object_by_id)
                new_min = int(new_field.get("cardinality", {}).get("min", 0))
                if old_sql == new_sql and old_min == new_min:
                    hint = (
                        f"rename_hint: column '{table}.{old_col}' may map to '{table}.{new_col}' "
                        f"({old_obj['name']}.{old_field['name']} -> {new_obj['name']}.{new_field['name']})"
                    )
                    warnings.append(hint)
                    add_finding("column_rename_hint", "manual_review", hint)
                    break

        for fid in sorted(set(old_fields).intersection(new_fields)):
            old_field = old_fields[fid]
            new_field = new_fields[fid]
            old_type = old_field.get("type", {})
            new_type = new_field.get("type", {})
            type_level = classify_type_change(old_type, new_type)
            if type_level == "breaking":
                warnings.append(
                    "destructive: field type changed incompatibly "
                    f"({new_obj['name']}.{new_field['name']}: {describe_type_descriptor(old_type)} -> {describe_type_descriptor(new_type)})."
                )
                destructive_changes = True
                add_finding(
                    "column_type_change_incompatible",
                    "destructive",
                    f"type changed incompatibly: {new_obj['name']}.{new_field['name']}",
                    f"{describe_type_descriptor(old_type)} -> {describe_type_descriptor(new_type)}",
                )
            old_min = int(old_field.get("cardinality", {}).get("min", 0))
            new_min = int(new_field.get("cardinality", {}).get("min", 0))
            if new_min > old_min:
                warnings.append(
                    f"backfill_required: cardinality tightened for {new_obj['name']}.{new_field['name']} ({old_min} -> {new_min})."
                )
                backfill_required = True
                add_finding(
                    "cardinality_tightened_min",
                    "manual_review",
                    f"cardinality tightened: {new_obj['name']}.{new_field['name']} min {old_min} -> {new_min}",
                )
            old_max = old_field.get("cardinality", {}).get("max", 1)
            new_max = new_field.get("cardinality", {}).get("max", 1)
            if (old_max == 1 and new_max != 1) or (old_max != 1 and new_max == 1):
                warnings.append(
                    f"destructive: scalar/list wire shape changed for {new_obj['name']}.{new_field['name']} ({old_max} -> {new_max})."
                )
                destructive_changes = True
                add_finding(
                    "wire_shape_change",
                    "destructive",
                    f"wire shape changed: {new_obj['name']}.{new_field['name']} ({old_max} -> {new_max})",
                )

        old_display_columns = display_index_columns_for_object(old_obj, old_type_by_id, old_object_by_id)
        new_display_columns = display_index_columns_for_object(new_obj, type_by_id, object_by_id)
        if old_display_columns != new_display_columns:
            idx_display = display_index_name_for_object(new_obj)
            if old_display_columns:
                statements.append(f"drop index if exists {idx_display};")
            if new_display_columns:
                statements.append(f"create index if not exists {idx_display} on {table} ({', '.join(new_display_columns)});")
            if old_display_columns and new_display_columns:
                add_finding(
                    "display_index_changed",
                    "safe_auto_apply",
                    f"display index updated: {new_obj['name']}",
                    f"{old_display_columns} -> {new_display_columns}",
                )
            elif new_display_columns:
                add_finding(
                    "display_index_added",
                    "safe_auto_apply",
                    f"display index added: {new_obj['name']}",
                    f"{new_display_columns}",
                )
            else:
                add_finding(
                    "display_index_removed",
                    "safe_auto_apply",
                    f"display index removed: {new_obj['name']}",
                    f"{old_display_columns}",
                )

        old_state_names = sorted(s["name"] for s in old_obj.get("states", []))
        new_state_names = sorted(s["name"] for s in new_obj.get("states", []))
        if old_state_names != new_state_names:
            warnings.append(
                f"manual_review: state set changed for {new_obj['name']} (__prophet_state constraint may require manual adjustment)."
            )
            add_finding(
                "state_set_changed",
                "manual_review",
                f"state set changed for {new_obj['name']}",
                "__prophet_state constraint may require manual adjustment",
            )

    has_changes = bool(statements or warnings)
    if not has_changes:
        empty_meta = {
            "safe_auto_apply_count": 0,
            "manual_review_count": 0,
            "destructive_count": 0,
            "findings": [],
        }
        return "", [], False, empty_meta

    lines: List[str] = [
        "-- GENERATED FILE: do not edit directly.",
        "-- Source: baseline IR -> current IR delta migration",
        f"-- SAFETY: destructive_changes={'true' if destructive_changes else 'false'}",
        f"-- SAFETY: backfill_required={'true' if backfill_required else 'false'}",
        f"-- SAFETY: manual_review_required={'true' if warnings else 'false'}",
        f"-- SAFETY: safe_auto_apply_count={safe_auto_apply_count}",
        f"-- SAFETY: manual_review_count={manual_review_count}",
        f"-- SAFETY: destructive_count={destructive_count}",
        "",
    ]
    if warnings:
        lines.append("-- WARNINGS:")
        for warning in warnings:
            lines.append(f"-- - {warning}")
        lines.append("")
    lines.extend(statements)
    meta = {
        "safe_auto_apply_count": safe_auto_apply_count,
        "manual_review_count": manual_review_count,
        "destructive_count": destructive_count,
        "findings": findings,
    }
    return "\n".join(lines).rstrip() + "\n", warnings, True, meta


def render_openapi(ir: Dict[str, Any]) -> str:
    objects = ir["objects"]
    structs = ir.get("structs", [])
    actions = ir.get("actions", [])
    action_inputs = ir.get("action_inputs", [])
    events = ir.get("events", [])
    type_by_id = {t["id"]: t for t in ir.get("types", [])}
    object_by_id = {o["id"]: o for o in objects}
    struct_by_id = {s["id"]: s for s in structs}
    action_input_by_id = {s["id"]: s for s in action_inputs}
    event_by_id = {e["id"]: e for e in events if isinstance(e, dict) and "id" in e}

    def _resolved_display_name(item: Dict[str, Any]) -> str:
        explicit = str(item.get("display_name", "")).strip()
        if explicit:
            return explicit
        return str(item.get("name", "")).strip()

    def _apply_display_name_hint(schema: Dict[str, Any], item: Dict[str, Any]) -> None:
        if "$ref" in schema:
            return
        resolved = _resolved_display_name(item)
        symbol = str(item.get("name", "")).strip()
        if resolved and resolved != symbol:
            schema.setdefault("title", resolved)
            schema.setdefault("x-prophet-display-name", resolved)

    components_schemas: Dict[str, Any] = {}

    for source in list(objects) + list(structs) + list(action_inputs) + [e for e in events if isinstance(e, dict)]:
        for f in source.get("fields", []):
            for target_id in object_ref_target_ids_for_type(f["type"]):
                target = object_by_id[target_id]
                target_pk = primary_key_field_for_object(target)
                ref_name = f"{target['name']}Ref"
                components_schemas[ref_name] = {
                    "type": "object",
                    "required": [camel_case(target_pk["name"])],
                    "properties": {
                        camel_case(target_pk["name"]): json_schema_for_field(
                            target_pk,
                            type_by_id,
                            object_by_id,
                            struct_by_id,
                        )
                    },
                }

    for struct in structs:
        required_props: List[str] = []
        properties: Dict[str, Any] = {}
        for f in struct.get("fields", []):
            prop = camel_case(f["name"])
            field_schema = json_schema_for_field(f, type_by_id, object_by_id, struct_by_id)
            if isinstance(field_schema, dict):
                _apply_display_name_hint(field_schema, f)
            properties[prop] = field_schema
            if f.get("cardinality", {}).get("min", 0) > 0:
                required_props.append(prop)
        components_schemas[struct["name"]] = {
            "type": "object",
            "required": required_props,
            "properties": properties,
        }
        _apply_display_name_hint(components_schemas[struct["name"]], struct)
        if struct.get("description"):
            components_schemas[struct["name"]]["description"] = struct["description"]

    for obj in objects:
        required_props: List[str] = []
        properties: Dict[str, Any] = {}
        for f in obj.get("fields", []):
            prop = camel_case(f["name"])
            field_schema = json_schema_for_field(f, type_by_id, object_by_id, struct_by_id)
            if isinstance(field_schema, dict):
                _apply_display_name_hint(field_schema, f)
            properties[prop] = field_schema
            if f.get("cardinality", {}).get("min", 0) > 0:
                required_props.append(prop)
        if obj.get("states"):
            properties["state"] = {
                "type": "string",
                "enum": [s["name"].upper() for s in obj["states"]],
            }
            required_props.append("state")

        components_schemas[obj["name"]] = {
            "type": "object",
            "required": required_props,
            "properties": properties,
        }
        _apply_display_name_hint(components_schemas[obj["name"]], obj)
        if obj.get("description"):
            components_schemas[obj["name"]]["description"] = obj["description"]
        components_schemas[f"{obj['name']}ListResponse"] = {
            "type": "object",
            "required": ["items", "page", "size", "totalElements", "totalPages"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"$ref": f"#/components/schemas/{obj['name']}"},
                },
                "page": {"type": "integer"},
                "size": {"type": "integer"},
                "totalElements": {"type": "integer"},
                "totalPages": {"type": "integer"},
            },
        }

    for shape in action_inputs:
        required_props: List[str] = []
        properties: Dict[str, Any] = {}
        for f in shape.get("fields", []):
            prop = camel_case(f["name"])
            field_schema = json_schema_for_field(f, type_by_id, object_by_id, struct_by_id)
            if isinstance(field_schema, dict):
                _apply_display_name_hint(field_schema, f)
            properties[prop] = field_schema
            if f.get("cardinality", {}).get("min", 0) > 0:
                required_props.append(prop)
        components_schemas[shape["name"]] = {
            "type": "object",
            "required": required_props,
            "properties": properties,
        }
        _apply_display_name_hint(components_schemas[shape["name"]], shape)
        if shape.get("description"):
            components_schemas[shape["name"]]["description"] = shape["description"]

    for event in events:
        if not isinstance(event, dict):
            continue
        event_name = str(event.get("name", "Event"))
        required_props: List[str] = []
        properties: Dict[str, Any] = {}
        for f in [field for field in event.get("fields", []) if isinstance(field, dict)]:
            prop = camel_case(str(f.get("name", "field")))
            field_schema = json_schema_for_field(f, type_by_id, object_by_id, struct_by_id)
            if isinstance(field_schema, dict):
                _apply_display_name_hint(field_schema, f)
            properties[prop] = field_schema
            if f.get("cardinality", {}).get("min", 0) > 0:
                required_props.append(prop)
        components_schemas[event_name] = {
            "type": "object",
            "required": required_props,
            "properties": properties,
        }
        _apply_display_name_hint(components_schemas[event_name], event)
        if event.get("description"):
            components_schemas[event_name]["description"] = event["description"]

    paths: Dict[str, Any] = {}

    for obj in objects:
        fields = obj.get("fields", [])
        pk_fields = primary_key_fields_for_object(obj)
        pk = pk_fields[0]
        table = pluralize(snake_case(obj["name"]))
        pk_param = camel_case(pk["name"])
        query_filter_props: Dict[str, Any] = {}
        list_parameters: List[Dict[str, Any]] = [
            {
                "name": "page",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "minimum": 0, "default": 0},
            },
            {
                "name": "size",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "minimum": 1, "default": 20},
            },
            {
                "name": "sort",
                "in": "query",
                "required": False,
                "schema": {"type": "string"},
                "description": "Sort expression, for example field,asc",
            },
        ]

        def field_base_type(field_type: Dict[str, Any]) -> Optional[str]:
            if field_type["kind"] == "base":
                return str(field_type["name"])
            if field_type["kind"] == "custom":
                return str(type_by_id[field_type["target_type_id"]]["base"])
            return None

        for f in fields:
            kind = f["type"]["kind"]
            if kind in {"list", "struct"}:
                continue

            if kind == "object_ref":
                target = object_by_id[f["type"]["target_object_id"]]
                target_pk = primary_key_field_for_object(target)
                param_name = f"{camel_case(f['name'])}{pascal_case(camel_case(target_pk['name']))}"
                param_schema = json_schema_for_field(target_pk, type_by_id, object_by_id, struct_by_id)
            else:
                param_name = camel_case(f["name"])
                param_schema = json_schema_for_field(f, type_by_id, object_by_id, struct_by_id)

            filter_name = f"{obj['name']}{pascal_case(param_name)}Filter"
            filter_props: Dict[str, Any] = {"eq": param_schema}
            if kind == "object_ref":
                filter_props["in"] = {"type": "array", "items": param_schema}
            else:
                base_t = field_base_type(f["type"])
                if base_t in {"string", "duration"}:
                    filter_props["in"] = {"type": "array", "items": param_schema}
                    filter_props["contains"] = {"type": "string"}
                elif base_t in {"int", "long", "short", "byte", "double", "float", "decimal", "date", "datetime"}:
                    filter_props["in"] = {"type": "array", "items": param_schema}
                    filter_props["gte"] = param_schema
                    filter_props["lte"] = param_schema
                elif base_t != "boolean":
                    filter_props["in"] = {"type": "array", "items": param_schema}
            components_schemas[filter_name] = {"type": "object", "properties": filter_props}
            query_filter_props[param_name] = {"$ref": f"#/components/schemas/{filter_name}"}

        if obj.get("states"):
            state_filter_name = f"{obj['name']}StateFilter"
            enum_schema = {
                "type": "string",
                "enum": [s["name"].upper() for s in obj["states"]],
            }
            components_schemas[state_filter_name] = {
                "type": "object",
                "properties": {
                    "eq": enum_schema,
                    "in": {"type": "array", "items": enum_schema},
                },
            }
            query_filter_props["state"] = {"$ref": f"#/components/schemas/{state_filter_name}"}

        query_filter_name = f"{obj['name']}QueryFilter"
        components_schemas[query_filter_name] = {"type": "object", "properties": query_filter_props}

        paths[f"/{table}"] = {
            "get": {
                "operationId": f"list{obj['name']}",
                "parameters": list_parameters,
                "responses": {
                    "200": {
                        "description": f"Paginated {obj['name']} list response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{obj['name']}ListResponse"}
                            }
                        },
                    }
                },
            }
        }
        paths[f"/{table}/query"] = {
            "post": {
                "operationId": f"query{obj['name']}",
                "parameters": list_parameters[:3],
                "requestBody": {
                    "required": False,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{query_filter_name}"}
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": f"Paginated {obj['name']} list response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{obj['name']}ListResponse"}
                            }
                        },
                    }
                },
            }
        }
        pk_path_parts: List[str] = []
        pk_params: List[Dict[str, Any]] = []
        for key_field in pk_fields:
            key_name = camel_case(key_field["name"])
            pk_path_parts.append(f"{{{key_name}}}")
            pk_params.append(
                {
                    "name": key_name,
                    "in": "path",
                    "required": True,
                    "schema": json_schema_for_field(key_field, type_by_id, object_by_id, struct_by_id),
                }
            )
        pk_path = "/".join(pk_path_parts) if pk_path_parts else f"{{{pk_param}}}"
        paths[f"/{table}/{pk_path}"] = {
            "get": {
                "operationId": f"get{obj['name']}",
                "parameters": pk_params or [
                    {
                        "name": pk_param,
                        "in": "path",
                        "required": True,
                        "schema": json_schema_for_field(pk, type_by_id, object_by_id, struct_by_id),
                    }
                ],
                "responses": {
                    "200": {
                        "description": f"{obj['name']} found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{obj['name']}"}
                            }
                        },
                    },
                    "404": {"description": "Not found"},
                },
            }
        }

    for action in actions:
        req_name = action_input_by_id[action["input_shape_id"]]["name"]
        event_name = str(event_by_id.get(action["output_event_id"], {}).get("name", "Event"))
        op_id = f"{camel_case(action['name'])}Action"
        paths[f"/actions/{action['name']}"] = {
            "post": {
                "operationId": op_id,
                **(
                    {"summary": action["description"]}
                    if action.get("description")
                    else (
                        {"summary": _resolved_display_name(action)}
                        if _resolved_display_name(action)
                        else {}
                    )
                ),
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{req_name}"}
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Action response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{event_name}"}
                            }
                        },
                    }
                },
            }
        }

    spec = {
        "openapi": "3.1.0",
        "info": {
            "title": f"{str(ir.get('ontology', {}).get('display_name') or pascal_case(ir['ontology']['name']) or ir['ontology']['name'])} API",
            "version": ir["ontology"]["version"],
        },
        "servers": [{"url": "https://api.example.com"}],
        "paths": paths,
        "components": {"schemas": components_schemas},
    }
    return yaml_dump_stable(spec)


def compute_delta_from_baseline(
    root: Path, cfg: Dict[str, Any], ir: Dict[str, Any]
) -> Tuple[Optional[str], List[str], Optional[Path], Optional[str], Dict[str, Any]]:
    baseline_rel = str(cfg_get(cfg, ["compatibility", "baseline_ir"], ".prophet/baselines/main.ir.json"))
    baseline_path = root / baseline_rel
    if not baseline_path.exists():
        return None, [], None, None, {"safe_auto_apply_count": 0, "manual_review_count": 0, "destructive_count": 0, "findings": []}
    baseline_ir = json.loads(baseline_path.read_text(encoding="utf-8"))
    delta_sql, delta_warnings, has_delta, delta_meta = render_delta_migration(baseline_ir, ir)
    if not has_delta:
        return (
            None,
            [],
            baseline_path,
            str(baseline_ir.get("ir_hash")) if baseline_ir.get("ir_hash") else None,
            delta_meta,
        )
    return (
        delta_sql,
        delta_warnings,
        baseline_path,
        str(baseline_ir.get("ir_hash")) if baseline_ir.get("ir_hash") else None,
        delta_meta,
    )
