from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(kw_only=True)
class EventWireEnvelope:
    event_id: str
    trace_id: str
    event_type: str
    schema_version: str
    occurred_at: str
    source: str
    payload: Dict[str, object]
    attributes: Optional[Dict[str, str]] = None
    updated_objects: Optional[List[Dict[str, object]]] = None
