from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from .constants import BASE_TYPES
from .errors import ProphetError
from .models import ActionDef
from .models import ActionShapeDef
from .models import EventDef
from .models import FieldDef
from .models import KeyDef
from .models import ObjectDef
from .models import Ontology
from .models import StateDef
from .models import StructDef
from .models import TransitionDef
from .models import TriggerDef
from .models import TypeDef


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


def _parse_optional_description_line(line: str) -> Optional[str]:
    m = re.match(r'^description\s+\"(.*)\"$', line)
    if m:
        return m.group(1)
    m = re.match(r'^documentation\s+\"(.*)\"$', line)
    if m:
        return m.group(1)
    return None


def _parse_key_fields_csv(raw: str, line: int) -> List[str]:
    fields = [item.strip() for item in raw.split(",")]
    if not fields or any(not item for item in fields):
        raise ProphetError(f"line {line}: key declaration must include one or more field names")
    invalid = [name for name in fields if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name)]
    if invalid:
        raise ProphetError(f"line {line}: key declaration contains invalid field names: {', '.join(invalid)}")
    return fields


def _pascal_case(value: str) -> str:
    chunks = [part for part in value.replace("-", "_").split("_") if part]
    return "".join(chunk[:1].upper() + chunk[1:] for chunk in chunks)


def _snake_case(value: str) -> str:
    if not value:
        return ""
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", value)
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized)
    return normalized.strip("_").lower()


def transition_event_name(object_name: str, transition_name: str) -> str:
    return f"{object_name}{_pascal_case(transition_name)}Transition"


def _extract_explicit_ids(lines: List[Tuple[int, str]]) -> set[str]:
    ids: set[str] = set()
    for _, line in lines:
        if re.match(r"^id\s+\".*\"$", line):
            value = re.match(r'^id\s+\"(.*)\"$', line).group(1)  # type: ignore[union-attr]
            ids.add(value)
    return ids


class IdAllocator:
    def __init__(self, reserved_ids: set[str]):
        self._used_ids = set(reserved_ids)

    def reserve(self, value: str) -> None:
        self._used_ids.add(value)

    def generate(self, base: str) -> str:
        slug = _snake_case(base) or "id"
        candidate = slug
        suffix = 2
        while candidate in self._used_ids:
            candidate = f"{slug}_{suffix}"
            suffix += 1
        self._used_ids.add(candidate)
        return candidate


