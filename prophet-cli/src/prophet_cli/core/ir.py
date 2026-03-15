from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from .compatibility import build_query_contracts
from .models import FieldDef
from .models import Ontology
from .parser import resolve_type_descriptor


def _effective_object_key_field_names(
    field_names_in_order: List[str],
    key_declarations: List[Any],
    field_level_keys: Dict[str, List[str]],
    kind: str,
) -> List[str]:
    object_level = [k for k in key_declarations if k.kind == kind]
    if object_level:
        return [name for name in object_level[0].field_names if name in field_names_in_order]
    names = [name for name in field_level_keys.get(kind, []) if name in field_names_in_order]
    if kind == "primary" and not names and field_names_in_order:
        return [field_names_in_order[0]]
    return names


def cfg_get(cfg: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    cur: Any = cfg
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def resolve_field_type(
    field: FieldDef,
    type_name_to_id: Dict[str, str],
    enum_name_to_id: Dict[str, str],
    object_name_to_id: Dict[str, str],
    struct_name_to_id: Dict[str, str],
) -> Dict[str, Any]:
    return resolve_type_descriptor(field.type_raw, type_name_to_id, enum_name_to_id, object_name_to_id, struct_name_to_id)


def build_ir(
    ont: Ontology,
    cfg: Dict[str, Any],
    toolchain_version: str,
    ir_version: str,
) -> Dict[str, Any]:
    type_name_to_id = {t.name: t.id for t in ont.types}
    enum_name_to_id = {e.name: e.id for e in ont.enums}
    object_name_to_id = {o.name: o.id for o in ont.objects}
    struct_name_to_id = {s.name: s.id for s in ont.structs}
    action_input_name_to_id = {s.name: s.id for s in ont.action_inputs}
    action_name_to_id = {a.name: a.id for a in ont.actions}
    enum_values_by_enum_id = {
        enum.id: {value.name: value.id for value in enum.values}
        for enum in ont.enums
    }

    def sorted_by_id(items: List[Any]) -> List[Any]:
        return sorted(items, key=lambda x: x.id)

    def _resolved_display_name(symbol: str, display_name: Any) -> str:
        value = str(display_name or "").strip()
        return value if value else symbol

    types = []
    for t in sorted_by_id(ont.types):
        entry = {
            "id": t.id,
            "name": t.name,
            "display_name": _resolved_display_name(t.name, t.display_name),
            "kind": "custom",
            "base": t.base,
            "constraints": dict(sorted(t.constraints.items())),
        }
        if t.description:
            entry["description"] = t.description
        types.append(entry)

    enums = []
    for enum in sorted_by_id(ont.enums):
        entry = {
            "id": enum.id,
            "name": enum.name,
            "display_name": _resolved_display_name(enum.name, enum.display_name),
            "values": [],
        }
        if enum.description:
            entry["description"] = enum.description
        for value in enum.values:
            value_entry = {
                "id": value.id,
                "name": value.name,
                "display_name": _resolved_display_name(value.name, value.display_name),
            }
            if value.description:
                value_entry["description"] = value.description
            entry["values"].append(value_entry)
        enums.append(entry)

    objects = []
    for o in sorted_by_id(ont.objects):
        field_names = [f.name for f in o.fields]
        field_id_by_name = {f.name: f.id for f in o.fields}
        field_level_keys: Dict[str, List[str]] = {}
        for f in o.fields:
            if f.key:
                field_level_keys.setdefault(f.key, []).append(f.name)
        primary_key_field_names = _effective_object_key_field_names(field_names, o.keys, field_level_keys, "primary")
        display_key_field_names = _effective_object_key_field_names(field_names, o.keys, field_level_keys, "display")

        obj_fields = []
        for f in o.fields:
            resolved_type = resolve_field_type(f, type_name_to_id, enum_name_to_id, object_name_to_id, struct_name_to_id)
            max_cardinality: Any = "many" if resolved_type.get("kind") == "list" else 1
            card = {"min": 1 if f.required else 0, "max": max_cardinality}
            f_entry = {
                "id": f.id,
                "name": f.name,
                "display_name": _resolved_display_name(f.name, f.display_name),
                "type": resolved_type,
                "cardinality": card,
            }
            if f.key:
                f_entry["key"] = f.key
            if f.is_state_field:
                f_entry["is_state_field"] = True
                enum_id = str(resolved_type.get("target_enum_id", ""))
                if f.initial_enum_value is not None and enum_id in enum_values_by_enum_id:
                    initial_value_id = enum_values_by_enum_id[enum_id].get(f.initial_enum_value)
                    if initial_value_id is not None:
                        f_entry["initial_enum_value_id"] = initial_value_id
            if f.description:
                f_entry["description"] = f.description
            obj_fields.append(f_entry)

        obj_entry = {
            "id": o.id,
            "name": o.name,
            "display_name": _resolved_display_name(o.name, o.display_name),
            "fields": obj_fields,
            "keys": {
                "primary": {"field_ids": [field_id_by_name[name] for name in primary_key_field_names if name in field_id_by_name]},
                "display": {"field_ids": [field_id_by_name[name] for name in display_key_field_names if name in field_id_by_name]},
            },
        }
        if o.description:
            obj_entry["description"] = o.description
        objects.append(obj_entry)

    structs = []
    for s in sorted_by_id(ont.structs):
        struct_fields = []
        for f in s.fields:
            resolved_type = resolve_field_type(f, type_name_to_id, enum_name_to_id, object_name_to_id, struct_name_to_id)
            max_cardinality: Any = "many" if resolved_type.get("kind") == "list" else 1
            struct_fields.append(
                {
                    "id": f.id,
                    "name": f.name,
                    "display_name": _resolved_display_name(f.name, f.display_name),
                    "type": resolved_type,
                    "cardinality": {"min": 1 if f.required else 0, "max": max_cardinality},
                }
            )
            if f.description:
                struct_fields[-1]["description"] = f.description
        struct_entry = {
            "id": s.id,
            "name": s.name,
            "display_name": _resolved_display_name(s.name, s.display_name),
            "fields": struct_fields,
        }
        if s.description:
            struct_entry["description"] = s.description
        structs.append(struct_entry)

    action_inputs = []
    for shape in sorted_by_id(ont.action_inputs):
        shape_fields = []
        for f in shape.fields:
            resolved_type = resolve_field_type(f, type_name_to_id, enum_name_to_id, object_name_to_id, struct_name_to_id)
            max_cardinality = "many" if resolved_type.get("kind") == "list" else 1
            shape_fields.append(
                {
                    "id": f.id,
                    "name": f.name,
                    "display_name": _resolved_display_name(f.name, f.display_name),
                    "type": resolved_type,
                    "cardinality": {"min": 1 if f.required else 0, "max": max_cardinality},
                }
            )
            if f.description:
                shape_fields[-1]["description"] = f.description
        action_input_entry = {
            "id": shape.id,
            "name": shape.name,
            "display_name": _resolved_display_name(shape.name, shape.display_name),
            "fields": shape_fields,
        }
        if shape.description:
            action_input_entry["description"] = shape.description
        action_inputs.append(action_input_entry)

    event_name_to_id: Dict[str, str] = {}
    events = []
    for e in sorted_by_id(ont.events):
        entry = {
            "id": e.id,
            "name": e.name,
            "display_name": _resolved_display_name(e.name, e.display_name),
            "fields": [],
        }
        if e.description:
            entry["description"] = e.description
        event_fields = []
        for f in e.fields:
            resolved_type = resolve_field_type(f, type_name_to_id, enum_name_to_id, object_name_to_id, struct_name_to_id)
            max_cardinality = "many" if resolved_type.get("kind") == "list" else 1
            event_field_entry = {
                "id": f.id,
                "name": f.name,
                "display_name": _resolved_display_name(f.name, f.display_name),
                "type": resolved_type,
                "cardinality": {"min": 1 if f.required else 0, "max": max_cardinality},
            }
            if f.description:
                event_field_entry["description"] = f.description
            event_fields.append(event_field_entry)
        entry["fields"] = event_fields
        events.append(entry)
        event_name_to_id[e.name] = e.id

    actions = []
    for a in sorted_by_id(ont.actions):
        action_entry = {
            "id": a.id,
            "name": a.name,
            "display_name": _resolved_display_name(a.name, a.display_name),
            "input_shape_id": action_input_name_to_id[a.input_shape],
            "output_event_id": event_name_to_id[a.produces_event],
        }
        if a.description:
            action_entry["description"] = a.description
        actions.append(action_entry)

    triggers = []
    for t in sorted_by_id(ont.triggers):
        trigger_entry = {
            "id": t.id,
            "name": t.name,
            "display_name": _resolved_display_name(t.name, t.display_name),
            "event_id": event_name_to_id[t.event_name],
            "action_id": action_name_to_id[t.action_name],
        }
        if t.description:
            trigger_entry["description"] = t.description
        triggers.append(trigger_entry)

    ir = {
        "ir_version": ir_version,
        "toolchain_version": toolchain_version,
        "ontology_source_file": str(cfg_get(cfg, ["project", "ontology_file"], "")),
        "ontology": {
            "id": ont.id,
            "name": ont.name,
            "display_name": _resolved_display_name(ont.name, ont.display_name),
            "version": ont.version,
        },
        "types": types,
        "enums": enums,
        "objects": objects,
        "structs": structs,
        "action_inputs": action_inputs,
        "actions": actions,
        "events": events,
        "triggers": triggers,
        "query_contracts": [],
        "generation_profile": {
            "golden_stack": "spring_boot",
        },
        "compatibility_profile": {
            "strict_enums": bool(cfg_get(cfg, ["compatibility", "strict_enums"], False)),
            "list_scalar_shape_changes_are_breaking": True,
            "nested_list_shape_changes_are_breaking": True,
            "struct_field_contract_changes_are_breaking": True,
            "custom_type_constraint_changes_are_breaking": True,
        },
    }
    if ont.description:
        ir["ontology"]["description"] = ont.description

    ir["query_contracts"] = build_query_contracts(ir)
    contract_canonical = json.dumps(ir["query_contracts"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    ir["query_contracts_version"] = hashlib.sha256(contract_canonical).hexdigest()
    canonical = json.dumps(ir, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ir["ir_hash"] = hashlib.sha256(canonical).hexdigest()
    return ir
