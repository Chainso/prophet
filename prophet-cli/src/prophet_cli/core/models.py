from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TypeDef:
    name: str
    id: str
    base: str
    constraints: Dict[str, str]
    description: Optional[str]
    line: int
    display_name: Optional[str] = None


@dataclass
class FieldDef:
    name: str
    id: str
    type_raw: str
    required: bool
    key: Optional[str]
    description: Optional[str]
    line: int
    display_name: Optional[str] = None


@dataclass
class StateDef:
    name: str
    id: str
    initial: bool
    description: Optional[str]
    line: int
    display_name: Optional[str] = None


@dataclass
class TransitionDef:
    name: str
    id: str
    from_state: str
    to_state: str
    fields: List[FieldDef]
    description: Optional[str]
    line: int
    display_name: Optional[str] = None


@dataclass
class KeyDef:
    kind: str
    field_names: List[str]
    line: int


@dataclass
class ObjectDef:
    name: str
    id: str
    fields: List[FieldDef]
    keys: List[KeyDef]
    states: List[StateDef]
    transitions: List[TransitionDef]
    description: Optional[str]
    line: int
    display_name: Optional[str] = None


@dataclass
class StructDef:
    name: str
    id: str
    fields: List[FieldDef]
    description: Optional[str]
    line: int
    display_name: Optional[str] = None


@dataclass
class ActionDef:
    name: str
    id: str
    kind: str
    input_shape: str
    produces_event: str
    description: Optional[str]
    line: int
    display_name: Optional[str] = None


@dataclass
class ActionShapeDef:
    name: str
    id: str
    fields: List[FieldDef]
    description: Optional[str]
    line: int
    display_name: Optional[str] = None


@dataclass
class EventDef:
    name: str
    id: str
    kind: str
    fields: List[FieldDef]
    description: Optional[str]
    line: int
    display_name: Optional[str] = None


@dataclass
class TriggerDef:
    name: str
    id: str
    event_name: str
    action_name: str
    description: Optional[str]
    line: int
    display_name: Optional[str] = None


@dataclass
class Ontology:
    name: str
    id: str
    version: str
    description: Optional[str] = None
    display_name: Optional[str] = None
    types: List[TypeDef] = field(default_factory=list)
    objects: List[ObjectDef] = field(default_factory=list)
    structs: List[StructDef] = field(default_factory=list)
    action_inputs: List[ActionShapeDef] = field(default_factory=list)
    actions: List[ActionDef] = field(default_factory=list)
    events: List[EventDef] = field(default_factory=list)
    triggers: List[TriggerDef] = field(default_factory=list)
