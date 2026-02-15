from __future__ import annotations

from pathlib import Path
from uuid import uuid4
import sys

from fastapi import FastAPI
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
    GeneratedActionContext,
    GeneratedActionHandlers,
    ShipOrderActionHandler,
)
from generated.action_service import GeneratedActionExecutionService
from generated.actions import (
    ApproveOrderCommand,
    ApproveOrderResult,
    CreateOrderCommand,
    CreateOrderResult,
    ShipOrderCommand,
    ShipOrderResult,
)
from generated.domain import Order, OrderRef, User
from generated.events import GeneratedEventEmitterNoOp
from generated.fastapi_routes import build_generated_router
from generated.sqlalchemy_adapters import SqlAlchemyGeneratedRepositories


class CreateOrderHandler(CreateOrderActionHandler):
    async def handle(self, input: CreateOrderCommand, context: GeneratedActionContext) -> CreateOrderResult:
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
                currentState="created",
            )
        )
        return CreateOrderResult(order=OrderRef(orderId=order_id), currentState="created")


class ApproveOrderHandler(ApproveOrderActionHandler):
    async def handle(self, input: ApproveOrderCommand, context: GeneratedActionContext) -> ApproveOrderResult:
        existing = await context.repositories.order.get_by_id(input.order)
        if existing is None:
            raise ValueError(f"order not found: {input.order.orderId}")
        await context.repositories.order.save(
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
    async def handle(self, input: ShipOrderCommand, context: GeneratedActionContext) -> ShipOrderResult:
        existing = await context.repositories.order.get_by_id(input.order)
        if existing is None:
            raise ValueError(f"order not found: {input.order.orderId}")
        await context.repositories.order.save(
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


class ActionHandlers(GeneratedActionHandlers):
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

repositories = SqlAlchemyGeneratedRepositories(lambda: SessionLocal())
event_emitter = GeneratedEventEmitterNoOp()
context = GeneratedActionContext(repositories=repositories, eventEmitter=event_emitter)
service = GeneratedActionExecutionService(ActionHandlers(), event_emitter)

app = FastAPI(title="prophet_example_fastapi_sqlalchemy")
app.include_router(build_generated_router(service, context, repositories))
