from __future__ import annotations

from pathlib import Path
from uuid import uuid4
import sys

from django.db import connection
from django.db import models

ROOT = Path(__file__).resolve().parents[2]
GEN_SRC = ROOT / "gen" / "python" / "src"
if str(GEN_SRC) not in sys.path:
    sys.path.insert(0, str(GEN_SRC))

from generated import django_models as Models
from generated.action_handlers import (
    ApproveOrderActionHandler,
    CreateOrderActionHandler,
    ActionContext,
    ActionHandlers,
    ShipOrderActionHandler,
)
from generated.action_service import ActionExecutionService
from generated.actions import (
    ApproveOrderCommand,
    ApproveOrderResult,
    CreateOrderCommand,
    CreateOrderResult,
    ShipOrderCommand,
    ShipOrderResult,
)
from generated.django_adapters import DjangoRepositories
from generated.django_views import configure_generated_views
from generated.domain import Order, OrderRef, User
from generated.events import EventEmitterNoOp

_INITIALIZED = False


class CreateOrderHandler(CreateOrderActionHandler):
    def handle(self, input: CreateOrderCommand, context: ActionContext) -> CreateOrderResult:
        context.repositories.user.save(
            User(
                userId=input.customer.userId,
                email=f"{input.customer.userId}@example.local",
            )
        )
        order_id = str(uuid4())
        context.repositories.order.save(
            Order(
                orderId=order_id,
                customer=input.customer,
                totalAmount=input.totalAmount,
                discountCode=input.discountCode,
                tags=input.tags,
                shippingAddress=input.shippingAddress,
                currentState="created",
            )
        )
        return CreateOrderResult(order=OrderRef(orderId=order_id), currentState="created")


class ApproveOrderHandler(ApproveOrderActionHandler):
    def handle(self, input: ApproveOrderCommand, context: ActionContext) -> ApproveOrderResult:
        existing = context.repositories.order.get_by_id(input.order)
        if existing is None:
            raise ValueError(f"order not found: {input.order.orderId}")
        context.repositories.order.save(
            Order(
                orderId=existing.orderId,
                customer=existing.customer,
                totalAmount=existing.totalAmount,
                discountCode=existing.discountCode,
                tags=existing.tags,
                shippingAddress=existing.shippingAddress,
                currentState="approved",
            )
        )
        warnings = ["notes_attached"] if input.notes else None
        return ApproveOrderResult(order=input.order, decision="approved", warnings=warnings)


class ShipOrderHandler(ShipOrderActionHandler):
    def handle(self, input: ShipOrderCommand, context: ActionContext) -> ShipOrderResult:
        existing = context.repositories.order.get_by_id(input.order)
        if existing is None:
            raise ValueError(f"order not found: {input.order.orderId}")
        context.repositories.order.save(
            Order(
                orderId=existing.orderId,
                customer=existing.customer,
                totalAmount=existing.totalAmount,
                discountCode=existing.discountCode,
                tags=existing.tags,
                shippingAddress=existing.shippingAddress,
                currentState="shipped",
            )
        )
        labels = [f"{input.carrier}-{package_id}" for package_id in input.packageIds]
        return ShipOrderResult(
            order=input.order,
            shipmentStatus="shipped",
            labels=labels,
            labelBatches=[input.packageIds],
        )


class ActionHandlers(ActionHandlers):
    createOrder: CreateOrderActionHandler
    approveOrder: ApproveOrderActionHandler
    shipOrder: ShipOrderActionHandler

    def __init__(self) -> None:
        self.createOrder = CreateOrderHandler()
        self.approveOrder = ApproveOrderHandler()
        self.shipOrder = ShipOrderHandler()


def _generated_model_classes() -> list[type[models.Model]]:
    result: list[type[models.Model]] = []
    for value in vars(Models).values():
        if isinstance(value, type) and issubclass(value, models.Model) and value is not models.Model:
            result.append(value)
    return sorted(result, key=lambda item: item.__name__)


def _ensure_generated_schema() -> None:
    existing_tables = set(connection.introspection.table_names())
    model_classes = _generated_model_classes()
    with connection.schema_editor() as schema_editor:
        for model_cls in model_classes:
            if model_cls._meta.db_table not in existing_tables:
                schema_editor.create_model(model_cls)


def initialize_generated_runtime() -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return

    _ensure_generated_schema()
    repositories = DjangoRepositories()
    event_emitter = EventEmitterNoOp()
    context = ActionContext(repositories=repositories, eventEmitter=event_emitter)
    service = ActionExecutionService(ActionHandlers(), event_emitter)
    configure_generated_views(service, context, repositories)
    _INITIALIZED = True
