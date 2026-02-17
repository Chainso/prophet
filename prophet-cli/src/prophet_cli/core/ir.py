from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from .compatibility import build_query_contracts
from .models import FieldDef
from .models import Ontology
from .parser import resolve_type_descriptor


def _pascal_case(value: str) -> str:
    chunks = [part for part in value.replace("-", "_").split("_") if part]
    return "".join(chunk[:1].upper() + chunk[1:] for chunk in chunks)


def transition_event_name(object_name: str, transition_name: str) -> str:
    return f"{object_name}{_pascal_case(transition_name)}Transition"


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
    object_name_to_id: Dict[str, str],
    struct_name_to_id: Dict[str, str],
) -> Dict[str, Any]:
    return resolve_type_descriptor(field.type_raw, type_name_to_id, object_name_to_id, struct_name_to_id)


def build_ir(
    ont: Ontology,
    cfg: Dict[str, Any],
    toolchain_version: str,
    ir_version: str,
) -> Dict[str, Any]:
    type_name_to_id = {t.name: t.id for t in ont.types}
    object_name_to_id = {o.name: o.id for o in ont.objects}
    struct_name_to_id = {s.name: s.id for s in ont.structs}
    action_input_name_to_id = {s.name: s.id for s in ont.action_inputs}
    action_name_to_id = {a.name: a.id for a in ont.actions}

    def sorted_by_id(items: List[Any]) -> List[Any]:
        return sorted(items, key=lambda x: x.id)

    types = []
    for t in sorted_by_id(ont.types):
        entry = {
            "id": t.id,
            "name": t.name,
            "kind": "custom",
            "base": t.base,
            "constraints": dict(sorted(t.constraints.items())),
        }
        if t.description:
            entry["description"] = t.description
        types.append(entry)

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
            resolved_type = resolve_field_type(f, type_name_to_id, object_name_to_id, struct_name_to_id)
            max_cardinality: Any = "many" if resolved_type.get("kind") == "list" else 1
            card = {"min": 1 if f.required else 0, "max": max_cardinality}
            f_entry = {
                "id": f.id,
                "name": f.name,
                "type": resolved_type,
                "cardinality": card,
            }
            if f.key:
                f_entry["key"] = f.key
            if f.description:
                f_entry["description"] = f.description
            obj_fields.append(f_entry)

        state_name_to_id = {s.name: s.id for s in o.states}
        obj_states = []
        for s in o.states:
            state_entry = {"id": s.id, "name": s.name, "initial": s.initial}
            if s.description:
                state_entry["description"] = s.description
            obj_states.append(state_entry)
        obj_transitions = []
        for t in o.transitions:
            transition_entry = {
                "id": t.id,
                "name": t.name,
                "from_state_id": state_name_to_id[t.from_state],
                "to_state_id": state_name_to_id[t.to_state],
            }
            if t.description:
                transition_entry["description"] = t.description
            obj_transitions.append(transition_entry)

        obj_entry = {
            "id": o.id,
            "name": o.name,
            "fields": obj_fields,
            "keys": {
                "primary": {"field_ids": [field_id_by_name[name] for name in primary_key_field_names if name in field_id_by_name]},
                "display": {"field_ids": [field_id_by_name[name] for name in display_key_field_names if name in field_id_by_name]},
            },
            "states": obj_states,
            "transitions": obj_transitions,
        }
        if o.description:
            obj_entry["description"] = o.description
        objects.append(obj_entry)

    structs = []
    for s in sorted_by_id(ont.structs):
        struct_fields = []
        for f in s.fields:
            resolved_type = resolve_field_type(f, type_name_to_id, object_name_to_id, struct_name_to_id)
            max_cardinality: Any = "many" if resolved_type.get("kind") == "list" else 1
            struct_fields.append(
                {
                    "id": f.id,
                    "name": f.name,
                    "type": resolved_type,
                    "cardinality": {"min": 1 if f.required else 0, "max": max_cardinality},
                }
            )
            if f.description:
                struct_fields[-1]["description"] = f.description
        struct_entry = {
            "id": s.id,
            "name": s.name,
            "fields": struct_fields,
        }
        if s.description:
            struct_entry["description"] = s.description
        structs.append(struct_entry)

    action_inputs = []
    for shape in sorted_by_id(ont.action_inputs):
        shape_fields = []
        for f in shape.fields:
            resolved_type = resolve_field_type(f, type_name_to_id, object_name_to_id, struct_name_to_id)
            max_cardinality = "many" if resolved_type.get("kind") == "list" else 1
            shape_fields.append(
                {
                    "id": f.id,
                    "name": f.name,
                    "type": resolved_type,
                    "cardinality": {"min": 1 if f.required else 0, "max": max_cardinality},
                }
            )
            if f.description:
                shape_fields[-1]["description"] = f.description
        action_input_entry = {
            "id": shape.id,
            "name": shape.name,
            "fields": shape_fields,
        }
        if shape.description:
            action_input_entry["description"] = shape.description
        action_inputs.append(action_input_entry)

    obj_name_to_states = {o.name: {s.name: s.id for s in o.states} for o in ont.objects}

    event_name_to_id: Dict[str, str] = {}
    events = []
    for e in sorted_by_id(ont.events):
        entry = {
            "id": e.id,
            "name": e.name,
            "kind": "signal",
            "fields": [],
        }
        if e.description:
            entry["description"] = e.description
        signal_fields = []
        for f in e.fields:
            resolved_type = resolve_field_type(f, type_name_to_id, object_name_to_id, struct_name_to_id)
            max_cardinality = "many" if resolved_type.get("kind") == "list" else 1
            signal_field_entry = {
                "id": f.id,
                "name": f.name,
                "type": resolved_type,
                "cardinality": {"min": 1 if f.required else 0, "max": max_cardinality},
            }
            if f.description:
                signal_field_entry["description"] = f.description
            signal_fields.append(signal_field_entry)
        entry["fields"] = signal_fields
        events.append(entry)
        event_name_to_id[e.name] = e.id

    def primary_key_fields_for_object(obj: Any) -> List[FieldDef]:
        field_names = [f.name for f in obj.fields]
        field_level_keys: Dict[str, List[str]] = {}
        for fld in obj.fields:
            if fld.key:
                field_level_keys.setdefault(fld.key, []).append(fld.name)
        primary_key_names = _effective_object_key_field_names(field_names, obj.keys, field_level_keys, "primary")
        field_by_name = {fld.name: fld for fld in obj.fields}
        return [field_by_name[name] for name in primary_key_names if name in field_by_name]

    for obj in sorted_by_id(ont.objects):
        primary_key_fields = primary_key_fields_for_object(obj)
        for tr in sorted(obj.transitions, key=lambda x: x.id):
            transition_name = transition_event_name(obj.name, tr.name)
            transition_fields = []
            for pk_field in primary_key_fields:
                resolved_type = resolve_field_type(pk_field, type_name_to_id, object_name_to_id, struct_name_to_id)
                transition_fields.append(
                    {
                        "id": f"{tr.id}__pk__{pk_field.id}",
                        "name": pk_field.name,
                        "type": resolved_type,
                        "cardinality": {"min": 1, "max": 1},
                    }
                )
            transition_fields.extend(
                [
                    {
                        "id": f"{tr.id}__from_state",
                        "name": "fromState",
                        "type": {"kind": "base", "name": "string"},
                        "cardinality": {"min": 1, "max": 1},
                    },
                    {
                        "id": f"{tr.id}__to_state",
                        "name": "toState",
                        "type": {"kind": "base", "name": "string"},
                        "cardinality": {"min": 1, "max": 1},
                    },
                ]
            )
            for transition_field in tr.fields:
                resolved_type = resolve_field_type(
                    transition_field,
                    type_name_to_id,
                    object_name_to_id,
                    struct_name_to_id,
                )
                max_cardinality = "many" if resolved_type.get("kind") == "list" else 1
                transition_field_entry = {
                    "id": transition_field.id,
                    "name": transition_field.name,
                    "type": resolved_type,
                    "cardinality": {"min": 1 if transition_field.required else 0, "max": max_cardinality},
                }
                if transition_field.description:
                    transition_field_entry["description"] = transition_field.description
                transition_fields.append(transition_field_entry)
            transition_entry = {
                "id": tr.id,
                "name": transition_name,
                "kind": "transition",
                "fields": transition_fields,
                "object_id": object_name_to_id[obj.name],
                "transition_id": tr.id,
                "from_state_id": obj_name_to_states[obj.name][tr.from_state],
                "to_state_id": obj_name_to_states[obj.name][tr.to_state],
            }
            if tr.description:
                transition_entry["description"] = tr.description
            events.append(transition_entry)
            event_name_to_id[transition_name] = tr.id

    actions = []
    for a in sorted_by_id(ont.actions):
        action_entry = {
            "id": a.id,
            "name": a.name,
            "kind": a.kind,
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
            "version": ont.version,
        },
        "types": types,
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
