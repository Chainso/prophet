from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


_STD_TYPE_REF_BY_BASE: Dict[str, str] = {
    "string": "std:String",
    "int": "std:Int",
    "long": "std:Long",
    "short": "std:Short",
    "byte": "std:Byte",
    "double": "std:Double",
    "float": "std:Float",
    "decimal": "std:Decimal",
    "boolean": "std:Boolean",
    "datetime": "std:DateTime",
    "date": "std:Date",
    "duration": "std:Duration",
}


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


def _sanitize_identifier(raw: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_]", "_", str(raw))
    if not normalized:
        digest = hashlib.sha256(str(raw).encode("utf-8")).hexdigest()[:8]
        normalized = f"n_{digest}"
    if normalized[0].isdigit():
        normalized = f"n_{normalized}"
    return normalized


def _sanitize_prefix_name(raw: str) -> str:
    candidate = _sanitize_identifier(raw).lower()
    if candidate and candidate[0].isdigit():
        candidate = f"p_{candidate}"
    return candidate or "local_ontology"


def _local_namespace_fragment(value: str) -> str:
    fragment = snake_case(value).strip("_")
    if not fragment:
        fragment = "ontology"
    return fragment


def _turtle_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _turtle_literal(value: str) -> str:
    return f"\"{_turtle_escape(value)}\""


def _turtle_typed_literal(value: Any, datatype_qname: str) -> str:
    return f"\"{_turtle_escape(str(value))}\"^^{datatype_qname}"


def _decode_dsl_escaped(value: Any) -> str:
    raw = str(value)
    try:
        return str(json.loads(f"\"{raw}\""))
    except json.JSONDecodeError:
        return raw


def _parse_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _shacl_constraint_property_node(constraints: Dict[str, Any]) -> str:
    nodes: List[Tuple[str, str]] = [("sh:path", "sh:value")]

    pattern = constraints.get("pattern")
    if pattern is not None:
        nodes.append(("sh:pattern", _turtle_literal(_decode_dsl_escaped(pattern))))

    min_length = constraints.get("min_length")
    if min_length is None:
        min_length = constraints.get("minLength")
    parsed_min_length = _parse_int(min_length)
    if parsed_min_length is not None:
        nodes.append(("sh:minLength", str(parsed_min_length)))

    max_length = constraints.get("max_length")
    if max_length is None:
        max_length = constraints.get("maxLength")
    parsed_max_length = _parse_int(max_length)
    if parsed_max_length is not None:
        nodes.append(("sh:maxLength", str(parsed_max_length)))

    min_inclusive = constraints.get("min")
    parsed_min = _parse_int(min_inclusive)
    if parsed_min is not None:
        nodes.append(("sh:minInclusive", str(parsed_min)))

    max_inclusive = constraints.get("max")
    parsed_max = _parse_int(max_inclusive)
    if parsed_max is not None:
        nodes.append(("sh:maxInclusive", str(parsed_max)))

    if len(nodes) == 1:
        summary = ", ".join(f"{key}={value}" for key, value in sorted(constraints.items()))
        nodes.append(("sh:message", _turtle_literal(f"Unmapped constraints: {summary}")))

    parts = [f"{predicate} {obj}" for predicate, obj in nodes]
    return "[ " + " ; ".join(parts) + " ]"


def _emit_resource(lines: List[str], subject: str, rdf_type: str, statements: List[Tuple[str, str]]) -> None:
    if not statements:
        lines.append(f"{subject} a {rdf_type} .")
        lines.append("")
        return
    lines.append(f"{subject} a {rdf_type} ;")
    for idx, (predicate, obj) in enumerate(statements):
        suffix = " ." if idx == len(statements) - 1 else " ;"
        lines.append(f"  {predicate} {obj}{suffix}")
    lines.append("")


