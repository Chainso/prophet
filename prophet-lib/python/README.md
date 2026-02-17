<p align="center">
  <img src="https://raw.githubusercontent.com/Chainso/prophet/main/brand/exports/logo-horizontal-color.png" alt="Prophet logo" />
</p>

---

# prophet-events-runtime

`prophet-events-runtime` is the shared Python runtime contract used by Prophet-generated action services.

Main project repository:
- https://github.com/Chainso/prophet

It defines:
- an async `EventPublisher` protocol
- a canonical `EventWireEnvelope` dataclass
- `TransitionValidationResult` for generated transition-validator hooks
- utility helpers (`create_event_id`, `now_iso`)
- sync bridge helpers (`publish_sync`, `publish_batch_sync`)
- a `NoOpEventPublisher` for local wiring and tests

## Install

```bash
python3 -m pip install prophet-events-runtime
```

## API

```python
from typing import Iterable, Protocol

class EventPublisher(Protocol):
    async def publish(self, envelope: EventWireEnvelope) -> None: ...
    async def publish_batch(self, envelopes: Iterable[EventWireEnvelope]) -> None: ...
```

```python
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
```

Exports:
- `EventPublisher`
- `EventWireEnvelope`
- `NoOpEventPublisher`
- `create_event_id()`
- `now_iso()`
- `publish_sync(publisher, envelope)`
- `publish_batch_sync(publisher, envelopes)`
- `TransitionValidationResult`

## Implement a Platform Publisher

```python
from __future__ import annotations

from typing import Iterable

from prophet_events_runtime import EventPublisher
from prophet_events_runtime import EventWireEnvelope


class PlatformClient:
    async def send_event(self, payload: dict) -> None: ...
    async def send_events(self, payloads: list[dict]) -> None: ...


class PlatformEventPublisher(EventPublisher):
    def __init__(self, client: PlatformClient) -> None:
        self._client = client

    async def publish(self, envelope: EventWireEnvelope) -> None:
        await self._client.send_event(envelope.__dict__)

    async def publish_batch(self, envelopes: Iterable[EventWireEnvelope]) -> None:
        await self._client.send_events([envelope.__dict__ for envelope in envelopes])
```

## With Prophet-Generated Code

Generated Python action services publish event wire envelopes after successful handler execution.
If you do not provide an implementation, you can wire `NoOpEventPublisher` for local development.

## Local Validation

From repository root:

```bash
PYTHONPATH=prophet-lib/python/src python3 -m unittest discover -s prophet-lib/python/tests -p 'test_*.py' -v
python3 -m pip install --upgrade build twine
python3 -m build prophet-lib/python
python3 -m twine check prophet-lib/python/dist/*
```

## More Information

- Main repository README: https://github.com/Chainso/prophet#readme
- Runtime index: https://github.com/Chainso/prophet/tree/main/prophet-lib
- Event wire contract: https://github.com/Chainso/prophet/tree/main/prophet-lib/specs/wire-contract.md
- Event wire JSON schema: https://github.com/Chainso/prophet/tree/main/prophet-lib/specs/wire-event-envelope.schema.json
- Python integration reference: https://github.com/Chainso/prophet/tree/main/docs/reference/python.md
- Example app: https://github.com/Chainso/prophet/tree/main/examples/python/prophet_example_fastapi_sqlalchemy
