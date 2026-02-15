# GENERATED FILE: do not edit directly.
from __future__ import annotations

from typing import Protocol

from .actions import *
from .event_contracts import *

class GeneratedEventEmitter(Protocol):
    async def emit_approve_order_result(self, event: ApproveOrderResult) -> None: ...
    async def emit_create_order_result(self, event: CreateOrderResult) -> None: ...
    async def emit_ship_order_result(self, event: ShipOrderResult) -> None: ...
    async def emit_payment_captured(self, event: PaymentCaptured) -> None: ...
    async def emit_order_approve_transition(self, event: OrderApproveTransition) -> None: ...
    async def emit_order_ship_transition(self, event: OrderShipTransition) -> None: ...

class GeneratedEventEmitterNoOp:
    async def emit_approve_order_result(self, event: ApproveOrderResult) -> None:
        return None
    async def emit_create_order_result(self, event: CreateOrderResult) -> None:
        return None
    async def emit_ship_order_result(self, event: ShipOrderResult) -> None:
        return None
    async def emit_payment_captured(self, event: PaymentCaptured) -> None:
        return None
    async def emit_order_approve_transition(self, event: OrderApproveTransition) -> None:
        return None
    async def emit_order_ship_transition(self, event: OrderShipTransition) -> None:
        return None