def _append_name_description(statements: List[Tuple[str, str]], item: Dict[str, Any]) -> None:
    name = str(item.get("name", "")).strip()
    if name:
        statements.append(("prophet:name", _turtle_literal(name)))
    description = str(item.get("description", "")).strip()
    if description:
        statements.append(("prophet:description", _turtle_literal(description)))
    documentation = str(item.get("documentation", "")).strip()
    if documentation:
        statements.append(("prophet:documentation", _turtle_literal(documentation)))


@dataclass
class TurtleRenderContext:
    ontology_subject: str
    local_prefix: str
    list_type_nodes: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)
    object_reference_nodes: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)
    constraint_nodes: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)

    def local_resource(self, raw: str) -> str:
        return f"{self.local_prefix}:{_sanitize_identifier(raw)}"

    def base_type_ref(self, base_name: str) -> str:
        return _STD_TYPE_REF_BY_BASE.get(str(base_name), "std:String")

    def type_ref_for_descriptor(self, type_desc: Dict[str, Any], seed: str) -> str:
        kind = str(type_desc.get("kind", ""))
        if kind == "base":
            return self.base_type_ref(str(type_desc.get("name", "")))
        if kind == "custom":
            return self.local_resource(str(type_desc.get("target_type_id", "")))
        if kind == "object_ref":
            target_object_id = str(type_desc.get("target_object_id", ""))
            ref_subject = self.local_resource(f"{seed}_object_ref")
            if ref_subject not in self.object_reference_nodes:
                ref_name = pascal_case(seed) or "ObjectRef"
                self.object_reference_nodes[ref_subject] = [
                    ("prophet:name", _turtle_literal(ref_name)),
                    ("prophet:referencesObjectModel", self.local_resource(target_object_id)),
                    ("prophet:inLocalOntology", self.ontology_subject),
                ]
            return ref_subject
        if kind == "struct":
            return self.local_resource(str(type_desc.get("target_struct_id", "")))
        if kind == "list":
            list_subject = self.local_resource(f"{seed}_list_type")
            if list_subject not in self.list_type_nodes:
                item_ref = self.type_ref_for_descriptor(type_desc.get("element", {}), f"{seed}_item")
                self.list_type_nodes[list_subject] = [
                    ("prophet:name", _turtle_literal(f"{pascal_case(seed)}List")),
                    ("prophet:itemType", item_ref),
                    ("prophet:inLocalOntology", self.ontology_subject),
                ]
            return list_subject
        return "std:String"

    def property_block(self, field: Dict[str, Any]) -> Tuple[str, List[Tuple[str, str]]]:
        field_id = str(field.get("id", "field"))
        field_name = str(field.get("name", field_id))
        field_subject = self.local_resource(field_id)
        min_cardinality = int(field.get("cardinality", {}).get("min", 0))
        max_cardinality = field.get("cardinality", {}).get("max", 1)
        statements: List[Tuple[str, str]] = [
            ("prophet:name", _turtle_literal(field_name)),
            ("prophet:fieldKey", _turtle_literal(field_name)),
            ("prophet:minCardinality", str(min_cardinality)),
            ("prophet:valueType", self.type_ref_for_descriptor(field.get("type", {}), field_id)),
            ("prophet:inLocalOntology", self.ontology_subject),
        ]
        if isinstance(max_cardinality, int):
            statements.insert(3, ("prophet:maxCardinality", str(max_cardinality)))
        description = str(field.get("description", "")).strip()
        if description:
            statements.insert(1, ("prophet:description", _turtle_literal(description)))
        return field_subject, statements


