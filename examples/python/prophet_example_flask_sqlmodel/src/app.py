from __future__ import annotations

from pathlib import Path
from uuid import uuid4
import sys

from flask import Flask
from sqlmodel import Session, create_engine

ROOT = Path(__file__).resolve().parents[1]
GEN_SRC = ROOT / "gen" / "python" / "src"
if str(GEN_SRC) not in sys.path:
    sys.path.insert(0, str(GEN_SRC))

from generated import sqlmodel_models as SqlModelModels
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
from generated.domain import Order, OrderRef, User
from generated.events import EventPublisherNoOp
from generated.flask_routes import build_generated_blueprint
from generated.sqlmodel_adapters import SqlModelRepositories


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


engine = create_engine("sqlite:///./dev.db")
SqlModelModels.SQLModel.metadata.create_all(engine)

repositories = SqlModelRepositories(lambda: Session(engine))
event_publisher = EventPublisherNoOp()
context = ActionContext(repositories=repositories, eventPublisher=event_publisher)
service = ActionExecutionService(ActionHandlers())

app = Flask(__name__)
app.register_blueprint(build_generated_blueprint(service, context, repositories))
