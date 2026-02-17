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
from prophet_cli.core.materialize import materialize_missing_ids
from prophet_cli.codegen.stacks import resolve_stack_spec
from prophet_cli.codegen.stacks import stack_manifest_metadata
from prophet_cli.codegen.stacks import supported_stack_table
from prophet_cli.codegen.contracts import GenerationContext
from prophet_cli.codegen.contracts import StackGenerator
from prophet_cli.codegen.cache import compute_generation_signature
from prophet_cli.codegen.cache import generation_cache_path
from prophet_cli.codegen.cache import load_generation_cache
from prophet_cli.codegen.cache import write_generation_cache
from prophet_cli.codegen.pipeline import run_generation_pipeline
from prophet_cli.codegen.artifacts import managed_existing_files as _managed_existing_files
from prophet_cli.codegen.artifacts import remove_stale_outputs as _remove_stale_outputs
from prophet_cli.codegen.artifacts import write_outputs as _write_outputs
from prophet_cli.codegen.rendering import compute_delta_from_baseline
from prophet_cli.codegen.rendering import render_openapi
from prophet_cli.codegen.rendering import render_sql
from prophet_cli.targets.java_spring_jpa import JavaSpringJpaDeps
from prophet_cli.targets.java_spring_jpa import generate_outputs as generate_java_spring_jpa_outputs
from prophet_cli.targets.java_spring_jpa.render.spring import resolve_migration_runtime_modes
from prophet_cli.targets.node_express import NodeExpressDeps
from prophet_cli.targets.node_express import generate_outputs as generate_node_express_outputs
from prophet_cli.targets.node_express.autodetect import apply_node_autodetect
from prophet_cli.targets.python import apply_python_autodetect
from prophet_cli.targets.python import PythonDeps
from prophet_cli.targets.python import generate_outputs as generate_python_outputs
from prophet_cli.targets.turtle import render_turtle


TOOLCHAIN_VERSION = "0.20.0"
IR_VERSION = "0.1"
COMPATIBILITY_POLICY_DOC = "docs/reference/compatibility.md"

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


def java_package_segment(value: str) -> str:
    raw = snake_case(value).strip("_")
    if not raw:
        return "ontology"
    normalized = re.sub(r"[^a-z0-9_]", "_", raw)
    if normalized[:1].isdigit():
        return f"o_{normalized}"
    return normalized


def effective_base_package(base_package: str, ontology_name: str) -> str:
    segment = java_package_segment(ontology_name)
    suffix = f".{segment}"
    if base_package.endswith(suffix):
        return base_package
    return f"{base_package}{suffix}"


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
                    "field_id": "__state__",
                    "field_name": "state",
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


def _generate_outputs_for_java_spring_jpa(context: GenerationContext) -> Dict[str, str]:
    deps = JavaSpringJpaDeps(
        cfg_get=cfg_get,
        resolve_stack_spec=resolve_stack_spec,
        render_sql=lambda reader: render_sql(reader.as_dict()),
        compute_delta_from_baseline=lambda root, cfg, reader: compute_delta_from_baseline(
            root,
            cfg,
            reader.as_dict(),
        ),
        render_openapi=lambda reader: render_openapi(reader.as_dict()),
        render_turtle=lambda reader: render_turtle(reader.as_dict()),
        toolchain_version=TOOLCHAIN_VERSION,
    )
    return generate_java_spring_jpa_outputs(context, deps)


def _generate_outputs_for_node_express(context: GenerationContext) -> Dict[str, str]:
    deps = NodeExpressDeps(
        cfg_get=cfg_get,
        resolve_stack_spec=resolve_stack_spec,
        render_sql=lambda reader: render_sql(reader.as_dict()),
        render_openapi=lambda reader: render_openapi(reader.as_dict()),
        render_turtle=lambda reader: render_turtle(reader.as_dict()),
        toolchain_version=TOOLCHAIN_VERSION,
    )
    return generate_node_express_outputs(context, deps)


def _generate_outputs_for_python(context: GenerationContext) -> Dict[str, str]:
    deps = PythonDeps(
        cfg_get=cfg_get,
        resolve_stack_spec=resolve_stack_spec,
        render_sql=lambda reader: render_sql(reader.as_dict()),
        render_openapi=lambda reader: render_openapi(reader.as_dict()),
        render_turtle=lambda reader: render_turtle(reader.as_dict()),
        toolchain_version=TOOLCHAIN_VERSION,
    )
    return generate_python_outputs(context, deps)


