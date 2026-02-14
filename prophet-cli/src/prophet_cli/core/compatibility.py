from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from .errors import ProphetError


def snake_case(value: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.replace("-", "_").lower()


def pluralize(value: str) -> str:
    if value.endswith("y") and len(value) > 1 and value[-2] not in "aeiou":
        return value[:-1] + "ies"
    if value.endswith("s"):
        return value + "es"
    return value + "s"


def camel_case(value: str) -> str:
    parts = [part for part in re.split(r"[_\-\s]+", value) if part]
    if not parts:
        return value
    head = parts[0][:1].lower() + parts[0][1:]
    tail = [p[:1].upper() + p[1:] for p in parts[1:]]
    return "".join([head] + tail)


def parse_semver(version: str) -> Tuple[int, int, int]:
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not m:
        raise ProphetError(f"Invalid semver '{version}'")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def required_level_to_bump(level: str) -> str:
    if level == "breaking":
        return "major"
    if level == "additive":
        return "minor"
    return "patch"


def bump_rank(bump: str) -> int:
    return {"patch": 1, "minor": 2, "major": 3}[bump]


def classify_type_change(old_t: Dict[str, Any], new_t: Dict[str, Any]) -> str:
    if old_t == new_t:
        return "non_functional"

    old_kind = old_t.get("kind")
    new_kind = new_t.get("kind")
    if old_kind != new_kind:
        return "breaking"

    widen_pairs = {("int", "long"), ("float", "double")}

    if old_kind == "base":
        old_name = old_t.get("name")
        new_name = new_t.get("name")
        if old_name == new_name:
            return "non_functional"
        if (old_name, new_name) in widen_pairs:
            return "additive"
        return "breaking"

    if old_kind == "custom":
        if old_t.get("target_type_id") != new_t.get("target_type_id"):
            return "breaking"

    if old_kind == "object_ref":
        if old_t.get("target_object_id") != new_t.get("target_object_id"):
            return "breaking"

    if old_kind == "list":
        return classify_type_change(old_t.get("element", {}), new_t.get("element", {}))

    return "non_functional"


def describe_type_descriptor(t: Dict[str, Any]) -> str:
    kind = t.get("kind")
    if kind == "base":
        return str(t.get("name", "unknown"))
    if kind == "custom":
        return f"custom({t.get('target_type_id', 'unknown')})"
    if kind == "object_ref":
        return f"ref({t.get('target_object_id', 'unknown')})"
    if kind == "struct":
        return f"struct({t.get('target_struct_id', 'unknown')})"
    if kind == "list":
        return f"list({describe_type_descriptor(t.get('element', {}))})"
    return "unknown"


def base_type_for_descriptor(
    type_desc: Dict[str, Any],
    type_by_id: Dict[str, Dict[str, Any]],
) -> Optional[str]:
    kind = type_desc.get("kind")
    if kind == "base":
        return str(type_desc.get("name"))
    if kind == "custom":
        target_type_id = type_desc.get("target_type_id")
        if target_type_id in type_by_id:
            return str(type_by_id[target_type_id].get("base"))
    return None


def query_filter_operators_for_field(
    field: Dict[str, Any],
    type_by_id: Dict[str, Dict[str, Any]],
) -> List[str]:
    field_type = field.get("type", {})
    kind = field_type.get("kind")
    if kind in {"list", "struct"}:
        return []
    if kind == "object_ref":
        return ["eq", "in"]

    base = base_type_for_descriptor(field_type, type_by_id)
    if base in {"string", "duration"}:
        return ["eq", "in", "contains"]
    if base in {"int", "long", "short", "byte", "double", "float", "decimal", "date", "datetime"}:
        return ["eq", "in", "gte", "lte"]
    if base == "boolean":
        return ["eq"]
    return ["eq", "in"]


def build_query_contracts(ir: Dict[str, Any]) -> List[Dict[str, Any]]:
    type_by_id = {t["id"]: t for t in ir.get("types", [])}
    contracts: List[Dict[str, Any]] = []

    for obj in sorted(ir.get("objects", []), key=lambda item: item.get("id", "")):
        path_table = pluralize(snake_case(obj["name"]))
        fields_by_id = {f.get("id"): f for f in obj.get("fields", []) if isinstance(f, dict)}
        key_field_ids = (
            obj.get("keys", {})
            .get("primary", {})
            .get("field_ids", [])
            if isinstance(obj.get("keys"), dict)
            else []
        )
        key_path_parts: List[str] = []
        if isinstance(key_field_ids, list):
            for field_id in key_field_ids:
                field = fields_by_id.get(field_id)
                if isinstance(field, dict):
                    key_path_parts.append("{" + camel_case(str(field.get("name", "id"))) + "}")
        if len(key_path_parts) <= 1:
            get_by_id_path = f"/{path_table}/{{id}}"
        else:
            get_by_id_path = f"/{path_table}/" + "/".join(key_path_parts)

        filters: List[Dict[str, Any]] = []
        for field in sorted(obj.get("fields", []), key=lambda item: item.get("id", "")):
            ops = query_filter_operators_for_field(field, type_by_id)
            if not ops:
                continue
            filters.append(
                {
                    "field_id": field["id"],
                    "field_name": field["name"],
                    "operators": ops,
                }
            )

        if obj.get("states"):
            filters.append(
                {
                    "field_id": "__current_state__",
                    "field_name": "currentState",
                    "operators": ["eq", "in"],
                }
            )

        contract = {
            "object_id": obj["id"],
            "object_name": obj["name"],
            "paths": {
                "list": f"/{path_table}",
                "get_by_id": get_by_id_path,
                "typed_query": f"/{path_table}/query",
            },
            "pageable": {
                "supported": True,
                "default_size": 20,
            },
            "filters": filters,
        }
        canonical = json.dumps(contract, sort_keys=True, separators=(",", ":")).encode("utf-8")
        contract["contract_hash"] = hashlib.sha256(canonical).hexdigest()
        contracts.append(contract)

    return contracts


def query_contract_map(ir: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    contracts = ir.get("query_contracts")
    if isinstance(contracts, list) and contracts:
        return {c["object_id"]: c for c in contracts if isinstance(c, dict) and c.get("object_id")}
    generated = build_query_contracts(ir)
    return {c["object_id"]: c for c in generated}


def compare_irs(old_ir: Dict[str, Any], new_ir: Dict[str, Any]) -> Tuple[str, List[str]]:
    findings: List[Tuple[str, str]] = []

    def add(level: str, msg: str) -> None:
        findings.append((level, msg))

    def compare_field_collections(context: str, old_fields_list: List[Dict[str, Any]], new_fields_list: List[Dict[str, Any]]) -> None:
        old_fields = {f["id"]: f for f in old_fields_list}
        new_fields = {f["id"]: f for f in new_fields_list}

        for fid in sorted(set(old_fields) - set(new_fields)):
            add("breaking", f"field removed: {context} field_id={fid}")
        for fid in sorted(set(new_fields) - set(old_fields)):
            if new_fields[fid]["cardinality"].get("min", 0) > 0:
                add("breaking", f"required field added: {context} field_id={fid}")
            else:
                add("additive", f"optional field added: {context} field_id={fid}")

        for fid in sorted(set(old_fields) & set(new_fields)):
            old_f = old_fields[fid]
            new_f = new_fields[fid]
            type_level = classify_type_change(old_f.get("type", {}), new_f.get("type", {}))
            if type_level == "breaking":
                old_type = describe_type_descriptor(old_f.get("type", {}))
                new_type = describe_type_descriptor(new_f.get("type", {}))
                add("breaking", f"field type changed incompatibly: {context} field_id={fid} {old_type} -> {new_type}")
            elif type_level == "additive":
                old_type = describe_type_descriptor(old_f.get("type", {}))
                new_type = describe_type_descriptor(new_f.get("type", {}))
                add("additive", f"field type widened: {context} field_id={fid} {old_type} -> {new_type}")

            old_card = old_f.get("cardinality", {})
            new_card = new_f.get("cardinality", {})
            old_min = old_card.get("min", 0)
            new_min = new_card.get("min", 0)
            old_max = old_card.get("max", 1)
            new_max = new_card.get("max", 1)

            if new_min > old_min:
                add("breaking", f"cardinality tightened: {context} field_id={fid} min {old_min} -> {new_min}")
            elif new_min < old_min:
                add("additive", f"cardinality loosened: {context} field_id={fid} min {old_min} -> {new_min}")

            if (old_max == 1 and new_max != 1) or (old_max != 1 and new_max == 1):
                add("breaking", f"wire shape changed scalar/list: {context} field_id={fid}")
            elif isinstance(old_max, int) and isinstance(new_max, int):
                if new_max < old_max:
                    add("breaking", f"cardinality tightened: {context} field_id={fid} max {old_max} -> {new_max}")
                elif new_max > old_max:
                    add("additive", f"cardinality loosened: {context} field_id={fid} max {old_max} -> {new_max}")

    old_objects = {o["id"]: o for o in old_ir.get("objects", [])}
    new_objects = {o["id"]: o for o in new_ir.get("objects", [])}
    old_types = {t["id"]: t for t in old_ir.get("types", [])}
    new_types = {t["id"]: t for t in new_ir.get("types", [])}

    for tid in sorted(set(old_types) - set(new_types)):
        add("breaking", f"type removed: {tid}")
    for tid in sorted(set(new_types) - set(old_types)):
        add("additive", f"type added: {tid}")
    for tid in sorted(set(old_types) & set(new_types)):
        old_t = old_types[tid]
        new_t = new_types[tid]
        old_base = old_t.get("base")
        new_base = new_t.get("base")
        base_level = classify_type_change(
            {"kind": "base", "name": old_base},
            {"kind": "base", "name": new_base},
        )
        if base_level == "breaking":
            add("breaking", f"type base changed incompatibly: type={tid} {old_base} -> {new_base}")
        elif base_level == "additive":
            add("additive", f"type base widened: type={tid} {old_base} -> {new_base}")
        if old_t.get("constraints", {}) != new_t.get("constraints", {}):
            add("breaking", f"type constraints changed: type={tid}")

    for oid in sorted(set(old_objects) - set(new_objects)):
        add("breaking", f"object removed: {oid}")
    for oid in sorted(set(new_objects) - set(old_objects)):
        add("additive", f"object added: {oid}")

    for oid in sorted(set(old_objects) & set(new_objects)):
        old_obj = old_objects[oid]
        new_obj = new_objects[oid]
        compare_field_collections(f"object={oid}", old_obj.get("fields", []), new_obj.get("fields", []))

        old_states = {s["id"]: s for s in old_obj.get("states", [])}
        new_states = {s["id"]: s for s in new_obj.get("states", [])}
        for sid in sorted(set(old_states) - set(new_states)):
            add("breaking", f"state removed: object={oid} state_id={sid}")
        for sid in sorted(set(new_states) - set(old_states)):
            add("additive", f"state added: object={oid} state_id={sid}")

        old_trans = {t["id"]: t for t in old_obj.get("transitions", [])}
        new_trans = {t["id"]: t for t in new_obj.get("transitions", [])}
        for tid in sorted(set(old_trans) - set(new_trans)):
            add("breaking", f"transition removed: object={oid} transition_id={tid}")
        for tid in sorted(set(new_trans) - set(old_trans)):
            add("additive", f"transition added: object={oid} transition_id={tid}")

    def compare_named_list(kind: str, old_list: List[Dict[str, Any]], new_list: List[Dict[str, Any]]) -> None:
        def comparable_payload(item: Dict[str, Any]) -> Dict[str, Any]:
            if kind == "action":
                keep = ("id", "name", "kind", "input_shape_id", "output_shape_id")
                return {k: item.get(k) for k in keep}
            if kind == "event":
                keep = ("id", "name", "kind", "object_id", "action_id", "from_state_id", "to_state_id")
                return {k: item.get(k) for k in keep}
            if kind == "trigger":
                keep = ("id", "name", "event_id", "action_id")
                return {k: item.get(k) for k in keep}
            return dict(item)

        old_map = {i["id"]: i for i in old_list}
        new_map = {i["id"]: i for i in new_list}
        for xid in sorted(set(old_map) - set(new_map)):
            add("breaking", f"{kind} removed: {xid}")
        for xid in sorted(set(new_map) - set(old_map)):
            add("additive", f"{kind} added: {xid}")
        for xid in sorted(set(old_map) & set(new_map)):
            if comparable_payload(old_map[xid]) != comparable_payload(new_map[xid]):
                add("breaking", f"{kind} changed: {xid}")

    def compare_action_shape_list(kind: str, old_list: List[Dict[str, Any]], new_list: List[Dict[str, Any]]) -> None:
        old_map = {i["id"]: i for i in old_list}
        new_map = {i["id"]: i for i in new_list}
        for xid in sorted(set(old_map) - set(new_map)):
            add("breaking", f"{kind} removed: {xid}")
        for xid in sorted(set(new_map) - set(old_map)):
            add("additive", f"{kind} added: {xid}")
        for xid in sorted(set(old_map) & set(new_map)):
            compare_field_collections(f"{kind}={xid}", old_map[xid].get("fields", []), new_map[xid].get("fields", []))

    compare_action_shape_list("struct", old_ir.get("structs", []), new_ir.get("structs", []))
    compare_action_shape_list("action_input", old_ir.get("action_inputs", []), new_ir.get("action_inputs", []))
    compare_action_shape_list("action_output", old_ir.get("action_outputs", []), new_ir.get("action_outputs", []))
    compare_named_list("action", old_ir.get("actions", []), new_ir.get("actions", []))
    compare_named_list("event", old_ir.get("events", []), new_ir.get("events", []))
    compare_named_list("trigger", old_ir.get("triggers", []), new_ir.get("triggers", []))

    old_query_contracts = query_contract_map(old_ir)
    new_query_contracts = query_contract_map(new_ir)
    for oid in sorted(set(old_query_contracts) - set(new_query_contracts)):
        add("breaking", f"query contract removed: object={oid}")
    for oid in sorted(set(new_query_contracts) - set(old_query_contracts)):
        add("additive", f"query contract added: object={oid}")
    for oid in sorted(set(old_query_contracts) & set(new_query_contracts)):
        old_c = old_query_contracts[oid]
        new_c = new_query_contracts[oid]
        old_paths = old_c.get("paths", {})
        new_paths = new_c.get("paths", {})
        for path_key in sorted(set(old_paths) | set(new_paths)):
            old_path = old_paths.get(path_key)
            new_path = new_paths.get(path_key)
            if old_path == new_path:
                continue
            if old_path and new_path:
                add("breaking", f"query path changed: object={oid} {path_key} {old_path} -> {new_path}")
            elif old_path and not new_path:
                add("breaking", f"query path removed: object={oid} {path_key} {old_path}")
            elif new_path and not old_path:
                add("additive", f"query path added: object={oid} {path_key} {new_path}")

        old_filters = {f["field_id"]: f for f in old_c.get("filters", []) if f.get("field_id")}
        new_filters = {f["field_id"]: f for f in new_c.get("filters", []) if f.get("field_id")}
        for fid in sorted(set(old_filters) - set(new_filters)):
            add("breaking", f"query filter removed: object={oid} field_id={fid}")
        for fid in sorted(set(new_filters) - set(old_filters)):
            add("additive", f"query filter added: object={oid} field_id={fid}")
        for fid in sorted(set(old_filters) & set(new_filters)):
            old_ops = set(old_filters[fid].get("operators", []))
            new_ops = set(new_filters[fid].get("operators", []))
            for op in sorted(old_ops - new_ops):
                add("breaking", f"query operator removed: object={oid} field_id={fid} op={op}")
            for op in sorted(new_ops - old_ops):
                add("additive", f"query operator added: object={oid} field_id={fid} op={op}")

    if any(level == "breaking" for level, _ in findings):
        level = "breaking"
    elif any(level == "additive" for level, _ in findings):
        level = "additive"
    else:
        level = "non_functional"

    messages = [msg for _, msg in findings]
    return level, messages


def declared_bump(old_ver: str, new_ver: str) -> str:
    old = parse_semver(old_ver)
    new = parse_semver(new_ver)
    if new[0] > old[0]:
        return "major"
    if new[0] == old[0] and new[1] > old[1]:
        return "minor"
    return "patch"
