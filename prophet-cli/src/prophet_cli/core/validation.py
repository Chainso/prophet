from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .constants import BASE_TYPES
from .errors import ProphetError
from .models import FieldDef
from .models import ObjectDef
from .models import Ontology
from .models import StructDef
from .models import TypeDef
from .parser import resolve_type_descriptor

RESERVED_FIELD_PREFIXES = ("__prophet_",)


def _validate_reserved_field_name(
    owner: str,
    field: FieldDef,
    errors: List[str],
) -> None:
    for prefix in RESERVED_FIELD_PREFIXES:
        if field.name.startswith(prefix):
            errors.append(
                f"line {field.line}: field {owner}.{field.name} uses reserved prefix '{prefix}'"
            )
            break


def _effective_key_field_names(
    obj: ObjectDef,
    kind: str,
    errors: List[str],
) -> Optional[List[str]]:
    object_level = [k for k in obj.keys if k.kind == kind]
    field_level = [f.name for f in obj.fields if f.key == kind]
    if len(object_level) > 1:
        dup_lines = ", ".join(str(k.line) for k in object_level)
        errors.append(
            f"line {obj.line}: object {obj.name} declares key {kind} multiple times (lines: {dup_lines})"
        )
    if object_level:
        names = list(object_level[0].field_names)
        if field_level and set(field_level) != set(names):
            errors.append(
                f"line {obj.line}: object {obj.name} mixes object-level and field-level key {kind} declarations with different fields"
            )
        return names
    if field_level:
        return field_level
    return None


def validate_type_expr(
    type_raw: str,
    type_names: Dict[str, TypeDef],
    enum_name_to_id: Dict[str, str],
    object_names: Dict[str, ObjectDef],
    struct_names: Dict[str, StructDef],
) -> str | None:
    try:
        resolve_type_descriptor(
            type_raw,
            {t.name: t.id for t in type_names.values()},
            enum_name_to_id,
            {o.name: o.id for o in object_names.values()},
            {s.name: s.id for s in struct_names.values()},
        )
    except ProphetError as exc:
        return str(exc)
    return None


