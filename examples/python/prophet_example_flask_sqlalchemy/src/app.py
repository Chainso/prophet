from __future__ import annotations

from pathlib import Path
from uuid import uuid4
import sys

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
GEN_SRC = ROOT / "gen" / "python" / "src"
if str(GEN_SRC) not in sys.path:
    sys.path.insert(0, str(GEN_SRC))

from generated import sqlalchemy_models as SqlAlchemyModels
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
    CreateOrderCommand,
    ShipOrderCommand,
)
from generated.domain import Order, OrderRef, OrderStatus, User
from generated.event_contracts import CreateOrderResult, OrderApproved, OrderShipped
from generated.events import EventPublisherNoOp
from generated.flask_routes import build_generated_blueprint
from generated.sqlalchemy_adapters import SqlAlchemyRepositories


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
                status=OrderStatus.Created,
            )
        )
        return CreateOrderResult(order=OrderRef(orderId=order_id))


class ApproveOrderHandler(ApproveOrderActionHandler):
    def handle(self, input: ApproveOrderCommand, context: ActionContext) -> OrderApproved:
        existing = context.repositories.order.get_by_id(input.order)
        if existing is None:
            raise ValueError(f"order not found: {input.order.orderId}")

        saved_order = context.repositories.order.save(
            Order(
                orderId=existing.orderId,
                customer=existing.customer,
                totalAmount=existing.totalAmount,
                discountCode=existing.discountCode,
                tags=existing.tags,
                shippingAddress=existing.shippingAddress,
                approvedByUserId=input.approvedBy.userId if input.approvedBy else None,
                approvalNotes=input.notes,
                approvalReason=input.context.reason if input.context else None,
                shippingCarrier=existing.shippingCarrier,
                shippingTrackingNumber=existing.shippingTrackingNumber,
                shippingPackageIds=existing.shippingPackageIds,
                status=OrderStatus.Approved,
            )
        )
        return OrderApproved(order=OrderRef(orderId=saved_order.orderId))


class ShipOrderHandler(ShipOrderActionHandler):
    def handle(self, input: ShipOrderCommand, context: ActionContext) -> OrderShipped:
        existing = context.repositories.order.get_by_id(input.order)
        if existing is None:
            raise ValueError(f"order not found: {input.order.orderId}")

        saved_order = context.repositories.order.save(
            Order(
                orderId=existing.orderId,
                customer=existing.customer,
                totalAmount=existing.totalAmount,
                discountCode=existing.discountCode,
                tags=existing.tags,
                shippingAddress=existing.shippingAddress,
                approvedByUserId=existing.approvedByUserId,
                approvalNotes=existing.approvalNotes,
                approvalReason=existing.approvalReason,
                shippingCarrier=input.carrier,
                shippingTrackingNumber=input.trackingNumber,
                shippingPackageIds=input.packageIds,
                status=OrderStatus.Shipped,
            )
        )
        return OrderShipped(order=OrderRef(orderId=saved_order.orderId))


class ActionHandlers(ActionHandlers):
    createOrder: CreateOrderActionHandler
    approveOrder: ApproveOrderActionHandler
    shipOrder: ShipOrderActionHandler

    def __init__(self) -> None:
        self.createOrder = CreateOrderHandler()
        self.approveOrder = ApproveOrderHandler()
        self.shipOrder = ShipOrderHandler()


DB_PATH = ROOT / "dev.db"
if DB_PATH.exists():
    DB_PATH.unlink()

engine = create_engine(f"sqlite:///{DB_PATH}", future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
SqlAlchemyModels.Base.metadata.create_all(engine)

repositories = SqlAlchemyRepositories(lambda: SessionLocal())
event_publisher = EventPublisherNoOp()
context = ActionContext(repositories=repositories, eventPublisher=event_publisher)
service = ActionExecutionService(ActionHandlers())

app = Flask(__name__)
app.register_blueprint(build_generated_blueprint(service, context, repositories))
