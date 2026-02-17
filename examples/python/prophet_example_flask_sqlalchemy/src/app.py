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
from generated.domain import Order, OrderRef, User
from generated.event_contracts import CreateOrderResult, OrderApproveTransition, OrderShipTransition
from generated.events import EventPublisherNoOp
from generated.flask_routes import build_generated_blueprint
from generated.sqlalchemy_adapters import SqlAlchemyRepositories
from generated.transitions import TransitionServices


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
                state="created",
            )
        )
        return CreateOrderResult(order=OrderRef(orderId=order_id))


class ApproveOrderHandler(ApproveOrderActionHandler):
    def handle(self, input: ApproveOrderCommand, context: ActionContext) -> OrderApproveTransition:
        existing = context.repositories.order.get_by_id(input.order)
        if existing is None:
            raise ValueError(f"order not found: {input.order.orderId}")
        transitions = TransitionServices(context.repositories)
        draft = transitions.order.approveOrder(input.order)
        return draft.build()


class ShipOrderHandler(ShipOrderActionHandler):
    def handle(self, input: ShipOrderCommand, context: ActionContext) -> OrderShipTransition:
        existing = context.repositories.order.get_by_id(input.order)
        if existing is None:
            raise ValueError(f"order not found: {input.order.orderId}")
        transitions = TransitionServices(context.repositories)
        draft = transitions.order.shipOrder(input.order)
        return draft.build()


class ActionHandlers(ActionHandlers):
    createOrder: CreateOrderActionHandler
    approveOrder: ApproveOrderActionHandler
    shipOrder: ShipOrderActionHandler

    def __init__(self) -> None:
        self.createOrder = CreateOrderHandler()
        self.approveOrder = ApproveOrderHandler()
        self.shipOrder = ShipOrderHandler()


engine = create_engine("sqlite:///./dev.db", future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
SqlAlchemyModels.Base.metadata.create_all(engine)

repositories = SqlAlchemyRepositories(lambda: SessionLocal())
event_publisher = EventPublisherNoOp()
context = ActionContext(repositories=repositories, eventPublisher=event_publisher)
service = ActionExecutionService(ActionHandlers())

app = Flask(__name__)
app.register_blueprint(build_generated_blueprint(service, context, repositories))