def validate_ontology(ont: Ontology, strict_enums: bool = False) -> List[str]:
    errors: List[str] = []

    id_entries: List[Tuple[str, str, int]] = [("ontology", ont.id, 1)]
    for t in ont.types:
        id_entries.append((f"type {t.name}", t.id, t.line))
    for enum in ont.enums:
        id_entries.append((f"enum {enum.name}", enum.id, enum.line))
        for value in enum.values:
            id_entries.append((f"enumValue {enum.name}.{value.name}", value.id, value.line))
    for o in ont.objects:
        id_entries.append((f"object {o.name}", o.id, o.line))
        for f in o.fields:
            id_entries.append((f"field {o.name}.{f.name}", f.id, f.line))
    for s in ont.structs:
        id_entries.append((f"struct {s.name}", s.id, s.line))
        for f in s.fields:
            id_entries.append((f"field {s.name}.{f.name}", f.id, f.line))
    for shape in ont.action_inputs:
        id_entries.append((f"actionInput {shape.name}", shape.id, shape.line))
        for f in shape.fields:
            id_entries.append((f"field {shape.name}.{f.name}", f.id, f.line))
    for a in ont.actions:
        id_entries.append((f"action {a.name}", a.id, a.line))
    for e in ont.events:
        id_entries.append((f"event {e.name}", e.id, e.line))
        for f in e.fields:
            id_entries.append((f"field {e.name}.{f.name}", f.id, f.line))
    for t in ont.triggers:
        id_entries.append((f"trigger {t.name}", t.id, t.line))

    seen_ids: Dict[str, Tuple[str, int]] = {}
    for label, val, ln in id_entries:
        if val in seen_ids:
            prev_label, prev_ln = seen_ids[val]
            errors.append(f"line {ln}: duplicate id '{val}' used by {label} and {prev_label} (line {prev_ln})")
        else:
            seen_ids[val] = (label, ln)

    type_names = {t.name: t for t in ont.types}
    enum_name_to_id = {enum.name: enum.id for enum in ont.enums}
    object_names = {o.name: o for o in ont.objects}
    struct_names = {s.name: s for s in ont.structs}
    action_input_names = {s.name: s for s in ont.action_inputs}
    action_names = {a.name: a for a in ont.actions}
    event_names = {e.name: e for e in ont.events}
    enum_values_by_name = {enum.name: {value.name: value.id for value in enum.values} for enum in ont.enums}

    type_namespace: Dict[str, Tuple[str, int]] = {}

    def _register_type_namespace(name: str, label: str, line: int) -> None:
        existing = type_namespace.get(name)
        if existing is not None:
            errors.append(
                f"line {line}: type namespace name '{name}' collides with {existing[0]} (line {existing[1]})"
            )
            return
        type_namespace[name] = (label, line)

    for t in ont.types:
        _register_type_namespace(t.name, f"type {t.name}", t.line)
        if t.base not in BASE_TYPES:
            errors.append(f"line {t.line}: type {t.name} base '{t.base}' is not a supported base type")

    for enum in ont.enums:
        _register_type_namespace(enum.name, f"enum {enum.name}", enum.line)
        if not enum.values:
            errors.append(f"line {enum.line}: enum {enum.name} must declare at least one value")
        seen_value_names: Dict[str, int] = {}
        seen_value_ids: Dict[str, int] = {}
        for value in enum.values:
            previous_name_line = seen_value_names.get(value.name)
            if previous_name_line is not None:
                errors.append(
                    f"line {value.line}: enum {enum.name} declares duplicate value '{value.name}' (line {previous_name_line})"
                )
            else:
                seen_value_names[value.name] = value.line
            previous_id_line = seen_value_ids.get(value.id)
            if previous_id_line is not None:
                errors.append(
                    f"line {value.line}: enum {enum.name} uses duplicate value id '{value.id}' (line {previous_id_line})"
                )
            else:
                seen_value_ids[value.id] = value.line

    for s in ont.structs:
        _register_type_namespace(s.name, f"struct {s.name}", s.line)

    def _validate_non_object_field(owner_kind: str, owner_name: str, field: FieldDef) -> None:
        _validate_reserved_field_name(owner_name, field, errors)
        if field.key is not None:
            errors.append(
                f"line {field.line}: {owner_kind} {owner_name}.{field.name} must not declare key (keys are only valid on object fields)"
            )
        if field.is_state_field:
            errors.append(
                f"line {field.line}: {owner_kind} {owner_name}.{field.name} must not be marked as state"
            )
        if field.initial_enum_value is not None:
            errors.append(
                f"line {field.line}: {owner_kind} {owner_name}.{field.name} must not declare an initial enum value"
            )
        type_error = validate_type_expr(
            field.type_raw,
            type_names,
            enum_name_to_id,
            object_names,
            struct_names,
        )
        if type_error:
            errors.append(f"line {field.line}: field {owner_name}.{field.name} {type_error}")

    for o in ont.objects:
        for key_def in o.keys:
            if key_def.kind not in {"primary", "display"}:
                errors.append(
                    f"line {key_def.line}: object {o.name} key kind '{key_def.kind}' is invalid; expected primary or display"
                )

        field_by_name = {f.name: f for f in o.fields}
        primary_field_names = _effective_key_field_names(o, "primary", errors)
        if not primary_field_names:
            errors.append(f"line {o.line}: object {o.name} must declare at least one primary key field")
        else:
            if len(set(primary_field_names)) != len(primary_field_names):
                errors.append(f"line {o.line}: object {o.name} primary key must not repeat fields")
            for field_name in primary_field_names:
                if field_name not in field_by_name:
                    errors.append(
                        f"line {o.line}: object {o.name} key primary references unknown field '{field_name}'"
                    )
                    continue
                if not field_by_name[field_name].required:
                    errors.append(
                        f"line {field_by_name[field_name].line}: object {o.name} primary key field {field_name} must be required"
                    )

        display_field_names = _effective_key_field_names(o, "display", errors)
        if display_field_names is not None:
            if len(set(display_field_names)) != len(display_field_names):
                errors.append(f"line {o.line}: object {o.name} display key must not repeat fields")
            for field_name in display_field_names:
                if field_name not in field_by_name:
                    errors.append(
                        f"line {o.line}: object {o.name} key display references unknown field '{field_name}'"
                    )

        state_fields = [field for field in o.fields if field.is_state_field]
        if len(state_fields) > 1:
            errors.append(f"line {o.line}: object {o.name} may declare at most one state field")

        for f in o.fields:
            _validate_reserved_field_name(o.name, f, errors)
            if f.key is not None and f.key not in {"primary", "display"}:
                errors.append(
                    f"line {f.line}: field {o.name}.{f.name} key kind '{f.key}' is invalid; expected primary or display"
                )

            type_error = validate_type_expr(
                f.type_raw,
                type_names,
                enum_name_to_id,
                object_names,
                struct_names,
            )
            if type_error:
                errors.append(f"line {f.line}: field {o.name}.{f.name} {type_error}")
                continue

            descriptor = resolve_type_descriptor(
                f.type_raw,
                {t.name: t.id for t in type_names.values()},
                enum_name_to_id,
                {obj.name: obj.id for obj in object_names.values()},
                {s.name: s.id for s in struct_names.values()},
            )

            if primary_field_names and f.name in set(primary_field_names):
                if descriptor.get("kind") not in {"base", "custom", "enum"}:
                    errors.append(
                        f"line {f.line}: field {o.name}.{f.name} cannot be used in a primary key (only base/custom/enum scalar types are supported)"
                    )

            if f.is_state_field:
                if descriptor.get("kind") != "enum":
                    errors.append(f"line {f.line}: state field {o.name}.{f.name} must use an enum type")
                if f.initial_enum_value is None:
                    errors.append(f"line {f.line}: state field {o.name}.{f.name} must declare an initial enum value")
                elif descriptor.get("kind") == "enum":
                    target_enum_id = str(descriptor.get("target_enum_id", ""))
                    target_enum_name = next(
                        (enum.name for enum in ont.enums if enum.id == target_enum_id),
                        None,
                    )
                    if target_enum_name is not None and f.initial_enum_value not in enum_values_by_name[target_enum_name]:
                        errors.append(
                            f"line {f.line}: state field {o.name}.{f.name} initial value '{f.initial_enum_value}' is not a member of enum {target_enum_name}"
                        )
            elif f.initial_enum_value is not None:
                errors.append(
                    f"line {f.line}: field {o.name}.{f.name} must be marked as state before declaring an initial enum value"
                )

    for s in ont.structs:
        for f in s.fields:
            _validate_non_object_field("struct", s.name, f)

    for shape in ont.action_inputs:
        for f in shape.fields:
            _validate_non_object_field("actionInput", shape.name, f)

    for e in ont.events:
        for f in e.fields:
            _validate_non_object_field("event", e.name, f)

    for a in ont.actions:
        if a.input_shape not in action_input_names:
            errors.append(f"line {a.line}: action {a.name} input shape '{a.input_shape}' not found")
        if a.produces_event not in event_names:
            errors.append(f"line {a.line}: action {a.name} output event '{a.produces_event}' not found")

    for tr in ont.triggers:
        if tr.event_name not in event_names:
            errors.append(f"line {tr.line}: trigger {tr.name} references unknown event '{tr.event_name}'")
        if tr.action_name not in action_names:
            errors.append(f"line {tr.line}: trigger {tr.name} references unknown action '{tr.action_name}'")

    object_primary_counts: Dict[str, int] = {}
    for obj in ont.objects:
        primary_field_names = _effective_key_field_names(obj, "primary", [])
        object_primary_counts[obj.name] = len(primary_field_names or [])

    for obj in ont.objects:
        for field in obj.fields:
            descriptor_error = validate_type_expr(
                field.type_raw,
                type_names,
                enum_name_to_id,
                object_names,
                struct_names,
            )
            if descriptor_error:
                continue
            descriptor = resolve_type_descriptor(
                field.type_raw,
                {t.name: t.id for t in type_names.values()},
                enum_name_to_id,
                {object_model.name: object_model.id for object_model in ont.objects},
                {struct.name: struct.id for struct in ont.structs},
            )
            if descriptor.get("kind") != "object_ref":
                continue
            target_object_id = descriptor.get("target_object_id")
            target_name = next((candidate.name for candidate in ont.objects if candidate.id == target_object_id), None)
            if target_name is None:
                continue
            if object_primary_counts.get(target_name, 0) != 1:
                errors.append(
                    f"line {field.line}: field {obj.name}.{field.name} references object {target_name} which does not have exactly one primary key field (object refs currently require single-field primary keys)"
                )

    return errors