def parse_ontology(text: str) -> Ontology:
    p = Parser(text)
    start = p.expect(r"^ontology\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", "Expected ontology header")
    ont_name = start.group(1)
    id_allocator = IdAllocator(_extract_explicit_ids(p.lines))

    ont_id: Optional[str] = None
    ont_version: Optional[str] = None
    ont_description: Optional[str] = None
    types: List[TypeDef] = []
    objects: List[ObjectDef] = []
    structs: List[StructDef] = []
    action_inputs: List[ActionShapeDef] = []
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
            id_allocator.reserve(ont_id)
            continue

        if re.match(r"^version\s+\".*\"$", line):
            _, row = p.pop()
            ont_version = re.match(r'^version\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            continue

        parsed_description = _parse_optional_description_line(line)
        if parsed_description is not None:
            p.pop()
            ont_description = parsed_description
            continue

        m = re.match(r"^type\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            types.append(parse_type_block(p, m.group(1), ln, id_allocator))
            continue

        m = re.match(r"^object\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            objects.append(parse_object_block(p, m.group(1), ln, id_allocator))
            continue

        m = re.match(r"^struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            structs.append(parse_struct_block(p, m.group(1), ln, id_allocator))
            continue

        m = re.match(r"^action\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            action_def, inline_input, inline_output_event = parse_action_block(p, m.group(1), ln, id_allocator)
            actions.append(action_def)
            if inline_input is not None:
                action_inputs.append(inline_input)
            if inline_output_event is not None:
                events.append(inline_output_event)
            continue

        m = re.match(r"^signal\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            events.append(parse_signal_block(p, m.group(1), ln, id_allocator))
            continue

        m = re.match(r"^trigger\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            triggers.append(parse_trigger_block(p, m.group(1), ln, id_allocator))
            continue

        raise ProphetError(f"Unexpected line {ln}: {line}")

    if ont_id is None:
        ont_id = id_allocator.generate(f"ont_{ont_name}")
    if ont_version is None:
        raise ProphetError("Ontology missing version")

    return Ontology(
        name=ont_name,
        id=ont_id,
        version=ont_version,
        description=ont_description,
        types=types,
        objects=objects,
        structs=structs,
        action_inputs=action_inputs,
        actions=actions,
        events=events,
        triggers=triggers,
    )


def parse_type_block(p: Parser, name: str, block_line: int, id_allocator: IdAllocator) -> TypeDef:
    t_id: Optional[str] = None
    base: Optional[str] = None
    constraints: Dict[str, str] = {}
    description: Optional[str] = None
    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break

        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            t_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            id_allocator.reserve(t_id)
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

        parsed_description = _parse_optional_description_line(line)
        if parsed_description is not None:
            p.pop()
            description = parsed_description
            continue

        raise ProphetError(f"Unexpected type line {ln}: {line}")

    if t_id is None:
        t_id = id_allocator.generate(f"type_{name}")
    if base is None:
        raise ProphetError(f"Type {name} missing base (line {block_line})")
    return TypeDef(name=name, id=t_id, base=base, constraints=constraints, description=description, line=block_line)


def parse_object_block(p: Parser, name: str, block_line: int, id_allocator: IdAllocator) -> ObjectDef:
    o_id: Optional[str] = None
    fields: List[FieldDef] = []
    keys: List[KeyDef] = []
    states: List[StateDef] = []
    transitions: List[TransitionDef] = []
    description: Optional[str] = None

    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break

        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            o_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            id_allocator.reserve(o_id)
            continue

        m = re.match(r"^field\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            fields.append(parse_field_block(p, m.group(1), ln, id_allocator, f"obj_{name}"))
            continue

        m = re.match(r"^key\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*)\)$", line)
        if m:
            p.pop()
            keys.append(KeyDef(kind=m.group(1), field_names=_parse_key_fields_csv(m.group(2), ln), line=ln))
            continue

        m = re.match(r"^state\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            states.append(parse_state_block(p, m.group(1), ln, id_allocator, name))
            continue

        m = re.match(r"^transition\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            transitions.append(parse_transition_block(p, m.group(1), ln, id_allocator, name))
            continue

        parsed_description = _parse_optional_description_line(line)
        if parsed_description is not None:
            p.pop()
            description = parsed_description
            continue

        raise ProphetError(f"Unexpected object line {ln}: {line}")

    if o_id is None:
        o_id = id_allocator.generate(f"obj_{name}")
    return ObjectDef(
        name=name,
        id=o_id,
        fields=fields,
        keys=keys,
        states=states,
        transitions=transitions,
        description=description,
        line=block_line,
    )


def parse_struct_block(p: Parser, name: str, block_line: int, id_allocator: IdAllocator) -> StructDef:
    s_id: Optional[str] = None
    fields: List[FieldDef] = []
    description: Optional[str] = None

    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break

        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            s_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            id_allocator.reserve(s_id)
            continue

        m = re.match(r"^field\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            fields.append(parse_field_block(p, m.group(1), ln, id_allocator, f"struct_{name}"))
            continue

        parsed_description = _parse_optional_description_line(line)
        if parsed_description is not None:
            p.pop()
            description = parsed_description
            continue

        raise ProphetError(f"Unexpected struct line {ln}: {line}")

    if s_id is None:
        s_id = id_allocator.generate(f"struct_{name}")
    return StructDef(name=name, id=s_id, fields=fields, description=description, line=block_line)


def parse_field_block(
    p: Parser,
    name: str,
    block_line: int,
    id_allocator: IdAllocator,
    owner_scope: str,
) -> FieldDef:
    f_id: Optional[str] = None
    type_raw: Optional[str] = None
    required = True
    key: Optional[str] = None
    description: Optional[str] = None

    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break

        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            f_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            id_allocator.reserve(f_id)
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

        parsed_description = _parse_optional_description_line(line)
        if parsed_description is not None:
            p.pop()
            description = parsed_description
            continue

        raise ProphetError(f"Unexpected field line {ln}: {line}")

    if f_id is None:
        f_id = id_allocator.generate(f"fld_{owner_scope}_{name}")
    if type_raw is None:
        raise ProphetError(f"Field {name} missing type (line {block_line})")

    return FieldDef(
        name=name,
        id=f_id,
        type_raw=type_raw,
        required=required,
        key=key,
        description=description,
        line=block_line,
    )


def parse_state_block(
    p: Parser,
    name: str,
    block_line: int,
    id_allocator: IdAllocator,
    object_name: str,
) -> StateDef:
    s_id: Optional[str] = None
    initial = False
    description: Optional[str] = None
    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break
        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            s_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            id_allocator.reserve(s_id)
            continue
        if line == "initial":
            p.pop()
            initial = True
            continue
        parsed_description = _parse_optional_description_line(line)
        if parsed_description is not None:
            p.pop()
            description = parsed_description
            continue
        raise ProphetError(f"Unexpected state line {ln}: {line}")

    if s_id is None:
        s_id = id_allocator.generate(f"state_{object_name}_{name}")
    return StateDef(name=name, id=s_id, initial=initial, description=description, line=block_line)


def parse_transition_block(
    p: Parser,
    name: str,
    block_line: int,
    id_allocator: IdAllocator,
    object_name: str,
) -> TransitionDef:
    t_id: Optional[str] = None
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    fields: List[FieldDef] = []
    description: Optional[str] = None
    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break
        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            t_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            id_allocator.reserve(t_id)
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
        m = re.match(r"^field\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            fields.append(parse_field_block(p, m.group(1), ln, id_allocator, f"trans_{object_name}_{name}"))
            continue
        parsed_description = _parse_optional_description_line(line)
        if parsed_description is not None:
            p.pop()
            description = parsed_description
            continue
        raise ProphetError(f"Unexpected transition line {ln}: {line}")

    if from_state is None or to_state is None:
        raise ProphetError(f"Transition {name} missing from/to (line {block_line})")
    if t_id is None:
        t_id = id_allocator.generate(f"trans_{object_name}_{name}")
    return TransitionDef(
        name=name,
        id=t_id,
        from_state=from_state,
        to_state=to_state,
        fields=fields,
        description=description,
        line=block_line,
    )


def parse_action_shape_block(
    p: Parser,
    name: str,
    block_line: int,
    block_kind: str,
    id_allocator: IdAllocator,
) -> ActionShapeDef:
    shape_id: Optional[str] = None
    fields: List[FieldDef] = []
    description: Optional[str] = None
    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break
        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            shape_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            id_allocator.reserve(shape_id)
            continue
        m = re.match(r"^field\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            fields.append(parse_field_block(p, m.group(1), ln, id_allocator, f"shape_{name}"))
            continue
        parsed_description = _parse_optional_description_line(line)
        if parsed_description is not None:
            p.pop()
            description = parsed_description
            continue
        raise ProphetError(f"Unexpected {block_kind} line {ln}: {line}")

    if shape_id is None:
        shape_id = id_allocator.generate(f"shape_{name}")
    return ActionShapeDef(name=name, id=shape_id, fields=fields, description=description, line=block_line)


def parse_action_block(
    p: Parser,
    name: str,
    block_line: int,
    id_allocator: IdAllocator,
) -> Tuple[ActionDef, Optional[ActionShapeDef], Optional[EventDef]]:
    a_id: Optional[str] = None
    kind: Optional[str] = None
    input_shape: Optional[str] = None
    produces_event: Optional[str] = None
    description: Optional[str] = None
    inline_input: Optional[ActionShapeDef] = None
    inline_output_event: Optional[EventDef] = None
    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break
        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            a_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            id_allocator.reserve(a_id)
            continue
        m = re.match(r"^kind\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            kind = m.group(1)
            continue
        if line == "input {":
            p.pop()
            if input_shape is not None:
                raise ProphetError(f"Action {name} defines input more than once (line {ln})")
            input_shape = f"{_pascal_case(name)}Command"
            inline_input = parse_inline_action_shape_block(
                p,
                input_shape,
                ln,
                f"action {name} input",
                id_allocator,
                f"ain_{name}",
            )
            continue
        if line == "output {":
            p.pop()
            if produces_event is not None:
                raise ProphetError(f"Action {name} defines output more than once (line {ln})")
            produces_event = f"{_pascal_case(name)}Result"
            inline_output_event = parse_inline_signal_block(
                p,
                produces_event,
                ln,
                f"action {name} output",
                id_allocator,
                f"sig_action_{name}",
            )
            continue
        m = re.match(r"^output\s+signal\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            if produces_event is not None:
                raise ProphetError(f"Action {name} defines output more than once (line {ln})")
            produces_event = m.group(1)
            continue
        m = re.match(r"^output\s+transition\s+([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)$", line)
        if m:
            p.pop()
            if produces_event is not None:
                raise ProphetError(f"Action {name} defines output more than once (line {ln})")
            produces_event = transition_event_name(m.group(1), m.group(2))
            continue
        if line.startswith("input "):
            raise ProphetError(
                f"Action {name} input must be declared as 'input {{ ... }}' (line {ln})"
            )
        if line.startswith("output "):
            raise ProphetError(
                f"Action {name} output must be one of 'output {{ ... }}', 'output signal <SignalName>', or 'output transition <ObjectName>.<TransitionName>' (line {ln})"
            )
        parsed_description = _parse_optional_description_line(line)
        if parsed_description is not None:
            p.pop()
            description = parsed_description
            continue
        raise ProphetError(f"Unexpected action line {ln}: {line}")

    if kind is None or input_shape is None or produces_event is None:
        raise ProphetError(f"Action {name} missing kind/input/output (line {block_line})")
    if a_id is None:
        a_id = id_allocator.generate(f"act_{name}")
    return (
        ActionDef(
            name=name,
            id=a_id,
            kind=kind,
            input_shape=input_shape,
            produces_event=produces_event,
            description=description,
            line=block_line,
        ),
        inline_input,
        inline_output_event,
    )


def parse_inline_signal_block(
    p: Parser,
    signal_name: str,
    block_line: int,
    block_label: str,
    id_allocator: IdAllocator,
    id_base: str,
) -> EventDef:
    signal_id: Optional[str] = None
    fields: List[FieldDef] = []
    description: Optional[str] = None
    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break
        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            signal_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            id_allocator.reserve(signal_id)
            continue
        m = re.match(r"^field\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            fields.append(parse_field_block(p, m.group(1), ln, id_allocator, id_base))
            continue
        parsed_description = _parse_optional_description_line(line)
        if parsed_description is not None:
            p.pop()
            description = parsed_description
            continue
        raise ProphetError(f"Unexpected {block_label} line {ln}: {line}")

    if signal_id is None:
        signal_id = id_allocator.generate(id_base)
    return EventDef(
        name=signal_name,
        id=signal_id,
        kind="signal",
        fields=fields,
        description=description,
        line=block_line,
    )


def parse_inline_action_shape_block(
    p: Parser,
    shape_name: str,
    block_line: int,
    block_label: str,
    id_allocator: IdAllocator,
    id_base: str,
) -> ActionShapeDef:
    shape_id: Optional[str] = None
    fields: List[FieldDef] = []
    description: Optional[str] = None
    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break
        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            shape_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            id_allocator.reserve(shape_id)
            continue
        m = re.match(r"^field\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            fields.append(parse_field_block(p, m.group(1), ln, id_allocator, id_base))
            continue
        parsed_description = _parse_optional_description_line(line)
        if parsed_description is not None:
            p.pop()
            description = parsed_description
            continue
        raise ProphetError(f"Unexpected {block_label} line {ln}: {line}")

    if shape_id is None:
        shape_id = id_allocator.generate(id_base)
    return ActionShapeDef(
        name=shape_name,
        id=shape_id,
        fields=fields,
        description=description,
        line=block_line,
    )


def parse_signal_block(p: Parser, name: str, block_line: int, id_allocator: IdAllocator) -> EventDef:
    e_id: Optional[str] = None
    fields: List[FieldDef] = []
    description: Optional[str] = None
    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break
        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            e_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            id_allocator.reserve(e_id)
            continue
        m = re.match(r"^field\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$", line)
        if m:
            p.pop()
            fields.append(parse_field_block(p, m.group(1), ln, id_allocator, f"sig_{name}"))
            continue
        parsed_description = _parse_optional_description_line(line)
        if parsed_description is not None:
            p.pop()
            description = parsed_description
            continue
        raise ProphetError(f"Unexpected signal line {ln}: {line}")

    if e_id is None:
        e_id = id_allocator.generate(f"sig_{name}")
    return EventDef(
        name=name,
        id=e_id,
        kind="signal",
        fields=fields,
        description=description,
        line=block_line,
    )


def parse_trigger_block(p: Parser, name: str, block_line: int, id_allocator: IdAllocator) -> TriggerDef:
    t_id: Optional[str] = None
    event_name: Optional[str] = None
    action_name: Optional[str] = None
    description: Optional[str] = None
    while not p.eof():
        ln, line = p.peek()
        if line == "}":
            p.pop()
            break
        if re.match(r"^id\s+\".*\"$", line):
            _, row = p.pop()
            t_id = re.match(r'^id\s+\"(.*)\"$', row).group(1)  # type: ignore[union-attr]
            id_allocator.reserve(t_id)
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
        parsed_description = _parse_optional_description_line(line)
        if parsed_description is not None:
            p.pop()
            description = parsed_description
            continue
        raise ProphetError(f"Unexpected trigger line {ln}: {line}")

    if event_name is None or action_name is None:
        raise ProphetError(f"Trigger {name} missing when/invoke (line {block_line})")
    if t_id is None:
        t_id = id_allocator.generate(f"trg_{name}")
    return TriggerDef(
        name=name,
        id=t_id,
        event_name=event_name,
        action_name=action_name,
        description=description,
        line=block_line,
    )


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
