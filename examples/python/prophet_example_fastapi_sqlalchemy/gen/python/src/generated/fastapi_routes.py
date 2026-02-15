# GENERATED FILE: do not edit directly.
from __future__ import annotations

import dataclasses

from fastapi import APIRouter, HTTPException, Query

from .action_handlers import GeneratedActionContext
from .action_service import GeneratedActionExecutionService
from .actions import *
from .persistence import GeneratedRepositories

def build_generated_router(service: GeneratedActionExecutionService, context: GeneratedActionContext, repositories: GeneratedRepositories) -> APIRouter:
    router = APIRouter()

    @router.post('/actions/approveOrder')
    async def action_approveOrder(payload: dict):
        input_model = ApproveOrderCommand(**(payload or {}))
        result = await service.execute_approveOrder(input_model, context)
        return dataclasses.asdict(result)

    @router.post('/actions/createOrder')
    async def action_createOrder(payload: dict):
        input_model = CreateOrderCommand(**(payload or {}))
        result = await service.execute_createOrder(input_model, context)
        return dataclasses.asdict(result)

    @router.post('/actions/shipOrder')
    async def action_shipOrder(payload: dict):
        input_model = ShipOrderCommand(**(payload or {}))
        result = await service.execute_shipOrder(input_model, context)
        return dataclasses.asdict(result)

    @router.get('/orders')
    async def list_order(page: int = Query(default=0), size: int = Query(default=20)):
        result = await repositories.order.list(page, size)
        return dataclasses.asdict(result)

    @router.get('/orders/{id}')
    async def get_order(id: str):
        item = await repositories.order.get_by_id(OrderRef(orderId=id))
        if item is None:
            raise HTTPException(status_code=404, detail='not_found')
        return dataclasses.asdict(item)

    @router.post('/orders/query')
    async def query_order(payload: dict, page: int = Query(default=0), size: int = Query(default=20)):
        filter_model = OrderQueryFilter(**(payload or {}))
        result = await repositories.order.query(filter_model, page, size)
        return dataclasses.asdict(result)

    @router.get('/users')
    async def list_user(page: int = Query(default=0), size: int = Query(default=20)):
        result = await repositories.user.list(page, size)
        return dataclasses.asdict(result)

    @router.get('/users/{id}')
    async def get_user(id: str):
        item = await repositories.user.get_by_id(UserRef(userId=id))
        if item is None:
            raise HTTPException(status_code=404, detail='not_found')
        return dataclasses.asdict(item)

    @router.post('/users/query')
    async def query_user(payload: dict, page: int = Query(default=0), size: int = Query(default=20)):
        filter_model = UserQueryFilter(**(payload or {}))
        result = await repositories.user.query(filter_model, page, size)
        return dataclasses.asdict(result)

    return router
