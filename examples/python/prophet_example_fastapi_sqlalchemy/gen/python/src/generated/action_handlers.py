# GENERATED FILE: do not edit directly.
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .actions import *
from .events import GeneratedEventEmitter
from .persistence import GeneratedRepositories

@dataclass
class GeneratedActionContext:
    repositories: GeneratedRepositories
    eventEmitter: GeneratedEventEmitter

class ApproveOrderActionHandler(Protocol):
    async def handle(self, input: ApproveOrderCommand, context: GeneratedActionContext) -> ApproveOrderResult: ...

class ApproveOrderActionHandlerDefault:
    async def handle(self, input: ApproveOrderCommand, context: GeneratedActionContext) -> ApproveOrderResult:
        raise NotImplementedError('No implementation registered for action: approveOrder')

class CreateOrderActionHandler(Protocol):
    async def handle(self, input: CreateOrderCommand, context: GeneratedActionContext) -> CreateOrderResult: ...

class CreateOrderActionHandlerDefault:
    async def handle(self, input: CreateOrderCommand, context: GeneratedActionContext) -> CreateOrderResult:
        raise NotImplementedError('No implementation registered for action: createOrder')

class ShipOrderActionHandler(Protocol):
    async def handle(self, input: ShipOrderCommand, context: GeneratedActionContext) -> ShipOrderResult: ...

class ShipOrderActionHandlerDefault:
    async def handle(self, input: ShipOrderCommand, context: GeneratedActionContext) -> ShipOrderResult:
        raise NotImplementedError('No implementation registered for action: shipOrder')

class GeneratedActionHandlers(Protocol):
    approveOrder: ApproveOrderActionHandler
    createOrder: CreateOrderActionHandler
    shipOrder: ShipOrderActionHandler
