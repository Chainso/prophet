from __future__ import annotations

from pathlib import Path
from uuid import uuid4
import sys

from fastapi import FastAPI
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
    CreateOrderCommand,
    ShipOrderCommand,
)
from generated.domain import Order, OrderRef, User
from generated.event_contracts import CreateOrderResult, OrderApproveTransition, OrderShipTransition
from generated.events import EventPublisherNoOp
from generated.fastapi_routes import build_generated_router
from generated.sqlmodel_adapters import SqlModelRepositories
from generated.transitions import TransitionServices


class CreateOrderHandler(CreateOrderActionHandler):
    async def handle(self, input: CreateOrderCommand, context: ActionContext) -> CreateOrderResult:
        await context.repositories.user.save(
            User(
                userId=input.customer.userId,
                email=f"{input.customer.userId}@example.local",
            )
        )
        order_id = str(uuid4())
        await context.repositories.order.save(
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
    async def handle(self, input: ApproveOrderCommand, context: ActionContext) -> OrderApproveTransition:
        existing = await context.repositories.order.get_by_id(input.order)
        if existing is None:
            raise ValueError(f"order not found: {input.order.orderId}")

        saved_order = await context.repositories.order.save(
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
                state=existing.state,
            )
        )
        transitions = TransitionServices(context.repositories)
        draft = await transitions.order.approveOrder(saved_order)
        return draft.build(
            approvedByUserId=saved_order.approvedByUserId,
            noteCount=len(input.notes or []),
            approvalReason=saved_order.approvalReason,
        )


class ShipOrderHandler(ShipOrderActionHandler):
    async def handle(self, input: ShipOrderCommand, context: ActionContext) -> OrderShipTransition:
        existing = await context.repositories.order.get_by_id(input.order)
        if existing is None:
            raise ValueError(f"order not found: {input.order.orderId}")

        saved_order = await context.repositories.order.save(
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
                state=existing.state,
            )
        )
        transitions = TransitionServices(context.repositories)
        draft = await transitions.order.shipOrder(saved_order)
        return draft.build(
            carrier=input.carrier,
            trackingNumber=input.trackingNumber,
            packageIds=input.packageIds,
        )


class ActionHandlers(ActionHandlers):
    createOrder: CreateOrderActionHandler
    approveOrder: ApproveOrderActionHandler
    shipOrder: ShipOrderActionHandler

    def __init__(self) -> None:
        self.createOrder = CreateOrderHandler()
        self.approveOrder = ApproveOrderHandler()
        self.shipOrder = ShipOrderHandler()


engine = create_engine("sqlite:///./dev.db", connect_args={"check_same_thread": False})
SqlModelModels.SQLModel.metadata.create_all(engine)

repositories = SqlModelRepositories(lambda: Session(engine))
event_publisher = EventPublisherNoOp()
context = ActionContext(repositories=repositories, eventPublisher=event_publisher)
service = ActionExecutionService(ActionHandlers())

app = FastAPI(title="prophet_example_fastapi_sqlmodel")
app.include_router(build_generated_router(service, context, repositories))
