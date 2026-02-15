from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .constants import BASE_TYPES
from .models import FieldDef
from .models import ObjectDef
from .models import Ontology
from .models import StructDef
from .models import TypeDef
from .parser import resolve_type_descriptor
from .errors import ProphetError


def _pascal_case(value: str) -> str:
    chunks = [part for part in value.replace("-", "_").split("_") if part]
    return "".join(chunk[:1].upper() + chunk[1:] for chunk in chunks)


def transition_event_name(object_name: str, transition_name: str) -> str:
    return f"{object_name}{_pascal_case(transition_name)}Transition"


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
    object_names: Dict[str, ObjectDef],
    struct_names: Dict[str, StructDef],
) -> str | None:
    try:
        resolve_type_descriptor(
            type_raw,
            {t.name: t.id for t in type_names.values()},
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
    for o in ont.objects:
        id_entries.append((f"object {o.name}", o.id, o.line))
        for f in o.fields:
            id_entries.append((f"field {o.name}.{f.name}", f.id, f.line))
        for s in o.states:
            id_entries.append((f"state {o.name}.{s.name}", s.id, s.line))
        for tr in o.transitions:
            id_entries.append((f"transition {o.name}.{tr.name}", tr.id, tr.line))
    for s in ont.structs:
        id_entries.append((f"struct {s.name}", s.id, s.line))
        for f in s.fields:
            id_entries.append((f"field {s.name}.{f.name}", f.id, f.line))
    for shape in ont.action_inputs:
        id_entries.append((f"actionInput {shape.name}", shape.id, shape.line))
        for f in shape.fields:
            id_entries.append((f"field {shape.name}.{f.name}", f.id, f.line))
    for shape in ont.action_outputs:
        id_entries.append((f"actionOutput {shape.name}", shape.id, shape.line))
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
    object_names = {o.name: o for o in ont.objects}
    struct_names = {s.name: s for s in ont.structs}
    action_input_names = {s.name: s for s in ont.action_inputs}
    action_output_names = {s.name: s for s in ont.action_outputs}
    action_names = {a.name: a for a in ont.actions}

    for t in ont.types:
        if t.base not in BASE_TYPES:
            errors.append(f"line {t.line}: type {t.name} base '{t.base}' is not a supported base type")

    for o in ont.objects:
        for key_def in o.keys:
            if key_def.kind not in {"primary", "display"}:
                errors.append(
                    f"line {key_def.line}: object {o.name} key kind '{key_def.kind}' is invalid; expected primary or display"
                )
        for f in o.fields:
            if f.key is not None and f.key not in {"primary", "display"}:
                errors.append(
                    f"line {f.line}: field {o.name}.{f.name} key kind '{f.key}' is invalid; expected primary or display"
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
                primary_field = field_by_name[field_name]
                if not primary_field.required:
                    errors.append(
                        f"line {primary_field.line}: object {o.name} primary key field {field_name} must be required"
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

        state_names = {s.name: s for s in o.states}
        if o.states:
            initials = [s for s in o.states if s.initial]
            if len(initials) != 1:
                errors.append(f"line {o.line}: object {o.name} with states must have exactly one initial state")

        for tr in o.transitions:
            if tr.from_state not in state_names:
                errors.append(f"line {tr.line}: transition {o.name}.{tr.name} from unknown state '{tr.from_state}'")
            if tr.to_state not in state_names:
                errors.append(f"line {tr.line}: transition {o.name}.{tr.name} to unknown state '{tr.to_state}'")

        for f in o.fields:
            type_error = validate_type_expr(f.type_raw, type_names, object_names, struct_names)
            if type_error:
                errors.append(f"line {f.line}: field {o.name}.{f.name} {type_error}")
                continue
            if primary_field_names and f.name in set(primary_field_names):
                descriptor = resolve_type_descriptor(
                    f.type_raw,
                    {t.name: t.id for t in type_names.values()},
                    {obj.name: obj.id for obj in object_names.values()},
                    {s.name: s.id for s in struct_names.values()},
                )
                if descriptor.get("kind") not in {"base", "custom"}:
                    errors.append(
                        f"line {f.line}: field {o.name}.{f.name} cannot be used in a primary key (only base/custom scalar types are supported)"
                    )

    for s in ont.structs:
        for f in s.fields:
            if f.key is not None:
                errors.append(f"line {f.line}: struct {s.name}.{f.name} must not declare key")
            type_error = validate_type_expr(f.type_raw, type_names, object_names, struct_names)
            if type_error:
                errors.append(f"line {f.line}: field {s.name}.{f.name} {type_error}")

    def validate_action_shape_fields(kind: str, shape_name: str, fields: List[FieldDef]) -> None:
        for f in fields:
            if f.key is not None:
                errors.append(
                    f"line {f.line}: {kind} {shape_name}.{f.name} must not declare key (keys are only valid on object fields)"
                )
            type_error = validate_type_expr(f.type_raw, type_names, object_names, struct_names)
            if type_error:
                errors.append(f"line {f.line}: field {shape_name}.{f.name} {type_error}")

    for shape in ont.action_inputs:
        validate_action_shape_fields("actionInput", shape.name, shape.fields)

    for shape in ont.action_outputs:
        validate_action_shape_fields("actionOutput", shape.name, shape.fields)

    for a in ont.actions:
        if a.kind not in {"process", "workflow"}:
            errors.append(f"line {a.line}: action {a.name} kind must be process or workflow")
        if a.input_shape not in action_input_names:
            errors.append(f"line {a.line}: action {a.name} input shape '{a.input_shape}' not found")
        if a.output_shape not in action_output_names:
            errors.append(f"line {a.line}: action {a.name} output shape '{a.output_shape}' not found")

    for signal in ont.events:
        if signal.kind != "signal":
            errors.append(
                f"line {signal.line}: signal {signal.name} has unsupported kind '{signal.kind}'"
            )
        validate_action_shape_fields("signal", signal.name, signal.fields)

    event_name_sources: Dict[str, str] = {}
    for signal in ont.events:
        event_name_sources[signal.name] = f"signal {signal.name}"
    for shape in ont.action_outputs:
        existing = event_name_sources.get(shape.name)
        if existing is not None:
            errors.append(
                f"line {shape.line}: actionOutput {shape.name} collides with event name from {existing}"
            )
        event_name_sources[shape.name] = f"actionOutput {shape.name}"
    for obj in ont.objects:
        for tr in obj.transitions:
            derived_name = transition_event_name(obj.name, tr.name)
            existing = event_name_sources.get(derived_name)
            if existing is not None:
                errors.append(
                    f"line {tr.line}: transition event name '{derived_name}' collides with {existing}"
                )
            event_name_sources[derived_name] = f"transition {obj.name}.{tr.name}"

    for tr in ont.triggers:
        if tr.event_name not in event_name_sources:
            errors.append(f"line {tr.line}: trigger {tr.name} references unknown event '{tr.event_name}'")
        if tr.action_name not in action_names:
            errors.append(f"line {tr.line}: trigger {tr.name} references unknown action '{tr.action_name}'")

    object_primary_counts: Dict[str, int] = {}
    for o in ont.objects:
        primary_field_names = _effective_key_field_names(o, "primary", [])
        object_primary_counts[o.name] = len(primary_field_names or [])
    for o in ont.objects:
        for f in o.fields:
            descriptor_error = validate_type_expr(f.type_raw, type_names, object_names, struct_names)
            if descriptor_error:
                continue
            descriptor = resolve_type_descriptor(
                f.type_raw,
                {t.name: t.id for t in type_names.values()},
                {obj.name: obj.id for obj in object_names.values()},
                {s.name: s.id for s in struct_names.values()},
            )
            if descriptor.get("kind") != "object_ref":
                continue
            target_object_id = descriptor.get("target_object_id")
            target_name = next((obj.name for obj in ont.objects if obj.id == target_object_id), None)
            if target_name is None:
                continue
            if object_primary_counts.get(target_name, 0) != 1:
                errors.append(
                    f"line {f.line}: field {o.name}.{f.name} references object {target_name} which does not have exactly one primary key field (object refs currently require single-field primary keys)"
                )

    if strict_enums:
        for o in ont.objects:
            if len({s.name for s in o.states}) != len(o.states):
                errors.append(f"line {o.line}: object {o.name} has duplicate state names")

    return errors
