# GENERATED FILE: do not edit directly.
from __future__ import annotations

import dataclasses
import types

from typing import Any, Union, get_args, get_origin, get_type_hints

from fastapi import APIRouter, HTTPException, Query

from .action_handlers import GeneratedActionContext
from .action_service import GeneratedActionExecutionService
from .actions import *
from .persistence import GeneratedRepositories
from .query import *

_TYPE_HINT_CACHE: dict[type, dict[str, Any]] = {}

def _coerce_value(expected_type: Any, value: Any) -> Any:
    if value is None:
        return None
    origin = get_origin(expected_type)
    if origin is list:
        (item_type,) = get_args(expected_type) or (Any,)
        if not isinstance(value, list):
            return value
        return [_coerce_value(item_type, item) for item in value]
    if origin is dict:
        return value
    if origin in (types.UnionType, Union):
        args = [item for item in get_args(expected_type) if item is not type(None)]
        if len(args) == 1:
            return _coerce_value(args[0], value)
        for arg in args:
            try:
                return _coerce_value(arg, value)
            except Exception:
                continue
        return value
    if isinstance(expected_type, type) and dataclasses.is_dataclass(expected_type):
        if isinstance(value, expected_type):
            return value
        if not isinstance(value, dict):
            return value
        hints = _TYPE_HINT_CACHE.get(expected_type)
        if hints is None:
            hints = get_type_hints(expected_type, globalns=globals(), localns=globals())
            _TYPE_HINT_CACHE[expected_type] = hints
        kwargs: dict[str, Any] = {}
        for field in dataclasses.fields(expected_type):
            if field.name in value:
                field_type = hints.get(field.name, Any)
                kwargs[field.name] = _coerce_value(field_type, value[field.name])
        return expected_type(**kwargs)
    return value

def build_generated_router(service: GeneratedActionExecutionService, context: GeneratedActionContext, repositories: GeneratedRepositories) -> APIRouter:
    router = APIRouter()

    @router.post('/actions/approveOrder')
    async def action_approveOrder(payload: dict):
        input_model = _coerce_value(ApproveOrderCommand, payload or {})
        result = await service.execute_approveOrder(input_model, context)
        return dataclasses.asdict(result)

    @router.post('/actions/createOrder')
    async def action_createOrder(payload: dict):
        input_model = _coerce_value(CreateOrderCommand, payload or {})
        result = await service.execute_createOrder(input_model, context)
        return dataclasses.asdict(result)

    @router.post('/actions/shipOrder')
    async def action_shipOrder(payload: dict):
        input_model = _coerce_value(ShipOrderCommand, payload or {})
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
        filter_model = _coerce_value(OrderQueryFilter, payload or {})
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
        filter_model = _coerce_value(UserQueryFilter, payload or {})
        result = await repositories.user.query(filter_model, page, size)
        return dataclasses.asdict(result)

    return router
