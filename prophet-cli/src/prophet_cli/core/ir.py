from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from .compatibility import build_query_contracts
from .models import FieldDef
from .models import Ontology
from .parser import resolve_type_descriptor


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
    action_output_name_to_id = {s.name: s.id for s in ont.action_outputs}
    action_name_to_id = {a.name: a.id for a in ont.actions}

    def sorted_by_id(items: List[Any]) -> List[Any]:
        return sorted(items, key=lambda x: x.id)

    types = []
    for t in sorted_by_id(ont.types):
        types.append(
            {
                "id": t.id,
                "name": t.name,
                "kind": "custom",
                "base": t.base,
                "constraints": dict(sorted(t.constraints.items())),
            }
        )

    objects = []
    for o in sorted_by_id(ont.objects):
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
            obj_fields.append(f_entry)

        state_name_to_id = {s.name: s.id for s in o.states}
        obj_states = [{"id": s.id, "name": s.name, "initial": s.initial} for s in o.states]
        obj_transitions = []
        for t in o.transitions:
            obj_transitions.append(
                {
                    "id": t.id,
                    "name": t.name,
                    "from_state_id": state_name_to_id[t.from_state],
                    "to_state_id": state_name_to_id[t.to_state],
                }
            )

        objects.append(
            {
                "id": o.id,
                "name": o.name,
                "fields": obj_fields,
                "states": obj_states,
                "transitions": obj_transitions,
            }
        )

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
        structs.append(
            {
                "id": s.id,
                "name": s.name,
                "fields": struct_fields,
            }
        )

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
        action_inputs.append(
            {
                "id": shape.id,
                "name": shape.name,
                "fields": shape_fields,
            }
        )

    action_outputs = []
    for shape in sorted_by_id(ont.action_outputs):
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
        action_outputs.append(
            {
                "id": shape.id,
                "name": shape.name,
                "fields": shape_fields,
            }
        )

    event_name_to_id = {e.name: e.id for e in ont.events}

    actions = []
    for a in sorted_by_id(ont.actions):
        actions.append(
            {
                "id": a.id,
                "name": a.name,
                "kind": a.kind,
                "input_shape_id": action_input_name_to_id[a.input_shape],
                "output_shape_id": action_output_name_to_id[a.output_shape],
            }
        )

    obj_name_to_states = {o.name: {s.name: s.id for s in o.states} for o in ont.objects}

    events = []
    for e in sorted_by_id(ont.events):
        entry = {
            "id": e.id,
            "name": e.name,
            "kind": e.kind,
            "object_id": object_name_to_id[e.object_name],
        }
        if e.action:
            entry["action_id"] = action_name_to_id[e.action]
        if e.from_state:
            entry["from_state_id"] = obj_name_to_states[e.object_name][e.from_state]
        if e.to_state:
            entry["to_state_id"] = obj_name_to_states[e.object_name][e.to_state]
        events.append(entry)

    triggers = []
    for t in sorted_by_id(ont.triggers):
        triggers.append(
            {
                "id": t.id,
                "name": t.name,
                "event_id": event_name_to_id[t.event_name],
                "action_id": action_name_to_id[t.action_name],
            }
        )

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
        "action_outputs": action_outputs,
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

    ir["query_contracts"] = build_query_contracts(ir)
    contract_canonical = json.dumps(ir["query_contracts"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    ir["query_contracts_version"] = hashlib.sha256(contract_canonical).hexdigest()
    canonical = json.dumps(ir, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ir["ir_hash"] = hashlib.sha256(canonical).hexdigest()
    return ir

