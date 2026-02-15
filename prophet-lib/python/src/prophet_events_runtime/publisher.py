from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Iterable, Protocol
from uuid import uuid4

from .wire import EventWireEnvelope


class EventPublisher(Protocol):
    async def publish(self, envelope: EventWireEnvelope) -> None: ...

    async def publish_batch(self, envelopes: Iterable[EventWireEnvelope]) -> None: ...


class NoOpEventPublisher:
    async def publish(self, envelope: EventWireEnvelope) -> None:
        return None

    async def publish_batch(self, envelopes: Iterable[EventWireEnvelope]) -> None:
        return None


def create_event_id() -> str:
    return str(uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_async(coro: object) -> None:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(coro)  # type: ignore[arg-type]
        return
    raise RuntimeError("Cannot use sync publish helper while an event loop is running")


def publish_sync(publisher: EventPublisher, envelope: EventWireEnvelope) -> None:
    _run_async(publisher.publish(envelope))


def publish_batch_sync(publisher: EventPublisher, envelopes: Iterable[EventWireEnvelope]) -> None:
    _run_async(publisher.publish_batch(envelopes))
