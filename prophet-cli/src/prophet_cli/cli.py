#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from prophet_cli.core.errors import ProphetError
from prophet_cli.core.config import cfg_get as _core_cfg_get
from prophet_cli.core.config import load_config as _core_load_config
from prophet_cli.core.ir import build_ir as _core_build_ir
from prophet_cli.core.ir_reader import IRReader
from prophet_cli.core.parser import parse_ontology as _core_parse_ontology
from prophet_cli.core.parser import resolve_type_descriptor as _core_resolve_type_descriptor
from prophet_cli.core.parser import unwrap_list_type_once as _core_unwrap_list_type_once
from prophet_cli.core.compatibility import bump_rank as _core_bump_rank
from prophet_cli.core.compatibility import classify_type_change as _core_classify_type_change
from prophet_cli.core.compatibility import compare_irs as _core_compare_irs
from prophet_cli.core.compatibility import declared_bump as _core_declared_bump
from prophet_cli.core.compatibility import describe_type_descriptor as _core_describe_type_descriptor
from prophet_cli.core.compatibility import parse_semver as _core_parse_semver
from prophet_cli.core.compatibility import required_level_to_bump as _core_required_level_to_bump
from prophet_cli.core.validation import validate_ontology as _core_validate_ontology
from prophet_cli.core.validation import validate_type_expr as _core_validate_type_expr
from prophet_cli.codegen.stacks import resolve_stack_spec
from prophet_cli.codegen.stacks import supported_stack_table
from prophet_cli.codegen.contracts import GenerationContext
from prophet_cli.codegen.pipeline import run_generation_pipeline
from prophet_cli.codegen.artifacts import managed_existing_files as _managed_existing_files
from prophet_cli.codegen.artifacts import remove_stale_outputs as _remove_stale_outputs
from prophet_cli.codegen.artifacts import write_outputs as _write_outputs
from prophet_cli.targets.java_spring_jpa import JavaSpringJpaDeps
from prophet_cli.targets.java_spring_jpa import generate_outputs as generate_java_spring_jpa_outputs


TOOLCHAIN_VERSION = "0.3.0"
IR_VERSION = "0.1"
COMPATIBILITY_POLICY_DOC = "docs/prophet-compatibility-policy-v0.2.md"

BASE_TYPES = {
    "string",
    "int",
    "long",
    "short",
    "byte",
    "double",
    "float",
    "decimal",
    "boolean",
    "datetime",
    "date",
    "duration",
}


@dataclass
class TypeDef:
    name: str
    id: str
    base: str
    constraints: Dict[str, str]
    line: int


@dataclass
class FieldDef:
    name: str
    id: str
    type_raw: str
    required: bool
    key: Optional[str]
    line: int


@dataclass
class StateDef:
    name: str
    id: str
    initial: bool
    line: int


@dataclass
class TransitionDef:
    name: str
    id: str
    from_state: str
    to_state: str
    line: int


@dataclass
class ObjectDef:
    name: str
    id: str
    fields: List[FieldDef]
    states: List[StateDef]
    transitions: List[TransitionDef]
    line: int


@dataclass
class StructDef:
    name: str
    id: str
    fields: List[FieldDef]
    line: int


@dataclass
class ActionDef:
    name: str
    id: str
    kind: str
    input_shape: str
    output_shape: str
    line: int


@dataclass
class ActionShapeDef:
    name: str
    id: str
    fields: List[FieldDef]
    line: int


@dataclass
class EventDef:
    name: str
    id: str
    kind: str
    action: Optional[str]
    object_name: str
    from_state: Optional[str]
    to_state: Optional[str]
    line: int


@dataclass
class TriggerDef:
    name: str
    id: str
    event_name: str
    action_name: str
    line: int


@dataclass
class Ontology:
    name: str
    id: str
    version: str
    types: List[TypeDef] = field(default_factory=list)
    objects: List[ObjectDef] = field(default_factory=list)
    structs: List[StructDef] = field(default_factory=list)
    action_inputs: List[ActionShapeDef] = field(default_factory=list)
    action_outputs: List[ActionShapeDef] = field(default_factory=list)
    actions: List[ActionDef] = field(default_factory=list)
    events: List[EventDef] = field(default_factory=list)
    triggers: List[TriggerDef] = field(default_factory=list)


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


load_config = _core_load_config
cfg_get = _core_cfg_get