def registered_generators() -> Dict[str, StackGenerator]:
    return {
        "java_spring_jpa": _generate_outputs_for_java_spring_jpa,
        "node_express_prisma": _generate_outputs_for_node_express,
        "node_express_typeorm": _generate_outputs_for_node_express,
        "node_express_mongoose": _generate_outputs_for_node_express,
        "python_fastapi_sqlalchemy": _generate_outputs_for_python,
        "python_fastapi_sqlmodel": _generate_outputs_for_python,
        "python_flask_sqlalchemy": _generate_outputs_for_python,
        "python_flask_sqlmodel": _generate_outputs_for_python,
        "python_django_django_orm": _generate_outputs_for_python,
    }


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
        generators=registered_generators(),
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


def wire_node_project(root: Path) -> List[str]:
    package_json_path = root / "package.json"
    if not package_json_path.exists():
        return ["Skipped Node auto-wiring: package.json not found in current directory."]

    try:
        package = json.loads(package_json_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"Skipped Node auto-wiring: unable to parse package.json ({exc})."]

    if not isinstance(package, dict):
        return ["Skipped Node auto-wiring: package.json must contain a JSON object."]

    scripts = package.get("scripts", {})
    if not isinstance(scripts, dict):
        scripts = {}
    package["scripts"] = scripts

    messages: List[str] = []

    def ensure_script(name: str, value: str) -> None:
        existing = scripts.get(name)
        if existing == value:
            messages.append(f"package.json script '{name}' already configured.")
            return
        if existing is None:
            scripts[name] = value
            messages.append(f"Added package.json script '{name}'.")
            return
        messages.append(
            f"Skipped package.json script '{name}' update because it already exists with custom value."
        )

    ensure_script("prophet:gen", "prophet gen")
    ensure_script("prophet:check", "prophet check --show-reasons")
    ensure_script("prophet:validate", "prophet validate")

    package_json_path.write_text(json.dumps(package, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return messages


def unwire_node_project(root: Path) -> List[str]:
    package_json_path = root / "package.json"
    if not package_json_path.exists():
        return ["Skipped Node unwiring: package.json not found in current directory."]

    try:
        package = json.loads(package_json_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"Skipped Node unwiring: unable to parse package.json ({exc})."]

    if not isinstance(package, dict):
        return ["Skipped Node unwiring: package.json must contain a JSON object."]

    scripts = package.get("scripts", {})
    if not isinstance(scripts, dict):
        return ["Skipped Node unwiring: package.json scripts section is not a JSON object."]

    expected = {
        "prophet:gen": "prophet gen",
        "prophet:check": "prophet check --show-reasons",
        "prophet:validate": "prophet validate",
    }
    messages: List[str] = []
    changed = False
    for key, expected_value in expected.items():
        existing = scripts.get(key)
        if existing is None:
            messages.append(f"package.json script '{key}' not present.")
            continue
        if existing != expected_value:
            messages.append(f"Skipped removing package.json script '{key}' because it has a custom value.")
            continue
        del scripts[key]
        changed = True
        messages.append(f"Removed package.json script '{key}'.")

    if changed:
        package["scripts"] = scripts
        package_json_path.write_text(json.dumps(package, indent=2, sort_keys=False) + "\n", encoding="utf-8")

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
    source = ont_path.read_text(encoding="utf-8")
    ontology = parse_ontology(source)
    materialized_source, changed = materialize_missing_ids(source, ontology)
    if changed:
        ont_path.write_text(materialized_source, encoding="utf-8")
        ontology = parse_ontology(materialized_source)
    return ontology


@dataclass(frozen=True)
class CommandContext:
    root: Path
    cfg: Dict[str, Any]
    stack: StackSpec
    ontology_path: Path
    ontology: Ontology
    strict_enums: bool


def load_command_context(root: Path) -> Tuple[CommandContext, List[str]]:
    cfg = load_config(root / "prophet.yaml")
    cfg = apply_node_autodetect(cfg, root)
    cfg = apply_python_autodetect(cfg, root)

    node_autodetect_error = str(cfg.get("_autodetect_error", "")).strip()
    if node_autodetect_error:
        raise ProphetError(
            "Node autodetect failed to resolve a safe generation stack. "
            + node_autodetect_error
        )

    python_autodetect_error = str(cfg.get("_python_autodetect_error", "")).strip()
    if python_autodetect_error:
        raise ProphetError(
            "Python autodetect failed to resolve a safe generation stack. "
            + python_autodetect_error
        )

    stack = resolve_stack_spec(cfg)
    ontology_path = ontology_path_from_cfg(root, cfg)
    ontology = load_ontology_from_cfg(root, cfg)
    strict_enums = bool(cfg_get(cfg, ["compatibility", "strict_enums"], False))
    errors = validate_ontology(ontology, strict_enums=strict_enums)
    return (
        CommandContext(
            root=root,
            cfg=cfg,
            stack=stack,
            ontology_path=ontology_path,
            ontology=ontology,
            strict_enums=strict_enums,
        ),
        errors,
    )


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
    if "extension hook manifest not found" in msg:
        hints.append("Run `prophet gen` first so Prophet can emit extension hook metadata.")
    if "--wire-gradle cannot be used with --verify-clean" in msg:
        hints.append("Use `prophet gen --wire-gradle` and `prophet check` (or `prophet generate --verify-clean`) as separate steps.")
    if "--skip-unchanged cannot be used with --verify-clean" in msg:
        hints.append("Use `prophet gen --skip-unchanged` for local no-op speedups, and `prophet check` or `prophet generate --verify-clean` in CI.")
    if "invalid semver" in msg:
        hints.append("Use semantic versions in ontology `version`, for example `1.2.3`.")
    return hints


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
    ctx, errors = load_command_context(root)
    if errors:
        print_validation_failure(errors, ctx.ontology_path)
        return 1
    print("Validation passed.")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    root = Path.cwd()
    ctx, errors = load_command_context(root)
    if errors:
        print_validation_failure(errors, ctx.ontology_path)
        return 1

    ir = build_ir(ctx.ontology, ctx.cfg)
    delta_sql, delta_warnings, baseline_path, _, _ = compute_delta_from_baseline(root, ctx.cfg, ir)
    outputs = build_generated_outputs(ir, ctx.cfg, root=root)

    existing = set(managed_existing_files(root, ctx.cfg))
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

    baseline_path = root / str(cfg_get(ctx.cfg, ["compatibility", "baseline_ir"], ".prophet/baselines/main.ir.json"))
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
                "id": ctx.stack.id,
                "language": ctx.stack.language,
                "framework": ctx.stack.framework,
                "orm": ctx.stack.orm,
                "status": ctx.stack.status,
                "implemented": ctx.stack.implemented,
                "capabilities": sorted(ctx.stack.capabilities),
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
    print(f"Stack: {ctx.stack.id} ({ctx.stack.language}/{ctx.stack.framework}/{ctx.stack.orm})")
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
    ctx, errors = load_command_context(root)
    if errors:
        print_validation_failure(errors, ctx.ontology_path)
        return 1

    ir = build_ir(ctx.ontology, ctx.cfg)

    if args.verify_clean and args.wire_gradle:
        raise ProphetError("--wire-gradle cannot be used with --verify-clean")
    if args.verify_clean and args.skip_unchanged:
        raise ProphetError("--skip-unchanged cannot be used with --verify-clean")

    out_dir = str(cfg_get(ctx.cfg, ["generation", "out_dir"], "gen"))
    targets = list(cfg_get(ctx.cfg, ["generation", "targets"], list(ctx.stack.default_targets)))
    baseline_ir = str(cfg_get(ctx.cfg, ["compatibility", "baseline_ir"], ".prophet/baselines/main.ir.json"))
    signature = compute_generation_signature(
        toolchain_version=TOOLCHAIN_VERSION,
        stack_id=ctx.stack.id,
        ir_hash=str(ir.get("ir_hash", "")),
        out_dir=out_dir,
        targets=targets,
        baseline_ir=baseline_ir,
    )
    manifest_path = root / out_dir / "manifest" / "generated-files.json"
    cache_payload = load_generation_cache(root)
    cached_signature = str(cache_payload.get("signature", "")) if isinstance(cache_payload, dict) else ""
    if args.skip_unchanged and not args.wire_gradle:
        if cached_signature == signature and manifest_path.exists():
            print("Skipped generation: configuration and IR unchanged.")
            print(f"- stack: {ctx.stack.id} ({ctx.stack.language}/{ctx.stack.framework}/{ctx.stack.orm})")
            print(f"- signature: {signature}")
            return 0

    delta_sql, delta_warnings, baseline_path, _, _ = compute_delta_from_baseline(root, ctx.cfg, ir)
    outputs = build_generated_outputs(ir, ctx.cfg, root=root)

    if args.verify_clean:
        dirty = collect_dirty_generated_files(root, ctx.cfg, outputs)
        if dirty:
            print_dirty_generated_files(dirty)
            return 1

        print("Generated outputs are clean.")
        return 0

    remove_stale_outputs(root, ctx.cfg, outputs)
    write_outputs(outputs, root)

    ir_path = root / ".prophet" / "ir" / "current.ir.json"
    ir_path.parent.mkdir(parents=True, exist_ok=True)
    ir_path.write_text(json.dumps(ir, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    ensure_baseline_exists(root, ctx.cfg, ir)

    sync_example_project(root, ctx.cfg)

    gradle_messages: List[str] = []
    node_wiring_messages: List[str] = []
    requested_migrations: set[str] = set()
    detected_migrations: set[str] = set()
    enabled_migrations: set[str] = set()
    migration_warnings: List[str] = []
    if ctx.stack.language == "java":
        requested_migrations, detected_migrations, enabled_migrations, migration_warnings = resolve_migration_runtime_modes(
            ctx.cfg, root
        )
    if ctx.stack.language == "node":
        node_wiring_messages = wire_node_project(root)
    if args.wire_gradle:
        gradle_messages = wire_gradle_multi_module(root, ctx.cfg)

    print("Generated artifacts:")
    print(f"- stack: {ctx.stack.id} ({ctx.stack.language}/{ctx.stack.framework}/{ctx.stack.orm})")
    for rel in sorted(outputs.keys()):
        print(f"- {rel}")
    print("- .prophet/ir/current.ir.json")
    if ctx.stack.language == "java":
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
    if node_wiring_messages:
        print("")
        print("Node auto-wiring:")
        for msg in node_wiring_messages:
            print(f"- {msg}")

    write_generation_cache(
        root,
        {
            "schema_version": 1,
            "toolchain_version": TOOLCHAIN_VERSION,
            "stack_id": ctx.stack.id,
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
    cfg = apply_node_autodetect(cfg, root)
    cfg = apply_python_autodetect(cfg, root)
    out_dir = root / str(cfg_get(cfg, ["generation", "out_dir"], "gen"))
    baseline_rel = str(cfg_get(cfg, ["compatibility", "baseline_ir"], ".prophet/baselines/main.ir.json"))
    baseline_path = root / baseline_rel
    current_ir_path = root / ".prophet" / "ir" / "current.ir.json"
    generation_cache = generation_cache_path(root)

    removed: List[str] = []
    skipped: List[str] = []
    gradle_messages: List[str] = []
    node_unwire_messages: List[str] = []
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

    configured_base_package = str(cfg_get(cfg, ["generation", "spring_boot", "base_package"], "com.example.prophet"))
    ontology_name = "prophet"
    if current_ir_path.exists():
        try:
            ir_payload = json.loads(current_ir_path.read_text(encoding="utf-8"))
            if isinstance(ir_payload, dict):
                ontology_name = str(ir_payload.get("ontology", {}).get("name", ontology_name))
        except Exception:
            pass
    else:
        ontology_rel = str(cfg_get(cfg, ["project", "ontology_file"], "ontology/local/main.prophet"))
        ontology_path = root / ontology_rel
        if ontology_path.exists():
            try:
                ontology = load_ontology_from_cfg(root, cfg)
                ontology_name = ontology.name
            except Exception:
                pass
    base_package = effective_base_package(configured_base_package, ontology_name)
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
    try:
        stack = resolve_stack_spec(cfg)
        if stack.language == "node":
            node_unwire_messages = unwire_node_project(root)
    except ProphetError:
        pass

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
    if node_unwire_messages:
        print("")
        print("Node unwiring:")
        for msg in node_unwire_messages:
            print(f"- {msg}")

    return 0


def cmd_stacks(args: argparse.Namespace) -> int:
    metadata = stack_manifest_metadata()
    rows = supported_stack_table()
    if args.json:
        print(
            json.dumps(
                {
                    "schema_version": metadata["schema_version"],
                    "capability_catalog": metadata["capability_catalog"],
                    "stacks": rows,
                },
                indent=2,
                sort_keys=False,
            )
        )
        return 0

    print("Supported stacks:")
    print(f"- schema_version: {metadata['schema_version']}")
    for row in rows:
        status = str(row.get("status", "planned"))
        print(f"- {row['id']}: {row['language']}/{row['framework']}/{row['orm']} [{status}]")
        print(f"  description: {row['description']}")
        print(f"  capabilities: {', '.join(row['capabilities'])}")
        print(f"  default targets: {', '.join(row['default_targets'])}")
        notes = str(row.get("notes", "")).strip()
        if notes:
            print(f"  notes: {notes}")
    return 0


def cmd_hooks(args: argparse.Namespace) -> int:
    root = Path.cwd()
    cfg = load_config(root / "prophet.yaml")
    out_dir = str(cfg_get(cfg, ["generation", "out_dir"], "gen"))
    manifest_path = root / out_dir / "manifest" / "extension-hooks.json"
    if not manifest_path.exists():
        raise ProphetError(f"Extension hook manifest not found: {manifest_path}.")

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    hooks = payload.get("hooks", [])

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False))
        return 0

    print(f"Extension hooks ({len(hooks)}):")
    for idx, item in enumerate(hooks, start=1):
        kind = str(item.get("kind", "hook"))
        name = str(item.get("action_name", ""))
        hook_id = str(item.get("action_id", ""))
        print(f"{idx}) {kind}: {name} ({hook_id})")
        if item.get("java_interface"):
            print(f"   interface: {item['java_interface']}")
        if item.get("default_implementation_class"):
            print(f"   default: {item['default_implementation_class']}")
    return 0


def cmd_version_check(args: argparse.Namespace) -> int:
    root = Path.cwd()
    ctx, errors = load_command_context(root)
    if errors:
        print_validation_failure(errors, ctx.ontology_path)
        return 1

    current_ir = build_ir(ctx.ontology, ctx.cfg)

    baseline_rel = args.against or str(cfg_get(ctx.cfg, ["compatibility", "baseline_ir"], ".prophet/baselines/main.ir.json"))
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
    ctx, errors = load_command_context(root)
    if errors:
        if args.json:
            report = {
                "ok": False,
                "validation": {
                    "passed": False,
                    "ontology_file": str(ctx.ontology_path),
                    "errors": errors,
                },
            }
            print(json.dumps(report, indent=2, sort_keys=False))
            return 1
        print_validation_failure(errors, ctx.ontology_path)
        return 1

    ir = build_ir(ctx.ontology, ctx.cfg)
    delta_sql, delta_warnings, _, _, delta_meta = compute_delta_from_baseline(root, ctx.cfg, ir)
    outputs = build_generated_outputs(ir, ctx.cfg, root=root)
    dirty = collect_dirty_generated_files(root, ctx.cfg, outputs)
    status = 0
    dirty_clean = not dirty
    if not dirty_clean:
        status = 1

    baseline_rel = args.against or str(cfg_get(ctx.cfg, ["compatibility", "baseline_ir"], ".prophet/baselines/main.ir.json"))
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
        ctx.cfg, root
    )

    if args.json:
        report = {
            "ok": status == 0,
            "stack": {
                "id": ctx.stack.id,
                "language": ctx.stack.language,
                "framework": ctx.stack.framework,
                "orm": ctx.stack.orm,
                "status": ctx.stack.status,
                "implemented": ctx.stack.implemented,
                "capabilities": sorted(ctx.stack.capabilities),
            },
            "validation": {
                "passed": True,
                "ontology_file": str(ctx.ontology_path),
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
    print(f"Stack: {ctx.stack.id} ({ctx.stack.language}/{ctx.stack.framework}/{ctx.stack.orm})")
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
    p_stacks.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON stack matrix output",
    )
    p_stacks.set_defaults(func=cmd_stacks)

    p_hooks = sub.add_parser(
        "hooks",
        formatter_class=HelpFormatter,
        help="List generated extension hook surfaces",
        description=(
            "Read generated extension hook metadata and print available extension points.\n"
            "Requires a prior `prophet gen` run."
        ),
    )
    p_hooks.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON hook metadata from extension-hooks.json",
    )
    p_hooks.set_defaults(func=cmd_hooks)

    p_generate = sub.add_parser(
        "generate",
        formatter_class=HelpFormatter,
        help="Generate SQL/OpenAPI/Turtle/stack artifacts and current IR",
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
