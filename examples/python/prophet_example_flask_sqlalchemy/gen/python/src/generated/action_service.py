# GENERATED FILE: do not edit directly.
from __future__ import annotations

from .action_handlers import GeneratedActionContext
from .action_handlers import GeneratedActionHandlers
from .actions import *
from .events import GeneratedEventEmitter

class GeneratedActionExecutionService:
    def __init__(self, handlers: GeneratedActionHandlers, eventEmitter: GeneratedEventEmitter):
        self.handlers = handlers
        self.eventEmitter = eventEmitter

    def execute_approveOrder(self, input: ApproveOrderCommand, context: GeneratedActionContext) -> ApproveOrderResult:
        output = self.handlers.approveOrder.handle(input, context)
        self.eventEmitter.emit_approve_order_result(output)
        return output

    def execute_createOrder(self, input: CreateOrderCommand, context: GeneratedActionContext) -> CreateOrderResult:
        output = self.handlers.createOrder.handle(input, context)
        self.eventEmitter.emit_create_order_result(output)
        return output

    def execute_shipOrder(self, input: ShipOrderCommand, context: GeneratedActionContext) -> ShipOrderResult:
        output = self.handlers.shipOrder.handle(input, context)
        self.eventEmitter.emit_ship_order_result(output)
        return output
