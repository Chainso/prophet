from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from .constants import BASE_TYPES
from .errors import ProphetError
from .models import ActionDef
from .models import ActionShapeDef
from .models import EventDef
from .models import FieldDef
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