def _sorted_items(ir: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
    return sorted(ir.get(key, []), key=lambda item: str(item.get("id", "")))


def render_turtle(ir: Dict[str, Any]) -> str:
    ontology = ir.get("ontology", {}) if isinstance(ir.get("ontology"), dict) else {}
    ontology_name = str(ontology.get("name", "Ontology")).strip() or "Ontology"
    ontology_id = str(ontology.get("id", "")) or f"ontology_{snake_case(ontology_name)}"
    ontology_prefix_seed = _local_namespace_fragment(ontology_name or ontology_id)
    local_prefix = _sanitize_prefix_name(ontology_prefix_seed)
    if local_prefix in {"prophet", "std", "sh", "xsd", "owl", "rdf", "rdfs"}:
        local_prefix = f"{local_prefix}_local"
    local_namespace = f"http://prophet.platform/local/{ontology_prefix_seed}#"
    ontology_subject = f"{local_prefix}:{_sanitize_identifier(ontology_id)}"
    context = TurtleRenderContext(ontology_subject=ontology_subject, local_prefix=local_prefix)

    types = _sorted_items(ir, "types")
    objects = _sorted_items(ir, "objects")
    structs = _sorted_items(ir, "structs")
    action_inputs = _sorted_items(ir, "action_inputs")
    actions = _sorted_items(ir, "actions")
    events = _sorted_items(ir, "events")
    triggers = _sorted_items(ir, "triggers")
    transition_event_fields_by_transition_id: Dict[str, List[Dict[str, Any]]] = {}
    for event in events:
        if str(event.get("kind", "")) != "transition":
            continue
        transition_id = str(event.get("transition_id", "")).strip()
        if transition_id:
            transition_event_fields_by_transition_id[transition_id] = sorted(
                [field for field in event.get("fields", []) if isinstance(field, dict)],
                key=lambda item: str(item.get("id", "")),
            )

    lines: List[str] = [
        "# Code generated by prophet-cli. DO NOT EDIT.",
        "# Source: canonical IR projection in Prophet Turtle format",
        "",
        "@prefix prophet: <http://prophet.platform/ontology#> .",
        "@prefix std:     <http://prophet.platform/standard-types#> .",
        f"@prefix {local_prefix}: <{local_namespace}> .",
        "@prefix sh:      <http://www.w3.org/ns/shacl#> .",
        "@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .",
        "",
        "# ============================================================",
        "# Local Ontology",
        "# ============================================================",
        "",
    ]

    ontology_statements: List[Tuple[str, str]] = [
        ("prophet:name", _turtle_literal(ontology_name)),
    ]
    ontology_description = str(ontology.get("description", "")).strip()
    if ontology_description:
        ontology_statements.append(("prophet:description", _turtle_literal(ontology_description)))
    ontology_documentation = str(ontology.get("documentation", "")).strip()
    if ontology_documentation:
        ontology_statements.append(("prophet:documentation", _turtle_literal(ontology_documentation)))
    _emit_resource(lines, ontology_subject, "prophet:LocalOntology", ontology_statements)

    if types:
        lines.extend(
            [
                "# ============================================================",
                "# Custom Types",
                "# ============================================================",
                "",
            ]
        )
    for item in types:
        type_id = str(item.get("id", ""))
        subject = context.local_resource(type_id)
        statements: List[Tuple[str, str]] = []
        _append_name_description(statements, item)
        statements.append(("prophet:derivedFrom", context.base_type_ref(str(item.get("base", "")))))
        constraints = item.get("constraints", {})
        if isinstance(constraints, dict) and constraints:
            constraint_subject = context.local_resource(f"{type_id}_constraint")
            context.constraint_nodes[constraint_subject] = [
                ("sh:property", _shacl_constraint_property_node(constraints))
            ]
            statements.append(("prophet:hasConstraint", constraint_subject))
        statements.append(("prophet:inLocalOntology", ontology_subject))
        _emit_resource(lines, subject, "prophet:CustomType", statements)

    if context.constraint_nodes:
        lines.extend(
            [
                "# ============================================================",
                "# Constraint Shapes",
                "# ============================================================",
                "",
            ]
        )
    for subject in sorted(context.constraint_nodes.keys()):
        _emit_resource(lines, subject, "sh:NodeShape", context.constraint_nodes[subject])

    if structs:
        lines.extend(
            [
                "# ============================================================",
                "# Struct Types",
                "# ============================================================",
                "",
            ]
        )
    for struct in structs:
        struct_subject = context.local_resource(str(struct.get("id", "")))
        fields = sorted(struct.get("fields", []), key=lambda item: str(item.get("id", "")))
        field_defs = [context.property_block(field) for field in fields]
        statements: List[Tuple[str, str]] = []
        _append_name_description(statements, struct)
        statements.append(("prophet:inLocalOntology", ontology_subject))
        for field_subject, _ in field_defs:
            statements.append(("prophet:hasProperty", field_subject))
        _emit_resource(lines, struct_subject, "prophet:StructType", statements)
        for field_subject, field_statements in field_defs:
            _emit_resource(lines, field_subject, "prophet:PropertyDefinition", field_statements)

    if objects:
        lines.extend(
            [
                "# ============================================================",
                "# Object Models",
                "# ============================================================",
                "",
            ]
        )
    transition_subjects_by_id: Dict[str, str] = {}
    for obj in objects:
        obj_subject = context.local_resource(str(obj.get("id", "")))
        fields = sorted(obj.get("fields", []), key=lambda item: str(item.get("id", "")))
        field_defs = [context.property_block(field) for field in fields]
        state_defs = sorted(obj.get("states", []), key=lambda item: str(item.get("id", "")))
        transition_defs = sorted(obj.get("transitions", []), key=lambda item: str(item.get("id", "")))

        primary_ids = obj.get("keys", {}).get("primary", {}).get("field_ids", [])
        display_ids = obj.get("keys", {}).get("display", {}).get("field_ids", [])
        primary_ids = [str(field_id) for field_id in primary_ids] if isinstance(primary_ids, list) else []
        display_ids = [str(field_id) for field_id in display_ids] if isinstance(display_ids, list) else []
        if not primary_ids and field_defs:
            primary_ids = [str(fields[0].get("id", ""))]
        if not display_ids:
            display_ids = list(primary_ids)
        if not display_ids and field_defs:
            display_ids = [str(fields[0].get("id", ""))]

        primary_subject = context.local_resource(f"{obj.get('id', '')}_primary_key")
        display_subject = context.local_resource(f"{obj.get('id', '')}_display_key")

        statements: List[Tuple[str, str]] = []
        _append_name_description(statements, obj)
        statements.append(("prophet:inLocalOntology", ontology_subject))
        for field_subject, _ in field_defs:
            statements.append(("prophet:hasProperty", field_subject))
        for state in state_defs:
            statements.append(("prophet:hasPossibleState", context.local_resource(str(state.get("id", "")))))
        initial_state_ids = [str(state.get("id", "")) for state in state_defs if bool(state.get("initial"))]
        if initial_state_ids:
            statements.append(("prophet:initialState", context.local_resource(initial_state_ids[0])))
        if primary_ids:
            statements.append(("prophet:hasPrimaryKey", primary_subject))
        if display_ids:
            statements.append(("prophet:hasDisplayKey", display_subject))
        _emit_resource(lines, obj_subject, "prophet:ObjectModel", statements)

        for field_subject, field_statements in field_defs:
            _emit_resource(lines, field_subject, "prophet:PropertyDefinition", field_statements)

        if primary_ids:
            key_statements: List[Tuple[str, str]] = [
                ("prophet:name", _turtle_literal(f"{obj.get('name', 'Object')} Primary Key")),
                ("prophet:inLocalOntology", ontology_subject),
            ]
            for idx, _ in enumerate(primary_ids):
                part_subject = context.local_resource(f"{obj.get('id', '')}_primary_part_{idx}")
                key_statements.append(("prophet:hasKeyPart", part_subject))
            _emit_resource(lines, primary_subject, "prophet:KeyDefinition", key_statements)
            for idx, field_id in enumerate(primary_ids):
                part_subject = context.local_resource(f"{obj.get('id', '')}_primary_part_{idx}")
                part_statements = [
                    ("prophet:name", _turtle_literal(f"PK part {idx}")),
                    ("prophet:partIndex", _turtle_typed_literal(idx, "xsd:nonNegativeInteger")),
                    ("prophet:partProperty", context.local_resource(field_id)),
                    ("prophet:inLocalOntology", ontology_subject),
                ]
                _emit_resource(lines, part_subject, "prophet:KeyPart", part_statements)

        if display_ids:
            key_statements = [
                ("prophet:name", _turtle_literal(f"{obj.get('name', 'Object')} Display Key")),
                ("prophet:inLocalOntology", ontology_subject),
            ]
            for idx, _ in enumerate(display_ids):
                part_subject = context.local_resource(f"{obj.get('id', '')}_display_part_{idx}")
                key_statements.append(("prophet:hasKeyPart", part_subject))
            _emit_resource(lines, display_subject, "prophet:KeyDefinition", key_statements)
            for idx, field_id in enumerate(display_ids):
                part_subject = context.local_resource(f"{obj.get('id', '')}_display_part_{idx}")
                part_statements = [
                    ("prophet:name", _turtle_literal(f"DK part {idx}")),
                    ("prophet:partIndex", _turtle_typed_literal(idx, "xsd:nonNegativeInteger")),
                    ("prophet:partProperty", context.local_resource(field_id)),
                    ("prophet:inLocalOntology", ontology_subject),
                ]
                _emit_resource(lines, part_subject, "prophet:KeyPart", part_statements)

        for state in state_defs:
            state_subject = context.local_resource(str(state.get("id", "")))
            state_statements: List[Tuple[str, str]] = []
            _append_name_description(state_statements, state)
            state_statements.append(("prophet:stateOf", obj_subject))
            state_statements.append(("prophet:inLocalOntology", ontology_subject))
            _emit_resource(lines, state_subject, "prophet:State", state_statements)

        for transition in transition_defs:
            transition_id = str(transition.get("id", ""))
            transition_subject = context.local_resource(transition_id)
            transition_subjects_by_id[transition_id] = transition_subject
            transition_fields = transition_event_fields_by_transition_id.get(transition_id, [])
            transition_field_defs = [context.property_block(field) for field in transition_fields]
            transition_statements: List[Tuple[str, str]] = []
            _append_name_description(transition_statements, transition)
            transition_statements.append(("prophet:transitionOf", obj_subject))
            transition_statements.append(("prophet:fromState", context.local_resource(str(transition.get("from_state_id", "")))))
            transition_statements.append(("prophet:toState", context.local_resource(str(transition.get("to_state_id", "")))))
            for field_subject, _ in transition_field_defs:
                transition_statements.append(("prophet:hasProperty", field_subject))
            transition_statements.append(("prophet:inLocalOntology", ontology_subject))
            _emit_resource(lines, transition_subject, "prophet:Transition", transition_statements)
            for field_subject, field_statements in transition_field_defs:
                _emit_resource(lines, field_subject, "prophet:PropertyDefinition", field_statements)

    if action_inputs:
        lines.extend(
            [
                "# ============================================================",
                "# Action Inputs",
                "# ============================================================",
                "",
            ]
        )
    for shape in action_inputs:
        shape_subject = context.local_resource(str(shape.get("id", "")))
        fields = sorted(shape.get("fields", []), key=lambda item: str(item.get("id", "")))
        field_defs = [context.property_block(field) for field in fields]
        statements: List[Tuple[str, str]] = []
        _append_name_description(statements, shape)
        statements.append(("prophet:inLocalOntology", ontology_subject))
        for field_subject, _ in field_defs:
            statements.append(("prophet:hasProperty", field_subject))
        _emit_resource(lines, shape_subject, "prophet:ActionInput", statements)
        for field_subject, field_statements in field_defs:
            _emit_resource(lines, field_subject, "prophet:PropertyDefinition", field_statements)

    if actions:
        lines.extend(
            [
                "# ============================================================",
                "# Actions",
                "# ============================================================",
                "",
            ]
        )
    for action in actions:
        action_subject = context.local_resource(str(action.get("id", "")))
        statements: List[Tuple[str, str]] = []
        _append_name_description(statements, action)
        action_kind = str(action.get("kind", "")).strip()
        statements.extend(
            [
                ("prophet:acceptsInput", context.local_resource(str(action.get("input_shape_id", "")))),
                ("prophet:producesEvent", context.local_resource(str(action.get("output_event_id", "")))),
                ("prophet:inLocalOntology", ontology_subject),
            ]
        )
        action_rdf_type = "prophet:Workflow" if action_kind == "workflow" else "prophet:Process"
        _emit_resource(lines, action_subject, action_rdf_type, statements)

    signal_events = [event for event in events if str(event.get("kind", "")) == "signal"]
    signal_subjects_by_event_id: Dict[str, str] = {}
    if signal_events:
        lines.extend(
            [
                "# ============================================================",
                "# Signals",
                "# ============================================================",
                "",
            ]
        )
    for event in signal_events:
        event_id = str(event.get("id", ""))
        event_subject = context.local_resource(event_id)
        signal_subjects_by_event_id[event_id] = event_subject
        fields = sorted(event.get("fields", []), key=lambda item: str(item.get("id", "")))
        field_defs = [context.property_block(field) for field in fields]
        statements: List[Tuple[str, str]] = []
        _append_name_description(statements, event)
        for field_subject, _ in field_defs:
            statements.append(("prophet:hasProperty", field_subject))
        statements.append(("prophet:inLocalOntology", ontology_subject))

        _emit_resource(lines, event_subject, "prophet:Signal", statements)
        for field_subject, field_statements in field_defs:
            _emit_resource(lines, field_subject, "prophet:PropertyDefinition", field_statements)

    event_subject_by_id: Dict[str, str] = {}
    for event in events:
        event_id = str(event.get("id", ""))
        event_kind = str(event.get("kind", ""))
        if event_kind == "signal":
            event_subject_by_id[event_id] = signal_subjects_by_event_id.get(event_id, context.local_resource(event_id))
            continue
        if event_kind == "transition":
            transition_id = str(event.get("transition_id", "")).strip() or event_id
            event_subject_by_id[event_id] = transition_subjects_by_id.get(transition_id, context.local_resource(transition_id))
            continue
        event_subject_by_id[event_id] = context.local_resource(event_id)

    if triggers:
        lines.extend(
            [
                "# ============================================================",
                "# Triggers",
                "# ============================================================",
                "",
            ]
        )
    for trigger in triggers:
        trigger_subject = context.local_resource(str(trigger.get("id", "")))
        trigger_event_id = str(trigger.get("event_id", ""))
        event_subject = event_subject_by_id.get(trigger_event_id, context.local_resource(trigger_event_id))
        statements: List[Tuple[str, str]] = []
        _append_name_description(statements, trigger)
        statements.extend(
            [
                ("prophet:listensTo", event_subject),
                ("prophet:invokes", context.local_resource(str(trigger.get("action_id", "")))),
                ("prophet:inLocalOntology", ontology_subject),
            ]
        )
        _emit_resource(lines, trigger_subject, "prophet:EventTrigger", statements)

    if context.object_reference_nodes:
        lines.extend(
            [
                "# ============================================================",
                "# Object Reference Types",
                "# ============================================================",
                "",
            ]
        )
    for subject in sorted(context.object_reference_nodes.keys()):
        _emit_resource(lines, subject, "prophet:ObjectReference", context.object_reference_nodes[subject])

    if context.list_type_nodes:
        lines.extend(
            [
                "# ============================================================",
                "# Derived List Types",
                "# ============================================================",
                "",
            ]
        )
    for subject in sorted(context.list_type_nodes.keys()):
        _emit_resource(lines, subject, "prophet:ListType", context.list_type_nodes[subject])

    return "\n".join(lines).rstrip() + "\n"