class Parser:
    def __init__(self, text: str):
        self.lines: List[Tuple[int, str]] = []
        for i, raw in enumerate(text.splitlines(), start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue
            self.lines.append((i, stripped))
        self.i = 0

    def eof(self) -> bool:
        return self.i >= len(self.lines)

    def peek(self) -> Tuple[int, str]:
        if self.eof():
            return (-1, "")
        return self.lines[self.i]

    def pop(self) -> Tuple[int, str]:
        if self.eof():
            raise ProphetError("Unexpected EOF")
        val = self.lines[self.i]
        self.i += 1
        return val

    def expect(self, pattern: str, err: str) -> re.Match[str]:
        ln, line = self.pop()
        m = re.match(pattern, line)
        if not m:
            raise ProphetError(f"{err} at line {ln}: {line}")
        return m


def parse_ontology(text: str) -> Ontology:
    p = Parser(text)
    start = p.expect(r"^ontology\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", "Expected ontology header")
    ont_name = start.group(1)

    ont_id: Optional[str] = None
    ont_version: Optional[str] = None
    types: List[TypeDef] = []
    objects: List[ObjectDef] = []
    structs: List[StructDef] = []
    action_inputs: List[ActionShapeDef] = []
    action_outputs: List[ActionShapeDef] = []
    actions: List[ActionDef] = []
    events: List[EventDef] = []
    triggers: List[TriggerDef] = []

    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break

        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            ont_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            continue

        if re.match(r"^version\s+\".*\"$", line):
            _, row = p.pop()
            ont_version = re.match(r'^version\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            continue

        m = re.match(r"^type\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            types.append(parse_type_block(p, m.group(1), ln))
            continue

        m = re.match(r"^object\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            objects.append(parse_object_block(p, m.group(1), ln))
            continue

        m = re.match(r"^struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            structs.append(parse_struct_block(p, m.group(1), ln))
            continue

        m = re.match(r"^actionInput\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            action_inputs.append(parse_action_shape_block(p, m.group(1), ln, "actionInput"))
            continue

        m = re.match(r"^action_input\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            action_inputs.append(parse_action_shape_block(p, m.group(1), ln, "action_input"))
            continue

        m = re.match(r"^actionOutput\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            action_outputs.append(parse_action_shape_block(p, m.group(1), ln, "actionOutput"))
            continue

        m = re.match(r"^action_output\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            action_outputs.append(parse_action_shape_block(p, m.group(1), ln, "action_output"))
            continue

        m = re.match(r"^action\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            actions.append(parse_action_block(p, m.group(1), ln))
            continue

        m = re.match(r"^event\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            events.append(parse_event_block(p, m.group(1), ln))
            continue

        m = re.match(r"^trigger\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            triggers.append(parse_trigger_block(p, m.group(1), ln))
            continue

        raise ProphetError(f"Unexpected line {ln}: {line}")

    if ont_id is None:
        raise ProphetError("Ontology missing id")
    if ont_version is None:
        raise ProphetError("Ontology missing version")

    return Ontology(
        name=ont_name,
        id=ont_id,
        version=ont_version,
        types=types,
        objects=objects,
        structs=structs,
        action_inputs=action_inputs,
        action_outputs=action_outputs,
        actions=actions,
        events=events,
        triggers=triggers,
    )


def parse_type_block(p: Parser, name: str, block_line: int) -> TypeDef:
    t_id: Optional[str] = None
    base: Optional[str] = None
    constraints: Dict[str, str] = {}
    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break

        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            t_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            continue

        m = re.match(r"^base\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            base = m.group(1)
            continue

        m = re.match(r'^constraint\s+([A-Za-z_][A-Za-z0-9_]*)\s+\"(.*)\"$', line)
        if m:
            p.pop()
            constraints[m.group(1)] = m.group(2)
            continue

        raise ProphetError(f"Unexpected type line {ln}: {line}")

    if t_id is None:
        raise ProphetError(f"Type {name} missing id (line {block_line})")
    if base is None:
        raise ProphetError(f"Type {name} missing base (line {block_line})")
    return TypeDef(name=name, id=t_id, base=base, constraints=constraints, line=block_line)


def parse_object_block(p: Parser, name: str, block_line: int) -> ObjectDef:
    o_id: Optional[str] = None
    fields: List[FieldDef] = []
    states: List[StateDef] = []
    transitions: List[TransitionDef] = []

    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break

        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            o_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            continue

        m = re.match(r"^field\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            fields.append(parse_field_block(p, m.group(1), ln))
            continue

        m = re.match(r"^state\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            states.append(parse_state_block(p, m.group(1), ln))
            continue

        m = re.match(r"^transition\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            transitions.append(parse_transition_block(p, m.group(1), ln))
            continue

        raise ProphetError(f"Unexpected object line {ln}: {line}")

    if o_id is None:
        raise ProphetError(f"Object {name} missing id (line {block_line})")
    return ObjectDef(name=name, id=o_id, fields=fields, states=states, transitions=transitions, line=block_line)


def parse_struct_block(p: Parser, name: str, block_line: int) -> StructDef:
    s_id: Optional[str] = None
    fields: List[FieldDef] = []

    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break

        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            s_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            continue

        m = re.match(r"^field\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            fields.append(parse_field_block(p, m.group(1), ln))
            continue

        raise ProphetError(f"Unexpected struct line {ln}: {line}")

    if s_id is None:
        raise ProphetError(f"Struct {name} missing id (line {block_line})")
    return StructDef(name=name, id=s_id, fields=fields, line=block_line)


def parse_field_block(p: Parser, name: str, block_line: int) -> FieldDef:
    f_id: Optional[str] = None
    type_raw: Optional[str] = None
    required: Optional[bool] = None
    key: Optional[str] = None

    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break

        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            f_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            continue

        m = re.match(r"^type\s+(.+)$", line)
        if m:
            p.pop()
            type_raw = m.group(1).strip()
            continue

        if line == "required":
            p.pop()
            required = True
            continue

        if line == "optional":
            p.pop()
            required = False
            continue

        m = re.match(r"^key\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            key = m.group(1)
            continue

        raise ProphetError(f"Unexpected field line {ln}: {line}")

    if f_id is None:
        raise ProphetError(f"Field {name} missing id (line {block_line})")
    if type_raw is None:
        raise ProphetError(f"Field {name} missing type (line {block_line})")
    if required is None:
        raise ProphetError(f"Field {name} missing required/optional (line {block_line})")

    return FieldDef(name=name, id=f_id, type_raw=type_raw, required=required, key=key, line=block_line)


def parse_state_block(p: Parser, name: str, block_line: int) -> StateDef:
    s_id: Optional[str] = None
    initial = False
    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break
        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            s_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            continue
        if line == "initial":
            p.pop()
            initial = True
            continue
        raise ProphetError(f"Unexpected state line {ln}: {line}")

    if s_id is None:
        raise ProphetError(f"State {name} missing id (line {block_line})")
    return StateDef(name=name, id=s_id, initial=initial, line=block_line)


def parse_transition_block(p: Parser, name: str, block_line: int) -> TransitionDef:
    t_id: Optional[str] = None
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break
        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            t_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            continue
        m = re.match(r"^from\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            from_state = m.group(1)
            continue
        m = re.match(r"^to\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            to_state = m.group(1)
            continue
        raise ProphetError(f"Unexpected transition line {ln}: {line}")

    if t_id is None or from_state is None or to_state is None:
        raise ProphetError(f"Transition {name} missing id/from/to (line {block_line})")
    return TransitionDef(name=name, id=t_id, from_state=from_state, to_state=to_state, line=block_line)


def parse_action_shape_block(p: Parser, name: str, block_line: int, block_kind: str) -> ActionShapeDef:
    shape_id: Optional[str] = None
    fields: List[FieldDef] = []
    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break
        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            shape_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            continue
        m = re.match(r"^field\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            fields.append(parse_field_block(p, m.group(1), ln))
            continue
        raise ProphetError(f"Unexpected {block_kind} line {ln}: {line}")

    if shape_id is None:
        raise ProphetError(f"{block_kind} {name} missing id (line {block_line})")
    return ActionShapeDef(name=name, id=shape_id, fields=fields, line=block_line)


def parse_action_block(p: Parser, name: str, block_line: int) -> ActionDef:
    a_id: Optional[str] = None
    kind: Optional[str] = None
    input_shape: Optional[str] = None
    output_shape: Optional[str] = None
    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break
        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            a_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            continue
        m = re.match(r"^kind\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            kind = m.group(1)
            continue
        m = re.match(r"^input\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            input_shape = m.group(1)
            continue
        m = re.match(r"^output\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            output_shape = m.group(1)
            continue
        raise ProphetError(f"Unexpected action line {ln}: {line}")

    if a_id is None or kind is None or input_shape is None or output_shape is None:
        raise ProphetError(f"Action {name} missing id/kind/input/output (line {block_line})")
    return ActionDef(name=name, id=a_id, kind=kind, input_shape=input_shape, output_shape=output_shape, line=block_line)


def parse_event_block(p: Parser, name: str, block_line: int) -> EventDef:
    e_id: Optional[str] = None
    kind: Optional[str] = None
    action: Optional[str] = None
    object_name: Optional[str] = None
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break
        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            e_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            continue
        m = re.match(r"^kind\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            kind = m.group(1)
            continue
        m = re.match(r"^action\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            action = m.group(1)
            continue
        m = re.match(r"^object\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            object_name = m.group(1)
            continue
        m = re.match(r"^from\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            from_state = m.group(1)
            continue
        m = re.match(r"^to\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            to_state = m.group(1)
            continue
        raise ProphetError(f"Unexpected event line {ln}: {line}")

    if e_id is None or kind is None or object_name is None:
        raise ProphetError(f"Event {name} missing id/kind/object (line {block_line})")
    return EventDef(
        name=name,
        id=e_id,
        kind=kind,
        action=action,
        object_name=object_name,
        from_state=from_state,
        to_state=to_state,
        line=block_line,
    )


def parse_trigger_block(p: Parser, name: str, block_line: int) -> TriggerDef:
    t_id: Optional[str] = None
    event_name: Optional[str] = None
    action_name: Optional[str] = None
    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break
        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            t_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            continue
        m = re.match(r"^when\s+event\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            event_name = m.group(1)
            continue
        m = re.match(r"^invoke\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            action_name = m.group(1)
            continue
        raise ProphetError(f"Unexpected trigger line {ln}: {line}")

    if t_id is None or event_name is None or action_name is None:
        raise ProphetError(f"Trigger {name} missing id/when/invoke (line {block_line})")
    return TriggerDef(name=name, id=t_id, event_name=event_name, action_name=action_name, line=block_line)


def unwrap_list_type_once(type_raw: str) -> Optional[str]:
    raw = type_raw.strip()
    if raw.endswith("[]"):
        inner = raw[:-2].strip()
        if not inner:
            raise ProphetError(f"invalid list type '{type_raw}'")
        return inner
    if raw.startswith("list(") and raw.endswith(")"):
        depth = 0
        for i, ch in enumerate(raw):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth < 0:
                    raise ProphetError(f"invalid type syntax '{type_raw}'")
                if depth == 0 and i != len(raw) - 1:
                    return None
        if depth != 0:
            raise ProphetError(f"invalid type syntax '{type_raw}'")
        inner = raw[5:-1].strip()
        if not inner:
            raise ProphetError(f"invalid list type '{type_raw}'")
        return inner
    return None


def resolve_type_descriptor(
    type_raw: str,
    type_name_to_id: Dict[str, str],
    object_name_to_id: Dict[str, str],
    struct_name_to_id: Dict[str, str],
) -> Dict[str, Any]:
    raw = type_raw.strip()
    if not raw:
        raise ProphetError("type must not be empty")

    list_inner = unwrap_list_type_once(raw)
    if list_inner is not None:
        return {
            "kind": "list",
            "element": resolve_type_descriptor(list_inner, type_name_to_id, object_name_to_id, struct_name_to_id),
        }

    ref_match = re.match(r"^ref\(([A-Za-z_][A-Za-z0-9_]*)\)$", raw)
    if ref_match:
        target_name = ref_match.group(1)
        if target_name not in object_name_to_id:
            raise ProphetError(f"references unknown object '{target_name}'")
        return {"kind": "object_ref", "target_object_id": object_name_to_id[target_name]}

    if raw in BASE_TYPES:
        return {"kind": "base", "name": raw}

    if raw in struct_name_to_id:
        return {"kind": "struct", "target_struct_id": struct_name_to_id[raw]}

    if raw in type_name_to_id:
        return {"kind": "custom", "target_type_id": type_name_to_id[raw]}

    raise ProphetError(f"uses unknown type '{raw}'")


def validate_type_expr(
    type_raw: str,
    type_names: Dict[str, TypeDef],
    object_names: Dict[str, ObjectDef],
    struct_names: Dict[str, StructDef],
) -> Optional[str]:
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
    event_names = {e.name: e for e in ont.events}

    for t in ont.types:
        if t.base not in BASE_TYPES:
            errors.append(f"line {t.line}: type {t.name} base '{t.base}' is not a supported base type")

    for o in ont.objects:
        primary_fields = [f for f in o.fields if f.key == "primary"]
        if len(primary_fields) != 1:
            errors.append(f"line {o.line}: object {o.name} must declare exactly one primary key field")

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

    for e in ont.events:
        if e.kind not in {"action_output", "signal", "transition"}:
            errors.append(f"line {e.line}: event {e.name} kind '{e.kind}' is invalid")
        if e.object_name not in object_names:
            errors.append(f"line {e.line}: event {e.name} object '{e.object_name}' not found")
            continue

        obj = object_names[e.object_name]
        state_names = {s.name for s in obj.states}

        if e.kind == "action_output":
            if not e.action:
                errors.append(f"line {e.line}: action_output event {e.name} must reference action")
            elif e.action not in action_names:
                errors.append(f"line {e.line}: event {e.name} references unknown action '{e.action}'")
        if e.kind == "transition":
            if not e.from_state or not e.to_state:
                errors.append(f"line {e.line}: transition event {e.name} must define from and to")
            else:
                if e.from_state not in state_names:
                    errors.append(f"line {e.line}: transition event {e.name} from state '{e.from_state}' missing on object {obj.name}")
                if e.to_state not in state_names:
                    errors.append(f"line {e.line}: transition event {e.name} to state '{e.to_state}' missing on object {obj.name}")

    for tr in ont.triggers:
        if tr.event_name not in event_names:
            errors.append(f"line {tr.line}: trigger {tr.name} references unknown event '{tr.event_name}'")
        if tr.action_name not in action_names:
            errors.append(f"line {tr.line}: trigger {tr.name} references unknown action '{tr.action_name}'")

    if strict_enums:
        for o in ont.objects:
            if len({s.name for s in o.states}) != len(o.states):
                errors.append(f"line {o.line}: object {o.name} has duplicate state names")

    return errors


# Canonical core delegation boundary (Milestone 2):
# keep CLI surface stable while routing parser/validation through dedicated core modules.
parse_ontology = _core_parse_ontology
unwrap_list_type_once = _core_unwrap_list_type_once
resolve_type_descriptor = _core_resolve_type_descriptor
validate_type_expr = _core_validate_type_expr
validate_ontology = _core_validate_ontology


def resolve_field_type(
    field: FieldDef,
    type_name_to_id: Dict[str, str],
    object_name_to_id: Dict[str, str],
    struct_name_to_id: Dict[str, str],
) -> Dict[str, Any]:
    return resolve_type_descriptor(field.type_raw, type_name_to_id, object_name_to_id, struct_name_to_id)


def build_ir(ont: Ontology, cfg: Dict[str, Any]) -> Dict[str, Any]:
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
        "ir_version": IR_VERSION,
        "toolchain_version": TOOLCHAIN_VERSION,
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
                "get_by_id": f"/{path_table}/{{id}}",
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
        old_map = {i["id"]: i for i in old_list}
        new_map = {i["id"]: i for i in new_list}
        for xid in sorted(set(old_map) - set(new_map)):
            add("breaking", f"{kind} removed: {xid}")
        for xid in sorted(set(new_map) - set(old_map)):
            add("additive", f"{kind} added: {xid}")
        for xid in sorted(set(old_map) & set(new_map)):
            if old_map[xid] != new_map[xid]:
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


# Canonical core delegation boundary (Milestone 2/3):
# route IR and compatibility functions through dedicated core modules.
def _build_ir_delegate(ont: Ontology, cfg: Dict[str, Any]) -> Dict[str, Any]:
    return _core_build_ir(ont, cfg, toolchain_version=TOOLCHAIN_VERSION, ir_version=IR_VERSION)


build_ir = _build_ir_delegate
parse_semver = _core_parse_semver
required_level_to_bump = _core_required_level_to_bump
bump_rank = _core_bump_rank
classify_type_change = _core_classify_type_change
describe_type_descriptor = _core_describe_type_descriptor
compare_irs = _core_compare_irs


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


def java_type_for_type_descriptor(
    t: Dict[str, Any],
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> str:
    if t["kind"] == "list":
        elem_java = java_type_for_type_descriptor(t["element"], type_by_id, object_by_id, struct_by_id)
        return f"List<{elem_java}>"
    if t["kind"] == "object_ref":
        target = object_by_id[t["target_object_id"]]
        return f"{target['name']}Ref"
    if t["kind"] == "struct":
        target = struct_by_id[t["target_struct_id"]]
        return target["name"]

    if t["kind"] == "base":
        base = t["name"]
    elif t["kind"] == "custom":
        base = type_by_id[t["target_type_id"]]["base"]
    else:
        base = "string"

    return {
        "string": "String",
        "int": "Integer",
        "long": "Long",
        "short": "Short",
        "byte": "Short",
        "double": "Double",
        "float": "Float",
        "decimal": "BigDecimal",
        "boolean": "Boolean",
        "datetime": "OffsetDateTime",
        "date": "LocalDate",
        "duration": "Duration",
    }.get(base, "String")


def java_type_for_field(
    field: Dict[str, Any],
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> str:
    return java_type_for_type_descriptor(field["type"], type_by_id, object_by_id, struct_by_id)


def object_ref_target_ids_for_type(type_desc: Dict[str, Any]) -> List[str]:
    if type_desc.get("kind") == "object_ref":
        return [type_desc["target_object_id"]]
    if type_desc.get("kind") == "list":
        return object_ref_target_ids_for_type(type_desc["element"])
    return []


def struct_target_ids_for_type(type_desc: Dict[str, Any]) -> List[str]:
    if type_desc.get("kind") == "struct":
        return [type_desc["target_struct_id"]]
    if type_desc.get("kind") == "list":
        return struct_target_ids_for_type(type_desc["element"])
    return []


def add_java_imports_for_type(java_type: str, imports: set[str]) -> None:
    if "List<" in java_type:
        imports.add("import java.util.List;")
    if "BigDecimal" in java_type:
        imports.add("import java.math.BigDecimal;")
    if "OffsetDateTime" in java_type:
        imports.add("import java.time.OffsetDateTime;")
    if "LocalDate" in java_type:
        imports.add("import java.time.LocalDate;")
    if "Duration" in java_type:
        imports.add("import java.time.Duration;")


def render_java_record_with_builder(
    package_name: str,
    imports: set[str],
    record_name: str,
    fields: List[Tuple[str, str, bool]],
) -> str:
    record_components: List[str] = []
    for java_t, field_name, required in fields:
        ann = "@NotNull " if required else ""
        if required:
            imports.add("import jakarta.validation.constraints.NotNull;")
        record_components.append(f"    {ann}{java_t} {field_name}")

    builder_field_lines = [f"        private {java_t} {field_name};" for java_t, field_name, _ in fields]
    builder_setter_lines: List[str] = []
    for java_t, field_name, _ in fields:
        builder_setter_lines.extend(
            [
                f"        public Builder {field_name}({java_t} value) {{",
                f"            this.{field_name} = value;",
                "            return this;",
                "        }",
                "",
            ]
        )

    builder_build_lines = [
        f"        public {record_name} build() {{",
        f"            return new {record_name}(",
    ]
    for idx, (_, field_name, _) in enumerate(fields):
        suffix = "," if idx < len(fields) - 1 else ""
        builder_build_lines.append(f"                {field_name}{suffix}")
    builder_build_lines.extend(
        [
            "            );",
            "        }",
        ]
    )

    import_block = "\n".join(sorted(imports))
    source = (
        f"package {package_name};\n\n"
        + (f"{import_block}\n\n" if import_block else "")
        + f"public record {record_name}(\n"
        + ",\n".join(record_components)
        + "\n) {\n\n"
        + "    public static Builder builder() {\n"
        + "        return new Builder();\n"
        + "    }\n\n"
        + "    public static final class Builder {\n"
        + ("\n".join(builder_field_lines) + "\n\n" if builder_field_lines else "")
        + "\n".join(builder_setter_lines)
        + "\n".join(builder_build_lines)
        + "\n"
        + "    }\n"
        + "}\n"
    )
    return source


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


def add_generated_annotation(source: str) -> str:
    if "@Generated(" in source:
        return source

    lines = source.splitlines()
    package_idx = next((i for i, line in enumerate(lines) if line.startswith("package ")), -1)
    if package_idx == -1:
        return source

    generated_import = "import javax.annotation.processing.Generated;"
    if generated_import not in lines:
        first_import = next(
            (i for i, line in enumerate(lines[package_idx + 1 :], start=package_idx + 1) if line.startswith("import ")),
            -1,
        )
        if first_import != -1:
            lines.insert(first_import, generated_import)
        else:
            lines = lines[: package_idx + 1] + ["", generated_import, ""] + lines[package_idx + 1 :]

    type_idx = next(
        (
            i
            for i, line in enumerate(lines)
            if re.match(r"^public\s+(class|interface|record|enum)\s+[A-Za-z_][A-Za-z0-9_]*", line)
        ),
        -1,
    )
    if type_idx == -1:
        return source

    lines.insert(type_idx, '@Generated("prophet-cli")')
    result = "\n".join(lines)
    return result + ("\n" if source.endswith("\n") else "")


def annotate_generated_java_files(files: Dict[str, str]) -> None:
    for rel_path, content in list(files.items()):
        if rel_path.endswith(".java"):
            files[rel_path] = add_generated_annotation(content)


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
        pk = next((f for f in fields if f.get("key") == "primary"), fields[0])
        pk_col = snake_case(pk["name"])

        column_lines: List[str] = []
        fk_lines: List[str] = []

        for field in fields:
            col_name = snake_case(field["name"])
            required = field.get("cardinality", {}).get("min", 0) > 0
            not_null = " not null" if required else ""
            sql_type = sql_type_for_field(field, type_by_id)
            if field["type"]["kind"] == "object_ref":
                target_obj = object_by_id[field["type"]["target_object_id"]]
                target_fields = target_obj.get("fields", [])
                target_pk = next((f for f in target_fields if f.get("key") == "primary"), target_fields[0])
                target_table = pluralize(snake_case(target_obj["name"]))
                target_pk_col = snake_case(target_pk["name"])
                col_name = f"{col_name}_{target_pk_col}"
                sql_type = sql_type_for_field(target_pk, type_by_id)
                fk_name = f"fk_{table}_{col_name}"
                fk_lines.append(
                    f"  constraint {fk_name} foreign key ({col_name}) references {target_table}({target_pk_col})"
                )

            if field["id"] == pk["id"]:
                column_lines.append(f"  {col_name} {sql_type} primary key")
            else:
                extra = ""
                if sql_type.startswith("numeric"):
                    extra = " check ({0} >= 0)".format(col_name)
                column_lines.append(f"  {col_name} {sql_type}{not_null}{extra}")

        if obj.get("states"):
            enum_vals = ", ".join(f"'{s['name'].upper()}'" for s in obj["states"])
            column_lines.append(f"  current_state text not null check (current_state in ({enum_vals}))")

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
                target_fields = target_obj.get("fields", [])
                target_pk = next((f for f in target_fields if f.get("key") == "primary"), target_fields[0])
                idx_col = f"{snake_case(field['name'])}_{snake_case(target_pk['name'])}"
                idx_name = f"idx_{table}_{idx_col}"
                lines.append(f"create index if not exists {idx_name} on {table} ({idx_col});")

        if obj.get("states"):
            idx_state = f"idx_{table}_current_state"
            lines.append(f"create index if not exists {idx_state} on {table} (current_state);")

            history_table = f"{snake_case(obj['name'])}_state_history"
            lines.extend(
                [
                    "",
                    f"create table if not exists {history_table} (",
                    "  history_id bigserial primary key,",
                    f"  {pk_col} text not null,",
                    "  transition_id text not null,",
                    "  from_state text not null,",
                    "  to_state text not null,",
                    "  changed_at timestamptz not null default now(),",
                    "  changed_by text,",
                    f"  constraint fk_{history_table}_{pk_col} foreign key ({pk_col}) references {table}({pk_col})",
                    ");",
                    f"create index if not exists idx_{history_table}_{pk_col} on {history_table} ({pk_col});",
                    f"create index if not exists idx_{history_table}_changed_at on {history_table} (changed_at);",
                ]
            )

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def table_name_for_object(obj: Dict[str, Any]) -> str:
    return pluralize(snake_case(obj["name"]))


def primary_key_field_for_object(obj: Dict[str, Any]) -> Dict[str, Any]:
    fields = obj.get("fields", [])
    return next((f for f in fields if f.get("key") == "primary"), fields[0])


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


def render_create_table_statements_for_object(
    obj: Dict[str, Any],
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
) -> List[str]:
    table = table_name_for_object(obj)
    fields = obj.get("fields", [])
    pk = primary_key_field_for_object(obj)
    pk_col = snake_case(pk["name"])

    column_lines: List[str] = []
    fk_lines: List[str] = []
    index_lines: List[str] = []
    for field in fields:
        col_name, sql_type, fk_ref, idx_col = field_sql_column_details(field, type_by_id, object_by_id)
        required = field.get("cardinality", {}).get("min", 0) > 0
        not_null = " not null" if required else ""
        if field["id"] == pk["id"]:
            column_lines.append(f"  {col_name} {sql_type} primary key")
        else:
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

    if obj.get("states"):
        enum_vals = ", ".join(f"'{s['name'].upper()}'" for s in obj["states"])
        column_lines.append(f"  current_state text not null check (current_state in ({enum_vals}))")

    column_lines.extend(
        [
            "  row_version bigint not null default 0",
            "  created_at timestamptz not null default now()",
            "  updated_at timestamptz not null default now()",
        ]
    )

    statements: List[str] = []
    statements.append(f"create table if not exists {table} (")
    for idx, col in enumerate(column_lines + fk_lines):
        suffix = "," if idx < len(column_lines + fk_lines) - 1 else ""
        statements.append(col + suffix)
    statements.append(");")
    statements.extend(index_lines)
    if obj.get("states"):
        idx_state = f"idx_{table}_current_state"
        statements.append(f"create index if not exists {idx_state} on {table} (current_state);")
        history_table = f"{snake_case(obj['name'])}_state_history"
        statements.extend(
            [
                f"create table if not exists {history_table} (",
                "  history_id bigserial primary key,",
                f"  {pk_col} text not null,",
                "  transition_id text not null,",
                "  from_state text not null,",
                "  to_state text not null,",
                "  changed_at timestamptz not null default now(),",
                "  changed_by text,",
                f"  constraint fk_{history_table}_{pk_col} foreign key ({pk_col}) references {table}({pk_col})",
                ");",
                f"create index if not exists idx_{history_table}_{pk_col} on {history_table} ({pk_col});",
                f"create index if not exists idx_{history_table}_changed_at on {history_table} (changed_at);",
            ]
        )
    return statements


def render_delta_migration(
    old_ir: Dict[str, Any], new_ir: Dict[str, Any]
) -> Tuple[str, List[str], bool, Dict[str, Any]]:
    old_objects = {o["id"]: o for o in old_ir.get("objects", [])}
    new_objects = {o["id"]: o for o in new_ir.get("objects", [])}
    type_by_id = {t["id"]: t for t in new_ir.get("types", [])}
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

        old_state_names = sorted(s["name"] for s in old_obj.get("states", []))
        new_state_names = sorted(s["name"] for s in new_obj.get("states", []))
        if old_state_names != new_state_names:
            warnings.append(
                f"manual_review: state set changed for {new_obj['name']} (current_state constraint may require manual adjustment)."
            )
            add_finding(
                "state_set_changed",
                "manual_review",
                f"state set changed for {new_obj['name']}",
                "current_state constraint may require manual adjustment",
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
    action_outputs = ir.get("action_outputs", [])
    type_by_id = {t["id"]: t for t in ir.get("types", [])}
    object_by_id = {o["id"]: o for o in objects}
    struct_by_id = {s["id"]: s for s in structs}
    action_input_by_id = {s["id"]: s for s in action_inputs}
    action_output_by_id = {s["id"]: s for s in action_outputs}

    components_schemas: Dict[str, Any] = {}

    for source in list(objects) + list(structs) + list(action_inputs) + list(action_outputs):
        for f in source.get("fields", []):
            for target_id in object_ref_target_ids_for_type(f["type"]):
                target = object_by_id[target_id]
                target_fields = target.get("fields", [])
                target_pk = next((x for x in target_fields if x.get("key") == "primary"), target_fields[0])
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
            properties[prop] = json_schema_for_field(f, type_by_id, object_by_id, struct_by_id)
            if f.get("cardinality", {}).get("min", 0) > 0:
                required_props.append(prop)
        components_schemas[struct["name"]] = {
            "type": "object",
            "required": required_props,
            "properties": properties,
        }

    for obj in objects:
        required_props: List[str] = []
        properties: Dict[str, Any] = {}
        for f in obj.get("fields", []):
            prop = camel_case(f["name"])
            properties[prop] = json_schema_for_field(f, type_by_id, object_by_id, struct_by_id)
            if f.get("cardinality", {}).get("min", 0) > 0:
                required_props.append(prop)
        if obj.get("states"):
            properties["currentState"] = {
                "type": "string",
                "enum": [s["name"].upper() for s in obj["states"]],
            }
            required_props.append("currentState")

        components_schemas[obj["name"]] = {
            "type": "object",
            "required": required_props,
            "properties": properties,
        }
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
            properties[prop] = json_schema_for_field(f, type_by_id, object_by_id, struct_by_id)
            if f.get("cardinality", {}).get("min", 0) > 0:
                required_props.append(prop)
        components_schemas[shape["name"]] = {
            "type": "object",
            "required": required_props,
            "properties": properties,
        }

    for shape in action_outputs:
        required_props = []
        properties = {}
        for f in shape.get("fields", []):
            prop = camel_case(f["name"])
            properties[prop] = json_schema_for_field(f, type_by_id, object_by_id, struct_by_id)
            if f.get("cardinality", {}).get("min", 0) > 0:
                required_props.append(prop)
        components_schemas[shape["name"]] = {
            "type": "object",
            "required": required_props,
            "properties": properties,
        }

    paths: Dict[str, Any] = {}

    for obj in objects:
        fields = obj.get("fields", [])
        pk = next((f for f in fields if f.get("key") == "primary"), fields[0])
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
                target_fields = target.get("fields", [])
                target_pk = next((x for x in target_fields if x.get("key") == "primary"), target_fields[0])
                param_name = f"{camel_case(f['name'])}{pascal_case(camel_case(target_pk['name']))}"
                param_schema = json_schema_for_field(target_pk, type_by_id, object_by_id, struct_by_id)
            else:
                param_name = camel_case(f["name"])
                param_schema = json_schema_for_field(f, type_by_id, object_by_id, struct_by_id)

            list_parameters.append(
                {
                    "name": param_name,
                    "in": "query",
                    "required": False,
                    "schema": param_schema,
                }
            )
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
            list_parameters.append(
                {
                    "name": "currentState",
                    "in": "query",
                    "required": False,
                    "schema": {
                        "type": "string",
                        "enum": [s["name"].upper() for s in obj["states"]],
                    },
                }
            )
            state_filter_name = f"{obj['name']}CurrentStateFilter"
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
            query_filter_props["currentState"] = {"$ref": f"#/components/schemas/{state_filter_name}"}

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
        paths[f"/{table}/{{{pk_param}}}"] = {
            "get": {
                "operationId": f"get{obj['name']}",
                "parameters": [
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
        res_name = action_output_by_id[action["output_shape_id"]]["name"]
        op_id = f"{camel_case(action['name'])}Action"
        paths[f"/actions/{action['name']}"] = {
            "post": {
                "operationId": op_id,
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
                                "schema": {"$ref": f"#/components/schemas/{res_name}"}
                            }
                        },
                    }
                },
            }
        }

    spec = {
        "openapi": "3.1.0",
        "info": {
            "title": f"{pascal_case(ir['ontology']['name'])} API",
            "version": ir["ontology"]["version"],
        },
        "servers": [{"url": "https://api.example.com"}],
        "paths": paths,
        "components": {"schemas": components_schemas},
    }
    return yaml_dump_stable(spec)


def render_gradle_file(boot_version: str, dependency_management_version: str) -> str:
    return f"""plugins {{
    java
    id(\"org.springframework.boot\") version \"{boot_version}\"
    id(\"io.spring.dependency-management\") version \"{dependency_management_version}\"
}}

group = \"com.example\"
version = \"{TOOLCHAIN_VERSION}\"

java {{
    toolchain {{
        languageVersion = JavaLanguageVersion.of(21)
    }}
}}

repositories {{
    mavenCentral()
}}

dependencies {{
    implementation(\"org.springframework.boot:spring-boot-starter-web\")
    implementation(\"org.springframework.boot:spring-boot-starter-validation\")
    implementation(\"org.springframework.boot:spring-boot-starter-data-jpa\")
    runtimeOnly(\"org.postgresql:postgresql\")
    testImplementation(\"org.springframework.boot:spring-boot-starter-test\")
}}
"""


def detect_gradle_plugin_versions(
    root: Path,
    fallback_boot_version: str,
    fallback_dependency_management_version: str,
) -> Tuple[str, str]:
    build_kts = root / "build.gradle.kts"
    build_groovy = root / "build.gradle"
    build_path: Optional[Path] = build_kts if build_kts.exists() else build_groovy if build_groovy.exists() else None
    if build_path is None:
        return fallback_boot_version, fallback_dependency_management_version

    text = build_path.read_text(encoding="utf-8")

    boot_version = fallback_boot_version
    dep_mgmt_version = fallback_dependency_management_version

    boot_patterns = [
        re.compile(r'id\("org\.springframework\.boot"\)\s+version\s+"([^"]+)"'),
        re.compile(r"id\s+'org\.springframework\.boot'\s+version\s+'([^']+)'"),
    ]
    dep_patterns = [
        re.compile(r'id\("io\.spring\.dependency-management"\)\s+version\s+"([^"]+)"'),
        re.compile(r"id\s+'io\.spring\.dependency-management'\s+version\s+'([^']+)'"),
    ]

    for pattern in boot_patterns:
        m = pattern.search(text)
        if m:
            boot_version = m.group(1)
            break

    for pattern in dep_patterns:
        m = pattern.search(text)
        if m:
            dep_mgmt_version = m.group(1)
            break

    return boot_version, dep_mgmt_version


def detect_gradle_migration_tools(root: Path) -> set[str]:
    build_kts = root / "build.gradle.kts"
    build_groovy = root / "build.gradle"
    build_path: Optional[Path] = build_kts if build_kts.exists() else build_groovy if build_groovy.exists() else None
    if build_path is None:
        return set()

    text = build_path.read_text(encoding="utf-8")
    tools: set[str] = set()

    if (
        "org.flywaydb:flyway-core" in text
        or 'id("org.flywaydb.flyway")' in text
        or "id 'org.flywaydb.flyway'" in text
    ):
        tools.add("flyway")
    if (
        "org.liquibase:liquibase-core" in text
        or 'id("org.liquibase.gradle")' in text
        or "id 'org.liquibase.gradle'" in text
    ):
        tools.add("liquibase")

    return tools


def resolve_migration_runtime_modes(cfg: Dict[str, Any], root: Path) -> Tuple[set[str], set[str], set[str], List[str]]:
    targets = set(cfg_get(cfg, ["generation", "targets"], ["sql", "openapi", "spring_boot", "flyway", "liquibase"]))
    requested = {"flyway", "liquibase"}.intersection(targets)
    detected = detect_gradle_migration_tools(root)
    enabled = requested.intersection(detected)
    warnings: List[str] = []

    if "flyway" in requested and "flyway" not in detected:
        warnings.append(
            "Flyway target is enabled, but Flyway was not detected in host Gradle config; "
            "skipping Spring runtime Flyway resource wiring."
        )
    if "liquibase" in requested and "liquibase" not in detected:
        warnings.append(
            "Liquibase target is enabled, but Liquibase was not detected in host Gradle config; "
            "skipping Spring runtime Liquibase resource wiring."
        )
    if "flyway" in enabled and "liquibase" in enabled:
        warnings.append(
            "Both Flyway and Liquibase were detected in host Gradle config; "
            "Spring runtime resources are generated for both. Ensure runtime activates only one migration engine."
        )

    return requested, detected, enabled, warnings


def render_liquibase_root_changelog() -> str:
    return (
        "# GENERATED FILE: do not edit directly.\n"
        "databaseChangeLog:\n"
        "  - include:\n"
        "      file: prophet/changelog-master.yaml\n"
        "      relativeToChangelogFile: true\n"
    )


def render_liquibase_prophet_changelog(include_delta: bool = False) -> str:
    changelog = (
        "# GENERATED FILE: do not edit directly.\n"
        "databaseChangeLog:\n"
        "  - changeSet:\n"
        "      id: prophet-0001-init\n"
        "      author: prophet-cli\n"
        "      changes:\n"
        "        - sqlFile:\n"
        "            path: 0001-init.sql\n"
        "            relativeToChangelogFile: true\n"
        "            splitStatements: true\n"
        "            stripComments: false\n"
    )
    if include_delta:
        changelog += (
            "  - changeSet:\n"
            "      id: prophet-0002-delta\n"
            "      author: prophet-cli\n"
            "      changes:\n"
            "        - sqlFile:\n"
            "            path: 0002-delta.sql\n"
            "            relativeToChangelogFile: true\n"
            "            splitStatements: true\n"
            "            stripComments: false\n"
        )
    return changelog


def render_spring_files(
    ir: Dict[str, Any],
    cfg: Dict[str, Any],
    root: Optional[Path] = None,
    generated_schema_sql: Optional[str] = None,
    delta_schema_sql: Optional[str] = None,
) -> Dict[str, str]:
    files: Dict[str, str] = {}

    base_package = cfg_get(cfg, ["generation", "spring_boot", "base_package"], "com.example.prophet")
    fallback_boot_version = str(cfg_get(cfg, ["generation", "spring_boot", "boot_version"], "3.3.2"))
    fallback_dep_mgmt_version = str(
        cfg_get(cfg, ["generation", "spring_boot", "dependency_management_version"], "1.1.6")
    )
    work_root = root if root is not None else Path.cwd()
    boot_version, dep_mgmt_version = detect_gradle_plugin_versions(
        work_root,
        fallback_boot_version,
        fallback_dep_mgmt_version,
    )
    _, _, enabled_modes, _ = resolve_migration_runtime_modes(cfg, work_root)
    include_flyway = "flyway" in enabled_modes
    include_liquibase = "liquibase" in enabled_modes
    init_schema_sql = generated_schema_sql if generated_schema_sql is not None else render_sql(ir)
    package_path = base_package.replace(".", "/")

    objects = ir["objects"]
    structs = ir.get("structs", [])
    actions = ir.get("actions", [])
    action_inputs = ir.get("action_inputs", [])
    action_outputs = ir.get("action_outputs", [])
    type_by_id = {t["id"]: t for t in ir.get("types", [])}
    object_by_id = {o["id"]: o for o in objects}
    struct_by_id = {s["id"]: s for s in structs}
    action_input_by_id = {s["id"]: s for s in action_inputs}
    action_output_by_id = {s["id"]: s for s in action_outputs}

    files["build.gradle.kts"] = render_gradle_file(boot_version, dep_mgmt_version)
    application_prophet_yml = (
        "prophet:\n"
        f"  ontology-id: {ir['ontology']['id']}\n"
        "  compatibility-profile:\n"
        f"    strict-enums: {'true' if ir.get('compatibility_profile', {}).get('strict_enums') else 'false'}\n"
        "  actions:\n"
        "    base-path: /actions\n"
    )
    if include_liquibase:
        application_prophet_yml += (
            "spring:\n"
            "  liquibase:\n"
            "    change-log: classpath:db/changelog/db.changelog-master.yaml\n"
        )
    files["src/main/resources/application-prophet.yml"] = application_prophet_yml

    if include_flyway:
        files["src/main/resources/db/migration/V1__prophet_init.sql"] = init_schema_sql
        if delta_schema_sql:
            files["src/main/resources/db/migration/V2__prophet_delta.sql"] = delta_schema_sql
    if include_liquibase:
        files["src/main/resources/db/changelog/db.changelog-master.yaml"] = render_liquibase_root_changelog()
        files["src/main/resources/db/changelog/prophet/changelog-master.yaml"] = render_liquibase_prophet_changelog(
            include_delta=bool(delta_schema_sql)
        )
        files["src/main/resources/db/changelog/prophet/0001-init.sql"] = init_schema_sql
        if delta_schema_sql:
            files["src/main/resources/db/changelog/prophet/0002-delta.sql"] = delta_schema_sql

    # domain ref records
    ref_types: Dict[str, Dict[str, Any]] = {}
    for source in list(objects) + list(structs) + list(action_inputs) + list(action_outputs):
        for f in source.get("fields", []):
            for target_id in object_ref_target_ids_for_type(f["type"]):
                target = object_by_id[target_id]
                ref_types[target["id"]] = target

    for target in sorted(ref_types.values(), key=lambda x: x["id"]):
        target_fields = target.get("fields", [])
        target_pk = next((x for x in target_fields if x.get("key") == "primary"), target_fields[0])
        pk_java = java_type_for_field(target_pk, type_by_id, object_by_id, struct_by_id)
        cls = f"{target['name']}Ref"
        ref_fields = [(pk_java, camel_case(target_pk["name"]), True)]
        files[f"src/main/java/{package_path}/generated/domain/{cls}.java"] = render_java_record_with_builder(
            f"{base_package}.generated.domain",
            set(),
            cls,
            ref_fields,
        )

    # struct domain records
    for struct in structs:
        imports: set[str] = set()
        struct_fields: List[Tuple[str, str, bool]] = []
        for f in struct.get("fields", []):
            java_t = java_type_for_field(f, type_by_id, object_by_id, struct_by_id)
            add_java_imports_for_type(java_t, imports)
            for target_id in object_ref_target_ids_for_type(f["type"]):
                target = object_by_id[target_id]
                imports.add(f"import {base_package}.generated.domain.{target['name']}Ref;")
            for target_struct_id in struct_target_ids_for_type(f["type"]):
                target_struct = struct_by_id[target_struct_id]
                if target_struct["name"] != struct["name"]:
                    imports.add(f"import {base_package}.generated.domain.{target_struct['name']};")
            required = f.get("cardinality", {}).get("min", 0) > 0
            struct_fields.append((java_t, camel_case(f["name"]), required))

        files[f"src/main/java/{package_path}/generated/domain/{struct['name']}.java"] = render_java_record_with_builder(
            f"{base_package}.generated.domain",
            imports,
            struct["name"],
            struct_fields,
        )

    # state enums + domain records
    for obj in objects:
        if obj.get("states"):
            enum_name = f"{obj['name']}State"
            vals = ",\n    ".join(s["name"].upper() for s in obj["states"])
            files[f"src/main/java/{package_path}/generated/domain/{enum_name}.java"] = (
                f"package {base_package}.generated.domain;\n\n"
                f"public enum {enum_name} {{\n"
                f"    {vals}\n"
                "}\n"
            )

        imports: set[str] = set()
        object_fields: List[Tuple[str, str, bool]] = []

        for f in obj.get("fields", []):
            java_t = java_type_for_field(f, type_by_id, object_by_id, struct_by_id)
            add_java_imports_for_type(java_t, imports)
            for target_struct_id in struct_target_ids_for_type(f["type"]):
                target_struct = struct_by_id[target_struct_id]
                imports.add(f"import {base_package}.generated.domain.{target_struct['name']};")

            required = f.get("cardinality", {}).get("min", 0) > 0
            object_fields.append((java_t, camel_case(f["name"]), required))

        if obj.get("states"):
            object_fields.append((f"{obj['name']}State", "currentState", True))
            imports.add(f"import {base_package}.generated.domain.{obj['name']}State;")

        files[f"src/main/java/{package_path}/generated/domain/{obj['name']}.java"] = render_java_record_with_builder(
            f"{base_package}.generated.domain",
            imports,
            obj["name"],
            object_fields,
        )

    # persistence entities and repositories
    for obj in objects:
        fields = obj.get("fields", [])
        pk = next((f for f in fields if f.get("key") == "primary"), fields[0])
        entity_name = f"{obj['name']}Entity"
        table_name = pluralize(snake_case(obj["name"]))

        imports = {
            "import jakarta.persistence.Column;",
            "import jakarta.persistence.Convert;",
            "import jakarta.persistence.Entity;",
            "import jakarta.persistence.Id;",
            "import jakarta.persistence.PrePersist;",
            "import jakarta.persistence.PreUpdate;",
            "import jakarta.persistence.Table;",
            "import jakarta.persistence.Version;",
            "import java.time.OffsetDateTime;",
        }

        lines: List[str] = []
        json_converter_sources: List[Tuple[str, str]] = []

        for f in fields:
            col_name = snake_case(f["name"])
            required = f.get("cardinality", {}).get("min", 0) > 0
            nullable = "false" if required else "true"
            java_t = java_type_for_field(f, type_by_id, object_by_id, struct_by_id)
            add_java_imports_for_type(java_t, imports)
            for target_struct_id in struct_target_ids_for_type(f["type"]):
                target_struct = struct_by_id[target_struct_id]
                imports.add(f"import {base_package}.generated.domain.{target_struct['name']};")

            if f["type"]["kind"] in {"list", "struct"}:
                if f["type"]["kind"] == "list":
                    converter_name = f"{obj['name']}{pascal_case(f['name'])}ListConverter"
                    converter_mode = "list"
                    converter_target_type = java_type_for_type_descriptor(
                        f["type"],
                        type_by_id,
                        object_by_id,
                        struct_by_id,
                    )
                    element_type = java_type_for_type_descriptor(
                        f["type"]["element"],
                        type_by_id,
                        object_by_id,
                        struct_by_id,
                    )
                else:
                    converter_name = f"{obj['name']}{pascal_case(f['name'])}StructConverter"
                    converter_mode = "struct"
                    converter_target_type = java_type_for_type_descriptor(
                        f["type"],
                        type_by_id,
                        object_by_id,
                        struct_by_id,
                    )
                    element_type = converter_target_type
                lines.append(f"    @Convert(converter = {converter_name}.class)")
                lines.append(f"    @Column(name = \"{col_name}\", nullable = {nullable}, columnDefinition = \"text\")")
                lines.append(f"    private {java_t} {camel_case(f['name'])};")
                lines.append("")

                converter_imports = {
                    "import com.fasterxml.jackson.core.JsonProcessingException;",
                    "import com.fasterxml.jackson.databind.ObjectMapper;",
                    "import jakarta.persistence.AttributeConverter;",
                    "import jakarta.persistence.Converter;",
                }
                if converter_mode == "list":
                    converter_imports.add("import com.fasterxml.jackson.core.type.TypeReference;")
                    converter_imports.add("import java.util.Collections;")
                    converter_imports.add("import java.util.List;")
                add_java_imports_for_type(converter_target_type, converter_imports)
                if converter_mode == "list":
                    target_ref_type = f["type"]["element"]
                else:
                    target_ref_type = f["type"]
                for target_id in object_ref_target_ids_for_type(target_ref_type):
                    target = object_by_id[target_id]
                    converter_imports.add(f"import {base_package}.generated.domain.{target['name']}Ref;")
                for target_struct_id in struct_target_ids_for_type(target_ref_type):
                    target_struct = struct_by_id[target_struct_id]
                    converter_imports.add(f"import {base_package}.generated.domain.{target_struct['name']};")

                if converter_mode == "list":
                    converter_src = (
                        f"package {base_package}.generated.persistence;\n\n"
                        + "\n".join(sorted(converter_imports))
                        + "\n\n"
                        + "@Converter\n"
                        + f"public class {converter_name} implements AttributeConverter<{converter_target_type}, String> {{\n\n"
                        + "    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper().findAndRegisterModules();\n\n"
                        + "    @Override\n"
                        + f"    public String convertToDatabaseColumn({converter_target_type} attribute) {{\n"
                        + "        if (attribute == null) {\n"
                        + "            return null;\n"
                        + "        }\n"
                        + "        try {\n"
                        + "            return OBJECT_MAPPER.writeValueAsString(attribute);\n"
                        + "        } catch (JsonProcessingException ex) {\n"
                        + f"            throw new IllegalArgumentException(\"Failed to serialize list field {obj['name']}.{f['name']}\", ex);\n"
                        + "        }\n"
                        + "    }\n\n"
                        + "    @Override\n"
                        + f"    public {converter_target_type} convertToEntityAttribute(String dbData) {{\n"
                        + "        if (dbData == null || dbData.isBlank()) {\n"
                        + "            return Collections.emptyList();\n"
                        + "        }\n"
                        + "        try {\n"
                        + f"            return OBJECT_MAPPER.readValue(dbData, new TypeReference<{converter_target_type}>() {{}});\n"
                        + "        } catch (JsonProcessingException ex) {\n"
                        + f"            throw new IllegalArgumentException(\"Failed to deserialize list field {obj['name']}.{f['name']}\", ex);\n"
                        + "        }\n"
                        + "    }\n"
                        + "}\n"
                    )
                else:
                    converter_src = (
                        f"package {base_package}.generated.persistence;\n\n"
                        + "\n".join(sorted(converter_imports))
                        + "\n\n"
                        + "@Converter\n"
                        + f"public class {converter_name} implements AttributeConverter<{converter_target_type}, String> {{\n\n"
                        + "    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper().findAndRegisterModules();\n\n"
                        + "    @Override\n"
                        + f"    public String convertToDatabaseColumn({converter_target_type} attribute) {{\n"
                        + "        if (attribute == null) {\n"
                        + "            return null;\n"
                        + "        }\n"
                        + "        try {\n"
                        + "            return OBJECT_MAPPER.writeValueAsString(attribute);\n"
                        + "        } catch (JsonProcessingException ex) {\n"
                        + f"            throw new IllegalArgumentException(\"Failed to serialize struct field {obj['name']}.{f['name']}\", ex);\n"
                        + "        }\n"
                        + "    }\n\n"
                        + "    @Override\n"
                        + f"    public {converter_target_type} convertToEntityAttribute(String dbData) {{\n"
                        + "        if (dbData == null || dbData.isBlank()) {\n"
                        + "            return null;\n"
                        + "        }\n"
                        + "        try {\n"
                        + f"            return OBJECT_MAPPER.readValue(dbData, {converter_target_type}.class);\n"
                        + "        } catch (JsonProcessingException ex) {\n"
                        + f"            throw new IllegalArgumentException(\"Failed to deserialize struct field {obj['name']}.{f['name']}\", ex);\n"
                        + "        }\n"
                        + "    }\n"
                        + "}\n"
                    )
                json_converter_sources.append((converter_name, converter_src))
            elif f["type"]["kind"] == "object_ref":
                imports.update(
                    {
                        "import jakarta.persistence.FetchType;",
                        "import jakarta.persistence.JoinColumn;",
                        "import jakarta.persistence.ManyToOne;",
                    }
                )
                target = object_by_id[f["type"]["target_object_id"]]
                target_entity = f"{target['name']}Entity"
                target_fields = target.get("fields", [])
                target_pk = next((x for x in target_fields if x.get("key") == "primary"), target_fields[0])
                col_name = f"{col_name}_{snake_case(target_pk['name'])}"
                lines.append(f"    @ManyToOne(fetch = FetchType.LAZY, optional = {nullable})")
                lines.append(f"    @JoinColumn(name = \"{col_name}\", nullable = {nullable})")
                lines.append(f"    private {target_entity} {camel_case(f['name'])};")
                lines.append("")
            else:
                if obj.get("states") and f["id"] == pk["id"]:
                    pass
                if f["id"] == pk["id"]:
                    lines.append("    @Id")
                lines.append(f"    @Column(name = \"{col_name}\", nullable = {nullable})")
                lines.append(f"    private {java_t} {camel_case(f['name'])};")
                lines.append("")

        if obj.get("states"):
            imports.update(
                {
                    "import jakarta.persistence.EnumType;",
                    "import jakarta.persistence.Enumerated;",
                    f"import {base_package}.generated.domain.{obj['name']}State;",
                }
            )
            lines.append("    @Enumerated(EnumType.STRING)")
            lines.append("    @Column(name = \"current_state\", nullable = false)")
            lines.append(f"    private {obj['name']}State currentState;")
            lines.append("")

        lines.extend(
            [
                "    @Version",
                "    @Column(name = \"row_version\", nullable = false)",
                "    private long rowVersion;",
                "",
                "    @Column(name = \"created_at\", nullable = false, updatable = false)",
                "    private OffsetDateTime createdAt;",
                "",
                "    @Column(name = \"updated_at\", nullable = false)",
                "    private OffsetDateTime updatedAt;",
                "",
                "    @PrePersist",
                "    void onCreate() {",
                "        OffsetDateTime now = OffsetDateTime.now();",
                "        createdAt = now;",
                "        updatedAt = now;",
                "    }",
                "",
                "    @PreUpdate",
                "    void onUpdate() {",
                "        updatedAt = OffsetDateTime.now();",
                "    }",
                "",
            ]
        )

        for f in fields:
            java_t = java_type_for_field(f, type_by_id, object_by_id, struct_by_id)
            name = camel_case(f["name"])
            method = name[:1].upper() + name[1:]
            lines.append(f"    public {java_t if f['type']['kind'] != 'object_ref' else object_by_id[f['type']['target_object_id']]['name'] + 'Entity'} get{method}() {{")
            lines.append(f"        return {name};")
            lines.append("    }")
            lines.append("")
            lines.append(f"    public void set{method}({java_t if f['type']['kind'] != 'object_ref' else object_by_id[f['type']['target_object_id']]['name'] + 'Entity'} {name}) {{")
            lines.append(f"        this.{name} = {name};")
            lines.append("    }")
            lines.append("")

        if obj.get("states"):
            lines.append(f"    public {obj['name']}State getCurrentState() {{")
            lines.append("        return currentState;")
            lines.append("    }")
            lines.append("")
            lines.append(f"    public void setCurrentState({obj['name']}State currentState) {{")
            lines.append("        this.currentState = currentState;")
            lines.append("    }")
            lines.append("")

        imports_block = "\n".join(sorted(imports))
        entity_src = (
            f"package {base_package}.generated.persistence;\n\n"
            f"{imports_block}\n\n"
            "@Entity\n"
            f"@Table(name = \"{table_name}\")\n"
            f"public class {entity_name} {{\n\n"
            + "\n".join(lines)
            + "}\n"
        )

        files[f"src/main/java/{package_path}/generated/persistence/{entity_name}.java"] = entity_src
        for converter_name, converter_src in json_converter_sources:
            files[f"src/main/java/{package_path}/generated/persistence/{converter_name}.java"] = converter_src

        pk_java = java_type_for_field(pk, type_by_id, object_by_id, struct_by_id)
        repo_src = (
            f"package {base_package}.generated.persistence;\n\n"
            "import org.springframework.data.jpa.repository.JpaRepository;\n\n"
            "import org.springframework.data.jpa.repository.JpaSpecificationExecutor;\n\n"
            f"public interface {obj['name']}Repository extends JpaRepository<{entity_name}, {pk_java}>, JpaSpecificationExecutor<{entity_name}> {{\n"
            "}\n"
        )
        files[f"src/main/java/{package_path}/generated/persistence/{obj['name']}Repository.java"] = repo_src

        if obj.get("states"):
            history_entity_name = f"{obj['name']}StateHistoryEntity"
            history_repo_name = f"{obj['name']}StateHistoryRepository"
            pk_col = snake_case(pk["name"])
            history_table = f"{snake_case(obj['name'])}_state_history"
            history_entity = (
                f"package {base_package}.generated.persistence;\n\n"
                "import jakarta.persistence.Column;\n"
                "import jakarta.persistence.Entity;\n"
                "import jakarta.persistence.FetchType;\n"
                "import jakarta.persistence.GeneratedValue;\n"
                "import jakarta.persistence.GenerationType;\n"
                "import jakarta.persistence.Id;\n"
                "import jakarta.persistence.JoinColumn;\n"
                "import jakarta.persistence.ManyToOne;\n"
                "import jakarta.persistence.PrePersist;\n"
                "import jakarta.persistence.Table;\n"
                "import java.time.OffsetDateTime;\n\n"
                "@Entity\n"
                f"@Table(name = \"{history_table}\")\n"
                f"public class {history_entity_name} {{\n\n"
                "    @Id\n"
                "    @GeneratedValue(strategy = GenerationType.IDENTITY)\n"
                "    @Column(name = \"history_id\")\n"
                "    private Long historyId;\n\n"
                "    @ManyToOne(fetch = FetchType.LAZY, optional = false)\n"
                f"    @JoinColumn(name = \"{pk_col}\", nullable = false)\n"
                f"    private {obj['name']}Entity {camel_case(obj['name'])};\n\n"
                "    @Column(name = \"transition_id\", nullable = false)\n"
                "    private String transitionId;\n\n"
                "    @Column(name = \"from_state\", nullable = false)\n"
                "    private String fromState;\n\n"
                "    @Column(name = \"to_state\", nullable = false)\n"
                "    private String toState;\n\n"
                "    @Column(name = \"changed_at\", nullable = false)\n"
                "    private OffsetDateTime changedAt;\n\n"
                "    @Column(name = \"changed_by\")\n"
                "    private String changedBy;\n\n"
                "    @PrePersist\n"
                "    void onCreate() {\n"
                "        if (changedAt == null) {\n"
                "            changedAt = OffsetDateTime.now();\n"
                "        }\n"
                "    }\n\n"
                f"    public void set{obj['name']}({obj['name']}Entity value) {{\n"
                f"        this.{camel_case(obj['name'])} = value;\n"
                "    }\n\n"
                "    public void setTransitionId(String transitionId) {\n"
                "        this.transitionId = transitionId;\n"
                "    }\n\n"
                "    public void setFromState(String fromState) {\n"
                "        this.fromState = fromState;\n"
                "    }\n\n"
                "    public void setToState(String toState) {\n"
                "        this.toState = toState;\n"
                "    }\n\n"
                "    public void setChangedBy(String changedBy) {\n"
                "        this.changedBy = changedBy;\n"
                "    }\n"
                "}\n"
            )
            files[f"src/main/java/{package_path}/generated/persistence/{history_entity_name}.java"] = history_entity
            history_repo = (
                f"package {base_package}.generated.persistence;\n\n"
                "import org.springframework.data.jpa.repository.JpaRepository;\n\n"
                f"public interface {history_repo_name} extends JpaRepository<{history_entity_name}, Long> {{\n"
                "}\n"
            )
            files[f"src/main/java/{package_path}/generated/persistence/{history_repo_name}.java"] = history_repo

    config_src = (
        f"package {base_package}.generated.config;\n\n"
        "import org.springframework.boot.autoconfigure.domain.EntityScan;\n"
        "import org.springframework.context.annotation.Configuration;\n"
        "import org.springframework.data.jpa.repository.config.EnableJpaRepositories;\n\n"
        "@Configuration\n"
        f"@EntityScan(basePackages = \"{base_package}.generated.persistence\")\n"
        f"@EnableJpaRepositories(basePackages = \"{base_package}.generated.persistence\")\n"
        "public class GeneratedPersistenceConfig {\n"
        "}\n"
    )
    files[f"src/main/java/{package_path}/generated/config/GeneratedPersistenceConfig.java"] = config_src

    # action contract records
    action_shapes = sorted(action_inputs + action_outputs, key=lambda x: x["id"])
    for shape in action_shapes:
        imports: set[str] = set()
        shape_fields: List[Tuple[str, str, bool]] = []
        for f in shape.get("fields", []):
            java_t = java_type_for_field(f, type_by_id, object_by_id, struct_by_id)
            add_java_imports_for_type(java_t, imports)
            for target_id in object_ref_target_ids_for_type(f["type"]):
                target = object_by_id[target_id]
                imports.add(f"import {base_package}.generated.domain.{target['name']}Ref;")
            for target_struct_id in struct_target_ids_for_type(f["type"]):
                target_struct = struct_by_id[target_struct_id]
                imports.add(f"import {base_package}.generated.domain.{target_struct['name']};")
            required = f.get("cardinality", {}).get("min", 0) > 0
            shape_fields.append((java_t, camel_case(f["name"]), required))

        record_src = render_java_record_with_builder(
            f"{base_package}.generated.actions",
            imports,
            shape["name"],
            shape_fields,
        )
        files[f"src/main/java/{package_path}/generated/actions/{shape['name']}.java"] = record_src

    # action handler interfaces
    for action in sorted(actions, key=lambda x: x["id"]):
        req_name = action_input_by_id[action["input_shape_id"]]["name"]
        res_name = action_output_by_id[action["output_shape_id"]]["name"]
        handler_name = f"{pascal_case(action['name'])}ActionHandler"
        service_name = f"{pascal_case(action['name'])}ActionService"
        handler_src = (
            f"package {base_package}.generated.actions.handlers;\n\n"
            f"import {base_package}.generated.actions.{req_name};\n"
            f"import {base_package}.generated.actions.{res_name};\n\n"
            f"public interface {handler_name} {{\n"
            f"    {res_name} handle({req_name} request);\n"
            "}\n"
        )
        files[f"src/main/java/{package_path}/generated/actions/handlers/{handler_name}.java"] = handler_src

        default_cls = f"{handler_name}Default"
        default_handler_src = (
            f"package {base_package}.generated.actions.handlers.defaults;\n\n"
            f"import {base_package}.generated.actions.{req_name};\n"
            f"import {base_package}.generated.actions.{res_name};\n"
            f"import {base_package}.generated.actions.handlers.{handler_name};\n"
            "import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;\n"
            "import org.springframework.stereotype.Component;\n\n"
            "@Component\n"
            f"@ConditionalOnMissingBean({handler_name}.class)\n"
            f"public class {default_cls} implements {handler_name} {{\n"
            "    @Override\n"
            f"    public {res_name} handle({req_name} request) {{\n"
            f"        throw new UnsupportedOperationException(\"Action '{action['name']}' is not implemented\");\n"
            "    }\n"
            "}\n"
        )
        files[f"src/main/java/{package_path}/generated/actions/handlers/defaults/{default_cls}.java"] = default_handler_src

        service_src = (
            f"package {base_package}.generated.actions.services;\n\n"
            f"import {base_package}.generated.actions.{req_name};\n"
            f"import {base_package}.generated.actions.{res_name};\n\n"
            f"public interface {service_name} {{\n"
            f"    {res_name} execute({req_name} request);\n"
            "}\n"
        )
        files[f"src/main/java/{package_path}/generated/actions/services/{service_name}.java"] = service_src

        default_service_name = f"{service_name}Default"
        default_service_src = (
            f"package {base_package}.generated.actions.services.defaults;\n\n"
            f"import {base_package}.generated.actions.{req_name};\n"
            f"import {base_package}.generated.actions.{res_name};\n"
            f"import {base_package}.generated.actions.handlers.{handler_name};\n"
            f"import {base_package}.generated.actions.services.{service_name};\n"
            "import org.springframework.beans.factory.ObjectProvider;\n"
            "import org.springframework.stereotype.Component;\n\n"
            "@Component\n"
            f"public class {default_service_name} implements {service_name} {{\n"
            f"    private final ObjectProvider<{handler_name}> handlerProvider;\n\n"
            f"    public {default_service_name}(ObjectProvider<{handler_name}> handlerProvider) {{\n"
            "        this.handlerProvider = handlerProvider;\n"
            "    }\n\n"
            "    @Override\n"
            f"    public {res_name} execute({req_name} request) {{\n"
            f"        {handler_name} handler = handlerProvider.getIfAvailable();\n"
            "        if (handler == null) {\n"
            f"            throw new UnsupportedOperationException(\"No handler bean provided for action '{action['name']}'\");\n"
            "        }\n"
            "        return handler.handle(request);\n"
            "    }\n"
            "}\n"
        )
        files[
            f"src/main/java/{package_path}/generated/actions/services/defaults/{default_service_name}.java"
        ] = default_service_src

    # action controller delegates to generated action services
    controller_imports = {
        "import jakarta.validation.Valid;",
        "import org.springframework.http.ResponseEntity;",
        "import org.springframework.web.bind.annotation.PostMapping;",
        "import org.springframework.web.bind.annotation.RequestBody;",
        "import org.springframework.web.bind.annotation.RequestMapping;",
        "import org.springframework.web.bind.annotation.RestController;",
        "import org.springframework.web.server.ResponseStatusException;",
        "import static org.springframework.http.HttpStatus.NOT_IMPLEMENTED;",
    }
    controller_fields: List[str] = []
    ctor_args: List[str] = []
    ctor_assigns: List[str] = []
    controller_methods: List[str] = []
    for action in sorted(actions, key=lambda x: x["id"]):
        req_name = action_input_by_id[action["input_shape_id"]]["name"]
        res_name = action_output_by_id[action["output_shape_id"]]["name"]
        service_name = f"{pascal_case(action['name'])}ActionService"
        service_var = f"{camel_case(action['name'])}Service"
        method_name = camel_case(action["name"])
        controller_imports.add(f"import {base_package}.generated.actions.{req_name};")
        controller_imports.add(f"import {base_package}.generated.actions.{res_name};")
        controller_imports.add(f"import {base_package}.generated.actions.services.{service_name};")
        controller_fields.append(f"    private final {service_name} {service_var};")
        ctor_args.append(f"        {service_name} {service_var}")
        ctor_assigns.append(f"        this.{service_var} = {service_var};")
        controller_methods.extend(
            [
                f"    @PostMapping(\"/{action['name']}\")",
                f"    public ResponseEntity<{res_name}> {method_name}(@Valid @RequestBody {req_name} request) {{",
                "        try {",
                f"            return ResponseEntity.ok({service_var}.execute(request));",
                "        } catch (UnsupportedOperationException ex) {",
                "            throw new ResponseStatusException(NOT_IMPLEMENTED, ex.getMessage(), ex);",
                "        }",
                "    }",
                "",
            ]
        )

    ctor_signature = ",\n".join(ctor_args)
    action_controller_src = (
        f"package {base_package}.generated.api;\n\n"
        + "\n".join(sorted(controller_imports))
        + "\n\n"
        + "@RestController\n"
        + "@RequestMapping(\"/actions\")\n"
        + "public class ActionEndpointController {\n\n"
        + ("\n".join(controller_fields) + "\n\n" if controller_fields else "")
        + "    public ActionEndpointController(\n"
        + (ctor_signature + "\n" if ctor_signature else "")
        + "    ) {\n"
        + ("\n".join(ctor_assigns) + "\n" if ctor_assigns else "")
        + "    }\n\n"
        + "\n".join(controller_methods)
        + "}\n"
    )
    files[f"src/main/java/{package_path}/generated/api/ActionEndpointController.java"] = action_controller_src

    # object query controllers
    for obj in objects:
        fields = obj.get("fields", [])
        pk = next((f for f in fields if f.get("key") == "primary"), fields[0])
        repo_name = f"{obj['name']}Repository"
        entity_name = f"{obj['name']}Entity"
        domain_name = obj["name"]
        mapper_name = f"{obj['name']}DomainMapper"
        list_response_name = f"{obj['name']}ListResponse"
        pk_prop = camel_case(pk["name"])
        pk_java = java_type_for_field(pk, type_by_id, object_by_id, struct_by_id)
        path_table = pluralize(snake_case(obj["name"]))

        imports = {
            "import java.util.List;",
            "import java.util.Optional;",
            "import org.springframework.data.domain.Page;",
            "import org.springframework.data.domain.Pageable;",
            "import org.springframework.data.jpa.domain.Specification;",
            "import org.springframework.data.web.PageableDefault;",
            "import org.springframework.http.ResponseEntity;",
            "import org.springframework.web.bind.annotation.GetMapping;",
            "import org.springframework.web.bind.annotation.PathVariable;",
            "import org.springframework.web.bind.annotation.RequestParam;",
            "import org.springframework.web.bind.annotation.RequestMapping;",
            "import org.springframework.web.bind.annotation.RestController;",
            f"import {base_package}.generated.domain.{domain_name};",
            f"import {base_package}.generated.mapping.{mapper_name};",
            f"import {base_package}.generated.persistence.{entity_name};",
            f"import {base_package}.generated.persistence.{repo_name};",
        }
        add_java_imports_for_type(pk_java, imports)

        ref_imports: set[str] = set()
        domain_builder_steps: List[str] = []
        for f in fields:
            prop = camel_case(f["name"])
            getter = "get" + prop[:1].upper() + prop[1:] + "()"
            if f["type"]["kind"] == "object_ref":
                target = object_by_id[f["type"]["target_object_id"]]
                target_fields = target.get("fields", [])
                target_pk = next((x for x in target_fields if x.get("key") == "primary"), target_fields[0])
                target_pk_prop = camel_case(target_pk["name"])
                target_get = "get" + target_pk_prop[:1].upper() + target_pk_prop[1:] + "()"
                ref_cls = f"{target['name']}Ref"
                ref_imports.add(f"import {base_package}.generated.domain.{ref_cls};")
                domain_builder_steps.append(
                    f"            .{prop}(entity.{getter} == null ? null : {ref_cls}.builder().{target_pk_prop}(entity.{getter}.{target_get}).build())"
                )
            else:
                domain_builder_steps.append(f"            .{prop}(entity.{getter})")

        if obj.get("states"):
            enum_cls = f"{obj['name']}State"
            imports.add(f"import {base_package}.generated.domain.{enum_cls};")
            domain_builder_steps.append("            .currentState(entity.getCurrentState())")

        mapper_imports = {
            "import org.springframework.stereotype.Component;",
            f"import {base_package}.generated.domain.{domain_name};",
            f"import {base_package}.generated.persistence.{entity_name};",
        }
        mapper_imports = mapper_imports.union(ref_imports)
        mapper_src = (
            f"package {base_package}.generated.mapping;\n\n"
            + "\n".join(sorted(mapper_imports))
            + "\n\n"
            + "@Component\n"
            + f"public class {mapper_name} {{\n"
            + f"    public {domain_name} toDomain({entity_name} entity) {{\n"
            + "        if (entity == null) {\n"
            + "            return null;\n"
            + "        }\n"
            + f"        return {domain_name}.builder()\n"
            + "\n".join(domain_builder_steps)
            + "\n            .build();\n"
            + "    }\n"
            + "}\n"
        )
        files[f"src/main/java/{package_path}/generated/mapping/{mapper_name}.java"] = mapper_src

        list_method_params: List[str] = []
        filter_conditions: List[str] = []
        typed_filter_conditions: List[str] = []
        typed_query_fields: List[Tuple[str, str, bool]] = []
        typed_query_imports: set[str] = set()
        needs_join_type_import = False
        needs_date_time_format_import = False

        def base_type_for_descriptor(type_desc: Dict[str, Any]) -> Optional[str]:
            if type_desc["kind"] == "base":
                return str(type_desc["name"])
            if type_desc["kind"] == "custom":
                return str(type_by_id[type_desc["target_type_id"]]["base"])
            return None

        for f in fields:
            field_type = f["type"]
            kind = field_type["kind"]
            if kind in {"list", "struct"}:
                continue

            entity_prop = camel_case(f["name"])
            filter_record_name = f"{obj['name']}{pascal_case(entity_prop)}Filter"
            if kind == "object_ref":
                target = object_by_id[field_type["target_object_id"]]
                target_fields = target.get("fields", [])
                target_pk = next((x for x in target_fields if x.get("key") == "primary"), target_fields[0])
                target_pk_prop = camel_case(target_pk["name"])
                param_name = f"{entity_prop}{pascal_case(target_pk_prop)}"
                param_java = java_type_for_field(target_pk, type_by_id, object_by_id, struct_by_id)
                add_java_imports_for_type(param_java, imports)
                list_method_params.append(
                    f"        @RequestParam(name = \"{param_name}\", required = false) {param_java} {param_name}"
                )
                filter_conditions.extend(
                    [
                        f"        if ({param_name} != null) {{",
                        f"            spec = spec.and((root, query, cb) -> cb.equal(root.join(\"{entity_prop}\", JoinType.LEFT).get(\"{target_pk_prop}\"), {param_name}));",
                        "        }",
                    ]
                )
                needs_join_type_import = True

                filter_imports: set[str] = set()
                add_java_imports_for_type(param_java, filter_imports)
                filter_imports.add("import java.util.List;")
                filter_fields = [
                    (param_java, "eq", False),
                    (f"List<{param_java}>", "in", False),
                ]
                files[
                    f"src/main/java/{package_path}/generated/api/filters/{filter_record_name}.java"
                ] = render_java_record_with_builder(
                    f"{base_package}.generated.api.filters",
                    filter_imports,
                    filter_record_name,
                    filter_fields,
                )
                typed_query_fields.append((filter_record_name, entity_prop, False))
                typed_query_imports.add(f"import {base_package}.generated.api.filters.{filter_record_name};")
                typed_filter_conditions.extend(
                    [
                        f"            if (filter.{entity_prop}() != null) {{",
                        f"                {filter_record_name} {entity_prop}Filter = filter.{entity_prop}();",
                        f"                if ({entity_prop}Filter.eq() != null) {{",
                        f"                    spec = spec.and((root, query, cb) -> cb.equal(root.join(\"{entity_prop}\", JoinType.LEFT).get(\"{target_pk_prop}\"), {entity_prop}Filter.eq()));",
                        "                }",
                        f"                if ({entity_prop}Filter.in() != null && !{entity_prop}Filter.in().isEmpty()) {{",
                        f"                    spec = spec.and((root, query, cb) -> root.join(\"{entity_prop}\", JoinType.LEFT).get(\"{target_pk_prop}\").in({entity_prop}Filter.in()));",
                        "                }",
                        "            }",
                    ]
                )
                continue

            param_name = entity_prop
            param_java = java_type_for_field(f, type_by_id, object_by_id, struct_by_id)
            add_java_imports_for_type(param_java, imports)
            base_type = base_type_for_descriptor(field_type)
            annotation_suffix = ""
            if base_type == "date":
                annotation_suffix = " @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)"
                needs_date_time_format_import = True
            elif base_type == "datetime":
                annotation_suffix = " @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)"
                needs_date_time_format_import = True

            list_method_params.append(
                f"        @RequestParam(name = \"{param_name}\", required = false){annotation_suffix} {param_java} {param_name}"
            )
            filter_conditions.extend(
                [
                    f"        if ({param_name} != null) {{",
                    f"            spec = spec.and((root, query, cb) -> cb.equal(root.get(\"{entity_prop}\"), {param_name}));",
                    "        }",
                ]
            )

            filter_imports: set[str] = set()
            add_java_imports_for_type(param_java, filter_imports)
            filter_fields: List[Tuple[str, str, bool]] = [(param_java, "eq", False)]
            typed_condition_lines = [
                f"            if (filter.{entity_prop}() != null) {{",
                f"                {filter_record_name} {entity_prop}Filter = filter.{entity_prop}();",
                f"                if ({entity_prop}Filter.eq() != null) {{",
                f"                    spec = spec.and((root, query, cb) -> cb.equal(root.get(\"{entity_prop}\"), {entity_prop}Filter.eq()));",
                "                }",
            ]

            if base_type in {"string", "duration"}:
                filter_imports.add("import java.util.List;")
                filter_fields.append((f"List<{param_java}>", "in", False))
                filter_fields.append(("String", "contains", False))
                typed_condition_lines.extend(
                    [
                        f"                if ({entity_prop}Filter.in() != null && !{entity_prop}Filter.in().isEmpty()) {{",
                        f"                    spec = spec.and((root, query, cb) -> root.get(\"{entity_prop}\").in({entity_prop}Filter.in()));",
                        "                }",
                        f"                if ({entity_prop}Filter.contains() != null && !{entity_prop}Filter.contains().isBlank()) {{",
                        f"                    spec = spec.and((root, query, cb) -> cb.like(cb.lower(root.<String>get(\"{entity_prop}\")), \"%\" + {entity_prop}Filter.contains().toLowerCase() + \"%\"));",
                        "                }",
                    ]
                )
            elif base_type in {"int", "long", "short", "byte", "double", "float", "decimal", "date", "datetime"}:
                filter_imports.add("import java.util.List;")
                filter_fields.append((f"List<{param_java}>", "in", False))
                filter_fields.append((param_java, "gte", False))
                filter_fields.append((param_java, "lte", False))
                typed_condition_lines.extend(
                    [
                        f"                if ({entity_prop}Filter.in() != null && !{entity_prop}Filter.in().isEmpty()) {{",
                        f"                    spec = spec.and((root, query, cb) -> root.get(\"{entity_prop}\").in({entity_prop}Filter.in()));",
                        "                }",
                        f"                if ({entity_prop}Filter.gte() != null) {{",
                        f"                    spec = spec.and((root, query, cb) -> cb.greaterThanOrEqualTo(root.<{param_java}>get(\"{entity_prop}\"), {entity_prop}Filter.gte()));",
                        "                }",
                        f"                if ({entity_prop}Filter.lte() != null) {{",
                        f"                    spec = spec.and((root, query, cb) -> cb.lessThanOrEqualTo(root.<{param_java}>get(\"{entity_prop}\"), {entity_prop}Filter.lte()));",
                        "                }",
                    ]
                )
            elif base_type != "boolean":
                filter_imports.add("import java.util.List;")
                filter_fields.append((f"List<{param_java}>", "in", False))
                typed_condition_lines.extend(
                    [
                        f"                if ({entity_prop}Filter.in() != null && !{entity_prop}Filter.in().isEmpty()) {{",
                        f"                    spec = spec.and((root, query, cb) -> root.get(\"{entity_prop}\").in({entity_prop}Filter.in()));",
                        "                }",
                    ]
                )

            typed_condition_lines.extend(["            }"])
            files[
                f"src/main/java/{package_path}/generated/api/filters/{filter_record_name}.java"
            ] = render_java_record_with_builder(
                f"{base_package}.generated.api.filters",
                filter_imports,
                filter_record_name,
                filter_fields,
            )
            typed_query_fields.append((filter_record_name, entity_prop, False))
            typed_query_imports.add(f"import {base_package}.generated.api.filters.{filter_record_name};")
            typed_filter_conditions.extend(typed_condition_lines)

        if obj.get("states"):
            enum_cls = f"{obj['name']}State"
            list_method_params.append(
                f"        @RequestParam(name = \"currentState\", required = false) {enum_cls} currentState"
            )
            filter_conditions.extend(
                [
                    "        if (currentState != null) {",
                    "            spec = spec.and((root, query, cb) -> cb.equal(root.get(\"currentState\"), currentState));",
                    "        }",
                ]
            )
            state_filter_name = f"{obj['name']}CurrentStateFilter"
            files[
                f"src/main/java/{package_path}/generated/api/filters/{state_filter_name}.java"
            ] = render_java_record_with_builder(
                f"{base_package}.generated.api.filters",
                {
                    "import java.util.List;",
                    f"import {base_package}.generated.domain.{enum_cls};",
                },
                state_filter_name,
                [(enum_cls, "eq", False), (f"List<{enum_cls}>", "in", False)],
            )
            typed_query_fields.append((state_filter_name, "currentState", False))
            typed_query_imports.add(f"import {base_package}.generated.api.filters.{state_filter_name};")
            typed_filter_conditions.extend(
                [
                    "            if (filter.currentState() != null) {",
                    f"                {state_filter_name} currentStateFilter = filter.currentState();",
                    "                if (currentStateFilter.eq() != null) {",
                    "                    spec = spec.and((root, query, cb) -> cb.equal(root.get(\"currentState\"), currentStateFilter.eq()));",
                    "                }",
                    "                if (currentStateFilter.in() != null && !currentStateFilter.in().isEmpty()) {",
                    "                    spec = spec.and((root, query, cb) -> root.get(\"currentState\").in(currentStateFilter.in()));",
                    "                }",
                    "            }",
                ]
            )

        typed_query_name = f"{obj['name']}QueryFilter"
        files[
            f"src/main/java/{package_path}/generated/api/filters/{typed_query_name}.java"
        ] = render_java_record_with_builder(
            f"{base_package}.generated.api.filters",
            typed_query_imports,
            typed_query_name,
            typed_query_fields,
        )
        imports = imports.union(typed_query_imports)
        imports.add("import org.springframework.web.bind.annotation.PostMapping;")
        imports.add("import org.springframework.web.bind.annotation.RequestBody;")
        imports.add(f"import {base_package}.generated.api.filters.{typed_query_name};")

        list_method_params.append("        @PageableDefault(size = 20) Pageable pageable")
        list_method_signature = ",\n".join(list_method_params)
        filter_block = "\n".join(filter_conditions)

        if needs_join_type_import:
            imports.add("import jakarta.persistence.criteria.JoinType;")
        if needs_date_time_format_import:
            imports.add("import org.springframework.format.annotation.DateTimeFormat;")

        list_response_src = render_java_record_with_builder(
            f"{base_package}.generated.api",
            {
                "import java.util.List;",
                f"import {base_package}.generated.domain.{domain_name};",
            },
            list_response_name,
            [
                (f"List<{domain_name}>", "items", True),
                ("int", "page", True),
                ("int", "size", True),
                ("long", "totalElements", True),
                ("int", "totalPages", True),
            ],
        )
        files[f"src/main/java/{package_path}/generated/api/{list_response_name}.java"] = list_response_src

        typed_filter_block = "\n".join(typed_filter_conditions)
        typed_query_method = (
            "    @PostMapping(\"/query\")\n"
            f"    public ResponseEntity<{list_response_name}> query(\n"
            f"        @RequestBody(required = false) {typed_query_name} filter,\n"
            "        @PageableDefault(size = 20) Pageable pageable\n"
            "    ) {\n"
            f"        Specification<{entity_name}> spec = (root, query, cb) -> cb.conjunction();\n"
            "        if (filter != null) {\n"
            + (typed_filter_block + "\n" if typed_filter_block else "")
            + "        }\n"
            + f"        Page<{entity_name}> entityPage = repository.findAll(spec, pageable);\n"
            + f"        List<{domain_name}> items = entityPage.stream().map(mapper::toDomain).toList();\n"
            + f"        {list_response_name} result = {list_response_name}.builder()\n"
            + "            .items(items)\n"
            + "            .page(entityPage.getNumber())\n"
            + "            .size(entityPage.getSize())\n"
            + "            .totalElements(entityPage.getTotalElements())\n"
            + "            .totalPages(entityPage.getTotalPages())\n"
            + "            .build();\n"
            + "        return ResponseEntity.ok(result);\n"
            + "    }\n\n"
        )

        imports_block = "\n".join(sorted(imports))
        query_src = (
            f"package {base_package}.generated.api;\n\n"
            f"{imports_block}\n\n"
            "@RestController\n"
            f"@RequestMapping(\"/{path_table}\")\n"
            f"public class {obj['name']}QueryController {{\n\n"
            f"    private final {repo_name} repository;\n"
            f"    private final {mapper_name} mapper;\n\n"
            f"    public {obj['name']}QueryController({repo_name} repository, {mapper_name} mapper) {{\n"
            "        this.repository = repository;\n"
            "        this.mapper = mapper;\n"
            "    }\n\n"
            "    @GetMapping\n"
            f"    public ResponseEntity<{list_response_name}> list(\n"
            f"{list_method_signature}\n"
            "    ) {\n"
            f"        Specification<{entity_name}> spec = (root, query, cb) -> cb.conjunction();\n"
            + (filter_block + "\n" if filter_block else "")
            + f"        Page<{entity_name}> entityPage = repository.findAll(spec, pageable);\n"
            + f"        List<{domain_name}> items = entityPage.stream().map(mapper::toDomain).toList();\n"
            + f"        {list_response_name} result = {list_response_name}.builder()\n"
            + "            .items(items)\n"
            + "            .page(entityPage.getNumber())\n"
            + "            .size(entityPage.getSize())\n"
            + "            .totalElements(entityPage.getTotalElements())\n"
            + "            .totalPages(entityPage.getTotalPages())\n"
            + "            .build();\n"
            + "        return ResponseEntity.ok(result);\n"
            + "    }\n\n"
            + typed_query_method
            + f"    @GetMapping(\"/{{{pk_prop}}}\")\n"
            f"    public ResponseEntity<{domain_name}> getById(@PathVariable(\"{pk_prop}\") {pk_java} {pk_prop}) {{\n"
            f"        Optional<{entity_name}> maybeEntity = repository.findById({pk_prop});\n"
            "        if (maybeEntity.isEmpty()) {\n"
            "            return ResponseEntity.notFound().build();\n"
            "        }\n\n"
            f"        {domain_name} domain = mapper.toDomain(maybeEntity.get());\n"
            "        return ResponseEntity.ok(domain);\n"
            "    }\n"
            + "}\n"
        )

        files[f"src/main/java/{package_path}/generated/api/{obj['name']}QueryController.java"] = query_src

    annotate_generated_java_files(files)
    return files

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


def _generate_outputs_for_java_spring_jpa(context: GenerationContext) -> Dict[str, str]:
    deps = JavaSpringJpaDeps(
        cfg_get=cfg_get,
        resolve_stack_spec=resolve_stack_spec,
        render_sql=render_sql,
        compute_delta_from_baseline=compute_delta_from_baseline,
        render_liquibase_root_changelog=render_liquibase_root_changelog,
        render_liquibase_prophet_changelog=render_liquibase_prophet_changelog,
        render_openapi=render_openapi,
        render_spring_files=lambda ir, cfg, root, schema_sql, delta_sql: render_spring_files(
            ir,
            cfg,
            root=root,
            generated_schema_sql=schema_sql,
            delta_schema_sql=delta_sql,
        ),
        toolchain_version=TOOLCHAIN_VERSION,
    )
    return generate_java_spring_jpa_outputs(context, deps)


def build_generated_outputs(ir: Dict[str, Any], cfg: Dict[str, Any], root: Optional[Path] = None) -> Dict[str, str]:
    stack = resolve_stack_spec(cfg)
    work_root = root if root is not None else Path.cwd()
    ir_reader = IRReader.from_dict(ir)
    context = GenerationContext(
        stack_id=stack.id,
        ir=ir,
        ir_reader=ir_reader,
        cfg=cfg,
        root=work_root,
    )
    return run_generation_pipeline(
        context,
        generators={
            "java_spring_jpa": _generate_outputs_for_java_spring_jpa,
        },
    )


def write_outputs(outputs: Dict[str, str], root: Path) -> None:
    _write_outputs(outputs, root)


def remove_stale_outputs(root: Path, cfg: Dict[str, Any], outputs: Dict[str, str]) -> None:
    out_dir = str(cfg_get(cfg, ["generation", "out_dir"], "gen"))
    _remove_stale_outputs(root, out_dir, outputs)


def managed_existing_files(root: Path, cfg: Dict[str, Any]) -> List[str]:
    out_dir = str(cfg_get(cfg, ["generation", "out_dir"], "gen"))
    return _managed_existing_files(root, out_dir)


def sync_example_project(root: Path, cfg: Dict[str, Any]) -> None:
    out_dir = cfg_get(cfg, ["generation", "out_dir"], "gen")
    example = root / "examples" / "java" / "prophet_example_spring"
    if not example.exists():
        return

    build_gradle = example / "build.gradle.kts"
    if not build_gradle.exists():
        return

    spring_src = root / out_dir / "spring-boot" / "src" / "main" / "java" / "com" / "example" / "prophet" / "generated"
    spring_res = root / out_dir / "spring-boot" / "src" / "main" / "resources" / "application-prophet.yml"
    spring_flyway_src = root / out_dir / "spring-boot" / "src" / "main" / "resources" / "db" / "migration" / "V1__prophet_init.sql"
    spring_flyway_delta_src = (
        root / out_dir / "spring-boot" / "src" / "main" / "resources" / "db" / "migration" / "V2__prophet_delta.sql"
    )
    spring_liquibase_root_src = (
        root
        / out_dir
        / "spring-boot"
        / "src"
        / "main"
        / "resources"
        / "db"
        / "changelog"
        / "db.changelog-master.yaml"
    )
    spring_liquibase_prophet_changelog_src = (
        root
        / out_dir
        / "spring-boot"
        / "src"
        / "main"
        / "resources"
        / "db"
        / "changelog"
        / "prophet"
        / "changelog-master.yaml"
    )
    spring_liquibase_sql_src = (
        root
        / out_dir
        / "spring-boot"
        / "src"
        / "main"
        / "resources"
        / "db"
        / "changelog"
        / "prophet"
        / "0001-init.sql"
    )
    spring_liquibase_delta_sql_src = (
        root
        / out_dir
        / "spring-boot"
        / "src"
        / "main"
        / "resources"
        / "db"
        / "changelog"
        / "prophet"
        / "0002-delta.sql"
    )
    schema_src = root / out_dir / "sql" / "schema.sql"
    flyway_dst_file = example / "src" / "main" / "resources" / "db" / "migration" / "V1__prophet_init.sql"
    flyway_delta_dst_file = example / "src" / "main" / "resources" / "db" / "migration" / "V2__prophet_delta.sql"
    liquibase_root_dst_file = example / "src" / "main" / "resources" / "db" / "changelog" / "db.changelog-master.yaml"
    liquibase_prophet_changelog_dst_file = (
        example / "src" / "main" / "resources" / "db" / "changelog" / "prophet" / "changelog-master.yaml"
    )
    liquibase_prophet_sql_dst_file = (
        example / "src" / "main" / "resources" / "db" / "changelog" / "prophet" / "0001-init.sql"
    )
    liquibase_prophet_delta_sql_dst_file = (
        example / "src" / "main" / "resources" / "db" / "changelog" / "prophet" / "0002-delta.sql"
    )

    if spring_src.exists():
        dst = example / "src" / "main" / "java" / "com" / "example" / "prophet" / "generated"
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(spring_src, dst)

    if spring_res.exists():
        (example / "src" / "main" / "resources").mkdir(parents=True, exist_ok=True)
        shutil.copy2(spring_res, example / "src" / "main" / "resources" / "application-prophet.yml")

    if schema_src.exists():
        (example / "src" / "main" / "resources").mkdir(parents=True, exist_ok=True)
        shutil.copy2(schema_src, example / "src" / "main" / "resources" / "schema.sql")

    if spring_flyway_src.exists():
        flyway_dst = example / "src" / "main" / "resources" / "db" / "migration"
        flyway_dst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(spring_flyway_src, flyway_dst / "V1__prophet_init.sql")
    elif flyway_dst_file.exists():
        flyway_dst_file.unlink()
    if spring_flyway_delta_src.exists():
        flyway_dst = example / "src" / "main" / "resources" / "db" / "migration"
        flyway_dst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(spring_flyway_delta_src, flyway_dst / "V2__prophet_delta.sql")
    elif flyway_delta_dst_file.exists():
        flyway_delta_dst_file.unlink()

    if spring_liquibase_root_src.exists():
        liquibase_dst = example / "src" / "main" / "resources" / "db" / "changelog"
        liquibase_dst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(spring_liquibase_root_src, liquibase_dst / "db.changelog-master.yaml")
    elif liquibase_root_dst_file.exists():
        liquibase_root_dst_file.unlink()

    if spring_liquibase_prophet_changelog_src.exists():
        liquibase_prophet_dst = example / "src" / "main" / "resources" / "db" / "changelog" / "prophet"
        liquibase_prophet_dst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(spring_liquibase_prophet_changelog_src, liquibase_prophet_dst / "changelog-master.yaml")
    elif liquibase_prophet_changelog_dst_file.exists():
        liquibase_prophet_changelog_dst_file.unlink()

    if spring_liquibase_sql_src.exists():
        liquibase_prophet_dst = example / "src" / "main" / "resources" / "db" / "changelog" / "prophet"
        liquibase_prophet_dst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(spring_liquibase_sql_src, liquibase_prophet_dst / "0001-init.sql")
    elif liquibase_prophet_sql_dst_file.exists():
        liquibase_prophet_sql_dst_file.unlink()
    if spring_liquibase_delta_sql_src.exists():
        liquibase_prophet_dst = example / "src" / "main" / "resources" / "db" / "changelog" / "prophet"
        liquibase_prophet_dst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(spring_liquibase_delta_sql_src, liquibase_prophet_dst / "0002-delta.sql")
    elif liquibase_prophet_delta_sql_dst_file.exists():
        liquibase_prophet_delta_sql_dst_file.unlink()

    maybe_empty = [
        example / "src" / "main" / "resources" / "db" / "changelog" / "prophet",
        example / "src" / "main" / "resources" / "db" / "changelog",
        example / "src" / "main" / "resources" / "db" / "migration",
        example / "src" / "main" / "resources" / "db",
    ]
    for d in maybe_empty:
        if d.exists() and d.is_dir() and not any(d.iterdir()):
            d.rmdir()


def _find_block_close(text: str, open_brace_index: int) -> int:
    depth = 0
    for i in range(open_brace_index, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _inject_dependency(content: str, dep_line: str) -> Tuple[str, bool]:
    if dep_line in content:
        return content, False

    m = re.search(r"dependencies\s*\{", content)
    if m:
        open_idx = content.find("{", m.start())
        close_idx = _find_block_close(content, open_idx)
        if close_idx != -1:
            insertion = f"    {dep_line}\n"
            new_content = content[:close_idx] + insertion + content[close_idx:]
            return new_content, True

    block = f"\n\ndependencies {{\n    {dep_line}\n}}\n"
    return content.rstrip() + block, True


def wire_gradle_multi_module(root: Path, cfg: Dict[str, Any]) -> List[str]:
    out_dir = cfg_get(cfg, ["generation", "out_dir"], "gen")
    module_name = "prophet_generated"
    module_dir = f"{out_dir}/spring-boot"

    messages: List[str] = []

    settings_kts = root / "settings.gradle.kts"
    settings_groovy = root / "settings.gradle"
    settings_path: Optional[Path] = settings_kts if settings_kts.exists() else settings_groovy if settings_groovy.exists() else None

    if settings_path is None:
        messages.append("Skipped Gradle wiring: settings.gradle(.kts) not found in current directory.")
        return messages

    settings_content = settings_path.read_text(encoding="utf-8")
    if module_name in settings_content:
        messages.append(f"No changes in {settings_path.name}: :{module_name} already configured.")
    else:
        if settings_path.suffix == ".kts":
            snippet = (
                f"\ninclude(\":{module_name}\")\n"
                f"project(\":{module_name}\").projectDir = file(\"{module_dir}\")\n"
            )
        else:
            snippet = (
                f"\ninclude ':{module_name}'\n"
                f"project(':{module_name}').projectDir = file('{module_dir}')\n"
            )
        settings_path.write_text(settings_content.rstrip() + snippet, encoding="utf-8")
        messages.append(f"Updated {settings_path.name}: added :{module_name} module mapping to {module_dir}.")

    build_kts = root / "build.gradle.kts"
    build_groovy = root / "build.gradle"
    build_path: Optional[Path] = build_kts if build_kts.exists() else build_groovy if build_groovy.exists() else None

    if build_path is None:
        messages.append("Skipped app dependency wiring: build.gradle(.kts) not found in current directory.")
        return messages

    build_content = build_path.read_text(encoding="utf-8")
    dep_line = 'implementation(project(":prophet_generated"))' if build_path.suffix == ".kts" else "implementation project(':prophet_generated')"
    new_content, changed = _inject_dependency(build_content, dep_line)
    if changed:
        build_path.write_text(new_content, encoding="utf-8")
        messages.append(f"Updated {build_path.name}: added dependency on :{module_name}.")
    else:
        messages.append(f"No changes in {build_path.name}: dependency on :{module_name} already present.")

    return messages


def _remove_matching_lines(content: str, patterns: List[re.Pattern[str]]) -> Tuple[str, bool]:
    changed = False
    out_lines: List[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if any(p.match(stripped) for p in patterns):
            changed = True
            continue
        out_lines.append(line)
    new_content = "\n".join(out_lines)
    if content.endswith("\n"):
        new_content += "\n"
    return new_content, changed


def _remove_dependency(content: str, dep_patterns: List[re.Pattern[str]]) -> Tuple[str, bool]:
    return _remove_matching_lines(content, dep_patterns)


def unwire_gradle_multi_module(root: Path, cfg: Dict[str, Any]) -> List[str]:
    out_dir = cfg_get(cfg, ["generation", "out_dir"], "gen")
    module_name = "prophet_generated"
    module_dir = f"{out_dir}/spring-boot"
    messages: List[str] = []

    settings_kts = root / "settings.gradle.kts"
    settings_groovy = root / "settings.gradle"
    settings_path: Optional[Path] = settings_kts if settings_kts.exists() else settings_groovy if settings_groovy.exists() else None

    if settings_path is None:
        messages.append("Skipped Gradle unwiring: settings.gradle(.kts) not found in current directory.")
    else:
        settings_content = settings_path.read_text(encoding="utf-8")
        settings_patterns = [
            re.compile(rf'^include\(\s*":{module_name}"\s*\)$'),
            re.compile(rf'^project\(\s*":{module_name}"\s*\)\.projectDir\s*=\s*file\(\s*"{re.escape(module_dir)}"\s*\)$'),
            re.compile(rf"^include\s+':{module_name}'$"),
            re.compile(rf"^project\(\s*':{module_name}'\s*\)\.projectDir\s*=\s*file\(\s*'{re.escape(module_dir)}'\s*\)$"),
        ]
        new_settings, changed = _remove_matching_lines(settings_content, settings_patterns)
        if changed:
            settings_path.write_text(new_settings, encoding="utf-8")
            messages.append(f"Updated {settings_path.name}: removed :{module_name} module mapping.")
        else:
            messages.append(f"No changes in {settings_path.name}: :{module_name} mapping not present.")

    build_kts = root / "build.gradle.kts"
    build_groovy = root / "build.gradle"
    build_path: Optional[Path] = build_kts if build_kts.exists() else build_groovy if build_groovy.exists() else None

    if build_path is None:
        messages.append("Skipped app dependency unwiring: build.gradle(.kts) not found in current directory.")
    else:
        build_content = build_path.read_text(encoding="utf-8")
        dep_patterns = [
            re.compile(r'^implementation\(\s*project\(\s*":prophet_generated"\s*\)\s*\)$'),
            re.compile(r'^api\(\s*project\(\s*":prophet_generated"\s*\)\s*\)$'),
            re.compile(r"^implementation\s+project\(\s*':prophet_generated'\s*\)$"),
            re.compile(r"^api\s+project\(\s*':prophet_generated'\s*\)$"),
        ]
        new_build, changed = _remove_dependency(build_content, dep_patterns)
        if changed:
            build_path.write_text(new_build, encoding="utf-8")
            messages.append(f"Updated {build_path.name}: removed dependency on :{module_name}.")
        else:
            messages.append(f"No changes in {build_path.name}: dependency on :{module_name} not present.")

    return messages


def ontology_path_from_cfg(root: Path, cfg: Dict[str, Any]) -> Path:
    ontology_file = cfg_get(cfg, ["project", "ontology_file"], None)
    if not ontology_file:
        raise ProphetError(
            "Missing required config: project.ontology_file in prophet.yaml "
            "(see examples/java/prophet_example_spring/ontology/local/main.prophet for an example)."
        )
    return root / str(ontology_file)


def load_ontology_from_cfg(root: Path, cfg: Dict[str, Any]) -> Ontology:
    ont_path = ontology_path_from_cfg(root, cfg)
    if not ont_path.exists():
        raise ProphetError(f"Ontology file not found: {ont_path}")
    return parse_ontology(ont_path.read_text(encoding="utf-8"))


def print_validation_failure(errors: List[str], ontology_path: Path) -> None:
    print(f"Validation failed for {ontology_path} ({len(errors)} errors):")
    for idx, err in enumerate(errors, start=1):
        print(f"{idx}) {err}")
    print("")
    print("How to fix:")
    print("- Correct the ontology DSL lines listed above.")
    print("- Re-run: prophet validate")


def collect_dirty_generated_files(root: Path, cfg: Dict[str, Any], outputs: Dict[str, str]) -> List[str]:
    dirty: List[str] = []
    existing = set(managed_existing_files(root, cfg))
    new_files = set(outputs.keys())

    for rel in sorted(new_files):
        path = root / rel
        if not path.exists() or path.read_text(encoding="utf-8") != outputs[rel]:
            dirty.append(rel)

    for rel in sorted(existing - new_files):
        dirty.append(rel)
    return dirty


def print_dirty_generated_files(dirty: List[str]) -> None:
    print("Generated outputs are not clean:")
    for rel in dirty:
        print(f"- {rel}")
    print("")
    print("How to fix:")
    print("- Re-run generation: prophet gen")
    print("- Commit regenerated files if expected.")


def hints_for_prophet_error(message: str) -> List[str]:
    msg = message.lower()
    hints: List[str] = []
    if "prophet.yaml not found" in msg:
        hints.append("Run `prophet init` in your project root, then set `project.ontology_file`.")
    if "missing required config: project.ontology_file" in msg:
        hints.append("Set `project.ontology_file` in prophet.yaml to your ontology DSL path.")
    if "ontology file not found" in msg:
        hints.append("Verify `project.ontology_file` points to an existing file relative to your current directory.")
    if "baseline ir not found" in msg:
        hints.append("Run `prophet gen` once to create a baseline, or set `compatibility.baseline_ir`.")
    if "--wire-gradle cannot be used with --verify-clean" in msg:
        hints.append("Use `prophet gen --wire-gradle` and `prophet check` (or `prophet generate --verify-clean`) as separate steps.")
    if "--skip-unchanged cannot be used with --verify-clean" in msg:
        hints.append("Use `prophet gen --skip-unchanged` for local no-op speedups, and `prophet check` or `prophet generate --verify-clean` in CI.")
    if "invalid semver" in msg:
        hints.append("Use semantic versions in ontology `version`, for example `1.2.3`.")
    return hints


def generation_cache_path(root: Path) -> Path:
    return root / ".prophet" / "cache" / "generation.json"


def compute_generation_signature(cfg: Dict[str, Any], ir: Dict[str, Any], stack_id: str) -> str:
    payload = {
        "toolchain_version": TOOLCHAIN_VERSION,
        "stack_id": stack_id,
        "ir_hash": str(ir.get("ir_hash", "")),
        "out_dir": str(cfg_get(cfg, ["generation", "out_dir"], "gen")),
        "targets": list(cfg_get(cfg, ["generation", "targets"], ["sql", "openapi", "spring_boot", "flyway", "liquibase"])),
        "baseline_ir": str(cfg_get(cfg, ["compatibility", "baseline_ir"], ".prophet/baselines/main.ir.json")),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def load_generation_cache(root: Path) -> Dict[str, Any]:
    path = generation_cache_path(root)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        return {}
    return {}


def write_generation_cache(root: Path, payload: Dict[str, Any]) -> None:
    path = generation_cache_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def ensure_baseline_exists(root: Path, cfg: Dict[str, Any], ir: Dict[str, Any]) -> Path:
    baseline_rel = str(cfg_get(cfg, ["compatibility", "baseline_ir"], ".prophet/baselines/main.ir.json"))
    baseline = root / baseline_rel
    if not baseline.exists():
        baseline.parent.mkdir(parents=True, exist_ok=True)
        baseline.write_text(json.dumps(ir, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return baseline


def declared_bump(old_ver: str, new_ver: str) -> str:
    return _core_declared_bump(old_ver, new_ver)


def cmd_init(args: argparse.Namespace) -> int:
    root = Path.cwd()
    cfg_path = root / "prophet.yaml"
    if cfg_path.exists() and not args.force:
        raise ProphetError("prophet.yaml already exists (use --force to overwrite)")

    cfg_path.write_text(
        """schema_version: 1
project:
  name: my-ontology
  ontology_file: path/to/your-ontology.prophet
  version_source: ontology
generation:
  stack:
    id: java_spring_jpa
  targets:
    - sql
    - openapi
    - spring_boot
    - flyway
    - liquibase
  out_dir: gen
  spring_boot:
    base_package: com.example.prophet
    java_version: 21
    boot_version: 3.3
compatibility:
  baseline_ir: .prophet/baselines/main.ir.json
  strict_enums: false
determinism:
  canonical_sort: true
  include_timestamps: false
""",
        encoding="utf-8",
    )

    # Create internal Prophet state directories.
    (root / ".prophet" / "ir").mkdir(parents=True, exist_ok=True)
    (root / ".prophet" / "baselines").mkdir(parents=True, exist_ok=True)

    print("Initialized Prophet project.")
    print("Created:")
    print("- prophet.yaml")
    print("- .prophet/ir")
    print("- .prophet/baselines")
    print("")
    print("Next:")
    print("- set project.ontology_file to your ontology file path")
    print("- author your ontology file, or start from:")
    print("  examples/java/prophet_example_spring/ontology/local/main.prophet")
    print("")
    print("Note: gen/ is created on first 'prophet gen' or 'prophet generate'.")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    root = Path.cwd()
    cfg = load_config(root / "prophet.yaml")
    resolve_stack_spec(cfg)
    ontology_path = ontology_path_from_cfg(root, cfg)
    ont = load_ontology_from_cfg(root, cfg)
    strict_enums = bool(cfg_get(cfg, ["compatibility", "strict_enums"], False))
    errors = validate_ontology(ont, strict_enums=strict_enums)
    if errors:
        print_validation_failure(errors, ontology_path)
        return 1
    print("Validation passed.")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    root = Path.cwd()
    cfg = load_config(root / "prophet.yaml")
    stack = resolve_stack_spec(cfg)
    ontology_path = ontology_path_from_cfg(root, cfg)
    ont = load_ontology_from_cfg(root, cfg)
    strict_enums = bool(cfg_get(cfg, ["compatibility", "strict_enums"], False))
    errors = validate_ontology(ont, strict_enums=strict_enums)
    if errors:
        print_validation_failure(errors, ontology_path)
        return 1

    ir = build_ir(ont, cfg)
    delta_sql, delta_warnings, baseline_path, _, _ = compute_delta_from_baseline(root, cfg, ir)
    outputs = build_generated_outputs(ir, cfg, root=root)

    existing = set(managed_existing_files(root, cfg))
    new_files = set(outputs.keys())

    changes: List[Tuple[str, str]] = []

    for rel in sorted(new_files):
        path = root / rel
        if not path.exists():
            changes.append((rel, "added"))
        else:
            existing_content = path.read_text(encoding="utf-8")
            if existing_content != outputs[rel]:
                changes.append((rel, "modified"))

    for rel in sorted(existing - new_files):
        changes.append((rel, "deleted"))

    baseline_path = root / str(cfg_get(cfg, ["compatibility", "baseline_ir"], ".prophet/baselines/main.ir.json"))
    compatibility = "non_functional"
    required_bump = "patch"
    reasons: List[str] = []
    if baseline_path.exists():
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        compatibility, reasons = compare_irs(baseline, ir)
        required_bump = required_level_to_bump(compatibility)

    change_items = []
    for rel, status in changes:
        if rel.endswith("schema.sql"):
            reason = "SQL schema generated from object models and transitions"
        elif "/migrations/flyway/" in rel:
            reason = "Flyway migration generated from canonical SQL schema"
        elif "/migrations/liquibase/" in rel:
            reason = "Liquibase changelog generated from canonical SQL schema"
        elif rel.endswith("openapi.yaml"):
            reason = "OpenAPI generated from object/action contracts"
        elif "/spring-boot/" in rel:
            reason = "Spring Boot artifact generated from canonical IR"
        else:
            reason = "generated artifact changed"
        change_items.append({"path": rel, "status": status, "reason": reason})

    if args.json:
        payload = {
            "stack": {
                "id": stack.id,
                "language": stack.language,
                "framework": stack.framework,
                "orm": stack.orm,
                "capabilities": sorted(stack.capabilities),
            },
            "changes": change_items,
            "summary": {
                "change_count": len(change_items),
                "compatibility": compatibility,
                "required_bump": required_bump,
                "policy_reference": COMPATIBILITY_POLICY_DOC,
            },
            "compatibility_reasons": reasons if args.show_reasons else [],
        }
        print(json.dumps(payload, indent=2, sort_keys=False))
        return 0

    print(f"Plan: {len(changes)} changes")
    print(f"Stack: {stack.id} ({stack.language}/{stack.framework}/{stack.orm})")
    for idx, item in enumerate(change_items, start=1):
        print(f"{idx}) {item['path']} ({item['status']})")
        print(f"   reason: {item['reason']}")

    print("")
    print(f"Compatibility: {compatibility}")
    print(f"Required version bump: {required_bump}")
    print(f"Policy reference: {COMPATIBILITY_POLICY_DOC}")

    if reasons and args.show_reasons:
        print("")
        print("Detected compatibility changes:")
        for item in reasons:
            print(f"- {item}")

    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    root = Path.cwd()
    cfg = load_config(root / "prophet.yaml")
    stack = resolve_stack_spec(cfg)
    ontology_path = ontology_path_from_cfg(root, cfg)
    ont = load_ontology_from_cfg(root, cfg)
    strict_enums = bool(cfg_get(cfg, ["compatibility", "strict_enums"], False))
    errors = validate_ontology(ont, strict_enums=strict_enums)
    if errors:
        print_validation_failure(errors, ontology_path)
        return 1

    ir = build_ir(ont, cfg)

    if args.verify_clean and args.wire_gradle:
        raise ProphetError("--wire-gradle cannot be used with --verify-clean")
    if args.verify_clean and args.skip_unchanged:
        raise ProphetError("--skip-unchanged cannot be used with --verify-clean")

    signature = compute_generation_signature(cfg, ir, stack.id)
    out_dir = str(cfg_get(cfg, ["generation", "out_dir"], "gen"))
    manifest_path = root / out_dir / "manifest" / "generated-files.json"
    cache_payload = load_generation_cache(root)
    cached_signature = str(cache_payload.get("signature", "")) if isinstance(cache_payload, dict) else ""
    if args.skip_unchanged and not args.wire_gradle:
        if cached_signature == signature and manifest_path.exists():
            print("Skipped generation: configuration and IR unchanged.")
            print(f"- stack: {stack.id} ({stack.language}/{stack.framework}/{stack.orm})")
            print(f"- signature: {signature}")
            return 0

    delta_sql, delta_warnings, baseline_path, _, _ = compute_delta_from_baseline(root, cfg, ir)
    outputs = build_generated_outputs(ir, cfg, root=root)

    if args.verify_clean:
        dirty = collect_dirty_generated_files(root, cfg, outputs)
        if dirty:
            print_dirty_generated_files(dirty)
            return 1

        print("Generated outputs are clean.")
        return 0

    remove_stale_outputs(root, cfg, outputs)
    write_outputs(outputs, root)

    ir_path = root / ".prophet" / "ir" / "current.ir.json"
    ir_path.parent.mkdir(parents=True, exist_ok=True)
    ir_path.write_text(json.dumps(ir, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    ensure_baseline_exists(root, cfg, ir)

    sync_example_project(root, cfg)

    gradle_messages: List[str] = []
    requested_migrations, detected_migrations, enabled_migrations, migration_warnings = resolve_migration_runtime_modes(
        cfg, root
    )
    if args.wire_gradle:
        gradle_messages = wire_gradle_multi_module(root, cfg)

    print("Generated artifacts:")
    print(f"- stack: {stack.id} ({stack.language}/{stack.framework}/{stack.orm})")
    for rel in sorted(outputs.keys()):
        print(f"- {rel}")
    print("- .prophet/ir/current.ir.json")
    print("- examples/java/prophet_example_spring (synced if present)")
    print("")
    print("Migration auto-detection:")
    requested_label = ", ".join(sorted(requested_migrations)) if requested_migrations else "none"
    detected_label = ", ".join(sorted(detected_migrations)) if detected_migrations else "none"
    enabled_label = ", ".join(sorted(enabled_migrations)) if enabled_migrations else "none"
    print(f"- requested targets: {requested_label}")
    print(f"- detected in host Gradle: {detected_label}")
    print(f"- Spring runtime wiring enabled: {enabled_label}")
    if migration_warnings:
        print("- warnings:")
        for warning in migration_warnings:
            print(f"  - {warning}")
    if delta_sql:
        print("")
        print("Delta migration:")
        if baseline_path is not None:
            print(f"- baseline: {baseline_path}")
        print("- generated: yes (V2__prophet_delta.sql / 0002-delta.sql)")
        if delta_warnings:
            print("- safety warnings:")
            for warning in delta_warnings:
                print(f"  - {warning}")
    if gradle_messages:
        print("")
        print("Gradle wiring:")
        for msg in gradle_messages:
            print(f"- {msg}")

    write_generation_cache(
        root,
        {
            "schema_version": 1,
            "toolchain_version": TOOLCHAIN_VERSION,
            "stack_id": stack.id,
            "signature": signature,
            "ir_hash": ir.get("ir_hash"),
            "out_dir": out_dir,
        },
    )

    return 0


def cmd_clean(args: argparse.Namespace) -> int:
    root = Path.cwd()
    cfg_path = root / "prophet.yaml"
    if not cfg_path.exists():
        raise ProphetError("prophet.yaml not found in current directory")

    cfg = load_config(cfg_path)
    out_dir = root / str(cfg_get(cfg, ["generation", "out_dir"], "gen"))
    baseline_rel = str(cfg_get(cfg, ["compatibility", "baseline_ir"], ".prophet/baselines/main.ir.json"))
    baseline_path = root / baseline_rel
    current_ir_path = root / ".prophet" / "ir" / "current.ir.json"
    generation_cache = generation_cache_path(root)

    removed: List[str] = []
    skipped: List[str] = []
    gradle_messages: List[str] = []
    generated_markers = ("-- GENERATED FILE: do not edit directly.", "# GENERATED FILE: do not edit directly.")

    def remove_if_generated(path: Path, allow_force: bool = False) -> None:
        if not path.exists():
            skipped.append(str(path.relative_to(root)))
            return
        text = path.read_text(encoding="utf-8")
        if allow_force and args.force_schema:
            path.unlink()
            removed.append(str(path.relative_to(root)))
            return
        if text.startswith(generated_markers):
            path.unlink()
            removed.append(str(path.relative_to(root)))
            return
        msg = f"{path.relative_to(root)} (not removed: does not look generated"
        if allow_force:
            msg += "; use --force-schema"
        msg += ")"
        skipped.append(msg)

    if out_dir.exists():
        shutil.rmtree(out_dir)
        removed.append(str(out_dir.relative_to(root)))
    else:
        skipped.append(str(out_dir.relative_to(root)))

    if current_ir_path.exists():
        current_ir_path.unlink()
        removed.append(str(current_ir_path.relative_to(root)))
    else:
        skipped.append(str(current_ir_path.relative_to(root)))

    if generation_cache.exists():
        generation_cache.unlink()
        removed.append(str(generation_cache.relative_to(root)))
    else:
        skipped.append(str(generation_cache.relative_to(root)))

    if args.remove_baseline:
        if baseline_path.exists():
            baseline_path.unlink()
            removed.append(str(baseline_path.relative_to(root)))
        else:
            skipped.append(str(baseline_path.relative_to(root)))

    base_package = str(cfg_get(cfg, ["generation", "spring_boot", "base_package"], "com.example.prophet"))
    generated_java_dir = root / "src" / "main" / "java" / Path(base_package.replace(".", "/")) / "generated"
    if generated_java_dir.exists():
        shutil.rmtree(generated_java_dir)
        removed.append(str(generated_java_dir.relative_to(root)))
    else:
        skipped.append(str(generated_java_dir.relative_to(root)))

    app_prophet_path = root / "src" / "main" / "resources" / "application-prophet.yml"
    if app_prophet_path.exists():
        app_prophet_path.unlink()
        removed.append(str(app_prophet_path.relative_to(root)))
    else:
        skipped.append(str(app_prophet_path.relative_to(root)))

    schema_path = root / "src" / "main" / "resources" / "schema.sql"
    remove_if_generated(schema_path, allow_force=True)

    flyway_sql = root / "src" / "main" / "resources" / "db" / "migration" / "V1__prophet_init.sql"
    flyway_delta_sql = root / "src" / "main" / "resources" / "db" / "migration" / "V2__prophet_delta.sql"
    liquibase_root = root / "src" / "main" / "resources" / "db" / "changelog" / "db.changelog-master.yaml"
    liquibase_prophet_master = root / "src" / "main" / "resources" / "db" / "changelog" / "prophet" / "changelog-master.yaml"
    liquibase_prophet_sql = root / "src" / "main" / "resources" / "db" / "changelog" / "prophet" / "0001-init.sql"
    liquibase_prophet_delta_sql = root / "src" / "main" / "resources" / "db" / "changelog" / "prophet" / "0002-delta.sql"
    for p in [
        flyway_sql,
        flyway_delta_sql,
        liquibase_root,
        liquibase_prophet_master,
        liquibase_prophet_sql,
        liquibase_prophet_delta_sql,
    ]:
        remove_if_generated(p, allow_force=False)

    maybe_empty_dirs = [
        root / "src" / "main" / "resources" / "db" / "migration",
        root / "src" / "main" / "resources" / "db" / "changelog" / "prophet",
        root / "src" / "main" / "resources" / "db" / "changelog",
        root / "src" / "main" / "resources" / "db",
    ]
    for d in maybe_empty_dirs:
        if d.exists() and d.is_dir() and not any(d.iterdir()):
            d.rmdir()
            removed.append(str(d.relative_to(root)))

    ir_dir = root / ".prophet" / "ir"
    if ir_dir.exists() and not any(ir_dir.iterdir()):
        ir_dir.rmdir()
        removed.append(str(ir_dir.relative_to(root)))

    cache_dir = root / ".prophet" / "cache"
    if cache_dir.exists() and not any(cache_dir.iterdir()):
        cache_dir.rmdir()
        removed.append(str(cache_dir.relative_to(root)))

    if not args.keep_gradle_wire:
        gradle_messages = unwire_gradle_multi_module(root, cfg)

    if removed:
        print("Removed generated artifacts:")
        for item in removed:
            print(f"- {item}")
    else:
        print("No generated artifacts removed.")

    if skipped and args.verbose:
        print("")
        print("Skipped:")
        for item in skipped:
            print(f"- {item}")

    if gradle_messages:
        print("")
        print("Gradle unwiring:")
        for msg in gradle_messages:
            print(f"- {msg}")

    return 0


def cmd_stacks(args: argparse.Namespace) -> int:
    rows = supported_stack_table()
    print("Supported stacks:")
    for row in rows:
        status = "implemented" if row.get("implemented") else "planned"
        print(f"- {row['id']}: {row['language']}/{row['framework']}/{row['orm']} [{status}]")
        print(f"  capabilities: {', '.join(row['capabilities'])}")
    return 0


def cmd_version_check(args: argparse.Namespace) -> int:
    root = Path.cwd()
    cfg = load_config(root / "prophet.yaml")
    resolve_stack_spec(cfg)
    ontology_path = ontology_path_from_cfg(root, cfg)
    ont = load_ontology_from_cfg(root, cfg)
    strict_enums = bool(cfg_get(cfg, ["compatibility", "strict_enums"], False))
    errors = validate_ontology(ont, strict_enums=strict_enums)
    if errors:
        print_validation_failure(errors, ontology_path)
        return 1

    current_ir = build_ir(ont, cfg)

    baseline_rel = args.against or str(cfg_get(cfg, ["compatibility", "baseline_ir"], ".prophet/baselines/main.ir.json"))
    baseline_path = root / baseline_rel
    if not baseline_path.exists():
        raise ProphetError(f"Baseline IR not found: {baseline_path}")

    baseline_ir = json.loads(baseline_path.read_text(encoding="utf-8"))

    compatibility, changes = compare_irs(baseline_ir, current_ir)
    required_bump = required_level_to_bump(compatibility)

    old_ver = str(baseline_ir.get("ontology", {}).get("version", "0.0.0"))
    new_ver = str(current_ir.get("ontology", {}).get("version", "0.0.0"))
    declared = declared_bump(old_ver, new_ver)

    print(f"Compatibility result: {compatibility}")
    print(f"Required version bump: {required_bump}")
    print(f"Declared version bump: {declared} ({old_ver} -> {new_ver})")
    print(f"Policy reference: {COMPATIBILITY_POLICY_DOC}")

    if changes:
        print("")
        if compatibility == "breaking":
            print("Detected breaking changes:")
        elif compatibility == "additive":
            print("Detected additive changes:")
        else:
            print("Detected non-functional changes:")
        for item in changes:
            print(f"- {item}")

    if bump_rank(declared) < bump_rank(required_bump):
        print("")
        print("Version check failed: declared bump is lower than required bump.")
        print(f"See compatibility policy table: {COMPATIBILITY_POLICY_DOC}")
        return 1

    return 0


def cmd_check(args: argparse.Namespace) -> int:
    root = Path.cwd()
    cfg = load_config(root / "prophet.yaml")
    stack = resolve_stack_spec(cfg)
    ontology_path = ontology_path_from_cfg(root, cfg)
    ont = load_ontology_from_cfg(root, cfg)
    strict_enums = bool(cfg_get(cfg, ["compatibility", "strict_enums"], False))
    errors = validate_ontology(ont, strict_enums=strict_enums)
    if errors:
        if args.json:
            report = {
                "ok": False,
                "validation": {
                    "passed": False,
                    "ontology_file": str(ontology_path),
                    "errors": errors,
                },
            }
            print(json.dumps(report, indent=2, sort_keys=False))
            return 1
        print_validation_failure(errors, ontology_path)
        return 1

    ir = build_ir(ont, cfg)
    delta_sql, delta_warnings, _, _, delta_meta = compute_delta_from_baseline(root, cfg, ir)
    outputs = build_generated_outputs(ir, cfg, root=root)
    dirty = collect_dirty_generated_files(root, cfg, outputs)
    status = 0
    dirty_clean = not dirty
    if not dirty_clean:
        status = 1

    baseline_rel = args.against or str(cfg_get(cfg, ["compatibility", "baseline_ir"], ".prophet/baselines/main.ir.json"))
    baseline_path = root / baseline_rel
    compatibility_level = "unknown"
    required_bump = "unknown"
    declared = "unknown"
    changes: List[str] = []
    old_ver = "0.0.0"
    new_ver = str(ir.get("ontology", {}).get("version", "0.0.0"))
    compatibility_passed = False
    baseline_found = baseline_path.exists()

    if not baseline_path.exists():
        status = 1
    else:
        baseline_ir = json.loads(baseline_path.read_text(encoding="utf-8"))
        compatibility_level, changes = compare_irs(baseline_ir, ir)
        required_bump = required_level_to_bump(compatibility_level)
        old_ver = str(baseline_ir.get("ontology", {}).get("version", "0.0.0"))
        declared = declared_bump(old_ver, new_ver)
        compatibility_passed = bump_rank(declared) >= bump_rank(required_bump)
        if not compatibility_passed:
            status = 1
    requested_migrations, detected_migrations, enabled_migrations, migration_warnings = resolve_migration_runtime_modes(
        cfg, root
    )

    if args.json:
        report = {
            "ok": status == 0,
            "stack": {
                "id": stack.id,
                "language": stack.language,
                "framework": stack.framework,
                "orm": stack.orm,
                "capabilities": sorted(stack.capabilities),
            },
            "validation": {
                "passed": True,
                "ontology_file": str(ontology_path),
                "errors": [],
            },
            "generation": {
                "clean": dirty_clean,
                "dirty_files": dirty,
            },
            "compatibility": {
                "baseline_found": baseline_found,
                "baseline_path": str(baseline_path),
                "level": compatibility_level,
                "required_bump": required_bump,
                "declared_bump": declared,
                "from_version": old_ver,
                "to_version": new_ver,
                "policy_reference": COMPATIBILITY_POLICY_DOC,
                "passed": compatibility_passed,
                "changes": changes if args.show_reasons else [],
            },
            "delta_migration": {
                "generated": bool(delta_sql),
                "warnings": delta_warnings,
                "summary": {
                    "safe_auto_apply_count": delta_meta.get("safe_auto_apply_count", 0),
                    "manual_review_count": delta_meta.get("manual_review_count", 0),
                    "destructive_count": delta_meta.get("destructive_count", 0),
                },
                "findings": delta_meta.get("findings", []),
            },
            "migrations": {
                "requested": sorted(requested_migrations),
                "detected": sorted(detected_migrations),
                "enabled_runtime_wiring": sorted(enabled_migrations),
                "warnings": migration_warnings,
            },
        }
        print(json.dumps(report, indent=2, sort_keys=False))
        return status

    print("Validation passed.")
    print(f"Stack: {stack.id} ({stack.language}/{stack.framework}/{stack.orm})")
    if dirty:
        print("")
        print_dirty_generated_files(dirty)
        status = 1
    else:
        print("Generated outputs are clean.")

    print("")
    if not baseline_found:
        print(f"Version check failed: baseline IR not found: {baseline_path}")
        print("How to fix:")
        print("- Run `prophet gen` once to create a baseline IR.")
        print("- Or set `compatibility.baseline_ir` to the correct baseline path.")
    else:
        print(f"Compatibility result: {compatibility_level}")
        print(f"Required version bump: {required_bump}")
        print(f"Declared version bump: {declared} ({old_ver} -> {new_ver})")
        print(f"Policy reference: {COMPATIBILITY_POLICY_DOC}")
        if changes and args.show_reasons:
            print("Detected compatibility changes:")
            for item in changes:
                print(f"- {item}")
        if not compatibility_passed:
            print("Version check failed: declared bump is lower than required bump.")
            print(f"See compatibility policy table: {COMPATIBILITY_POLICY_DOC}")
    if delta_sql:
        print("")
        print("Delta migration summary:")
        print("- generated: yes")
        print(f"- safe auto-apply findings: {delta_meta.get('safe_auto_apply_count', 0)}")
        print(f"- manual review findings: {delta_meta.get('manual_review_count', 0)}")
        print(f"- destructive findings: {delta_meta.get('destructive_count', 0)}")
        if delta_warnings:
            print("- warnings:")
            for warning in delta_warnings:
                print(f"  - {warning}")

    print("")
    if status == 0:
        print("Check passed.")
    else:
        print("Check failed.")
    return status


def build_cli() -> argparse.ArgumentParser:
    class HelpFormatter(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
        pass

    parser = argparse.ArgumentParser(
        prog="prophet",
        formatter_class=HelpFormatter,
        description=(
            "Prophet ontology tooling CLI\n\n"
            "Reads prophet.yaml from the current working directory and runs the\n"
            "DSL -> validation -> IR -> generation pipeline."
        ),
        epilog=(
            "Common workflow:\n"
            "  prophet check --show-reasons\n"
            "  prophet gen --wire-gradle\n"
            "  prophet check"
        ),
    )
    sub = parser.add_subparsers(
        dest="command",
        required=True,
        metavar="COMMAND",
        title="commands",
        description="Available commands",
    )

    p_init = sub.add_parser(
        "init",
        formatter_class=HelpFormatter,
        help="Create starter prophet.yaml and Prophet metadata directories",
        description=(
            "Initialize Prophet config and metadata directories in the current directory.\n"
            "Set project.ontology_file to your own ontology file path."
        ),
    )
    p_init.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing prophet.yaml and Prophet metadata scaffold",
    )
    p_init.set_defaults(func=cmd_init)

    p_validate = sub.add_parser(
        "validate",
        formatter_class=HelpFormatter,
        help="Validate ontology syntax and semantic references",
        description=(
            "Parse and validate ontology definitions.\n"
            "Fails on invalid refs, duplicate IDs, broken transitions, and action contract mismatches."
        ),
    )
    p_validate.set_defaults(func=cmd_validate)

    p_plan = sub.add_parser(
        "plan",
        formatter_class=HelpFormatter,
        help="Show deterministic generated file changes without writing",
        description="Compute generation diff and compatibility summary without modifying files.",
    )
    p_plan.add_argument(
        "--show-reasons",
        action="store_true",
        help="Include compatibility change reasons (field/state/transition level)",
    )
    p_plan.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON plan output",
    )
    p_plan.set_defaults(func=cmd_plan)

    p_check = sub.add_parser(
        "check",
        formatter_class=HelpFormatter,
        help="Run validation + generated output cleanliness + compatibility bump checks",
        description=(
            "Run a CI-friendly quality gate in one command:\n"
            "1) validate ontology\n"
            "2) verify generated outputs are clean\n"
            "3) check compatibility/version bump against baseline IR"
        ),
    )
    p_check.add_argument(
        "--against",
        type=str,
        help="Path to baseline IR JSON (defaults to compatibility.baseline_ir in prophet.yaml)",
    )
    p_check.add_argument(
        "--show-reasons",
        action="store_true",
        help="Include compatibility change reasons from baseline comparison",
    )
    p_check.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON diagnostics instead of human-readable text",
    )
    p_check.set_defaults(func=cmd_check)

    p_stacks = sub.add_parser(
        "stacks",
        formatter_class=HelpFormatter,
        help="List supported generation stack ids and capabilities",
        description="Display supported framework/ORM stack combinations and capability metadata.",
    )
    p_stacks.set_defaults(func=cmd_stacks)

    p_generate = sub.add_parser(
        "generate",
        formatter_class=HelpFormatter,
        help="Generate SQL/OpenAPI/Spring/migration artifacts and current IR",
        description=(
            "Write deterministic generated artifacts to the configured output directory.\n"
            "Also updates .prophet/ir/current.ir.json and syncs the Spring example project if present."
        ),
    )
    p_generate.add_argument(
        "--verify-clean",
        action="store_true",
        help="CI mode: fail if generated outputs differ from files on disk",
    )
    p_generate.add_argument(
        "--wire-gradle",
        action="store_true",
        help="Auto-wire current Gradle project as multi-module with :prophet_generated",
    )
    p_generate.add_argument(
        "--skip-unchanged",
        action="store_true",
        help="Skip generation when config/IR signature is unchanged (ignored with --wire-gradle)",
    )
    p_generate.set_defaults(func=cmd_generate)

    p_gen = sub.add_parser(
        "gen",
        formatter_class=HelpFormatter,
        help="Alias for generate",
        description=(
            "Alias for `prophet generate`.\n"
            "Supports the same flags and behavior."
        ),
    )
    p_gen.add_argument(
        "--verify-clean",
        action="store_true",
        help="CI mode: fail if generated outputs differ from files on disk",
    )
    p_gen.add_argument(
        "--wire-gradle",
        action="store_true",
        help="Auto-wire current Gradle project as multi-module with :prophet_generated",
    )
    p_gen.add_argument(
        "--skip-unchanged",
        action="store_true",
        help="Skip generation when config/IR signature is unchanged (ignored with --wire-gradle)",
    )
    p_gen.set_defaults(func=cmd_generate)

    p_clean = sub.add_parser(
        "clean",
        formatter_class=HelpFormatter,
        help="Remove generated artifacts",
        description=(
            "Remove generated outputs from current project.\n"
            "By default removes gen/, .prophet/ir/current.ir.json, and generated Spring sync files."
        ),
    )
    p_clean.add_argument(
        "--remove-baseline",
        action="store_true",
        help="Also remove compatibility baseline (.prophet/baselines/main.ir.json)",
    )
    p_clean.add_argument(
        "--force-schema",
        action="store_true",
        help="Also remove src/main/resources/schema.sql even if it does not look generated",
    )
    p_clean.add_argument(
        "--verbose",
        action="store_true",
        help="Print skipped paths in addition to removed paths",
    )
    p_clean.add_argument(
        "--keep-gradle-wire",
        action="store_true",
        help="Do not remove :prophet_generated wiring from settings/build Gradle files",
    )
    p_clean.set_defaults(func=cmd_clean)

    p_version = sub.add_parser(
        "version",
        formatter_class=HelpFormatter,
        help="Version compatibility operations",
        description="Run compatibility checks between current ontology and a baseline IR.",
    )
    version_sub = p_version.add_subparsers(dest="version_cmd", required=True)
    p_version_check = version_sub.add_parser(
        "check",
        formatter_class=HelpFormatter,
        help="Compare current IR against baseline and enforce semver bump",
        description=(
            "Compute compatibility class (breaking/additive/non_functional),\n"
            "required semver bump, and fail if declared bump is insufficient."
        ),
    )
    p_version_check.add_argument(
        "--against",
        type=str,
        help="Path to baseline IR JSON (defaults to compatibility.baseline_ir in prophet.yaml)",
    )
    p_version_check.set_defaults(func=cmd_version_check)

    return parser


def main() -> int:
    parser = build_cli()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except ProphetError as e:
        message = str(e)
        print(f"Error: {message}", file=sys.stderr)
        hints = hints_for_prophet_error(message)
        if hints:
            print("Hints:", file=sys.stderr)
            for hint in hints:
                print(f"- {hint}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
