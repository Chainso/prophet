# GENERATED FILE: do not edit directly.
from __future__ import annotations

import dataclasses
import json
import types

from typing import Any, Union, get_args, get_origin, get_type_hints

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .action_handlers import GeneratedActionContext
from .action_service import GeneratedActionExecutionService
from .actions import *
from .persistence import GeneratedRepositories
from .query import *

_service: GeneratedActionExecutionService | None = None
_context: GeneratedActionContext | None = None
_repositories: GeneratedRepositories | None = None

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

def configure_generated_views(service: GeneratedActionExecutionService, context: GeneratedActionContext, repositories: GeneratedRepositories) -> None:
    global _service, _context, _repositories
    _service = service
    _context = context
    _repositories = repositories

@csrf_exempt
def action_approveOrder(request: HttpRequest) -> HttpResponse:
    if request.method != 'POST':
        return JsonResponse({'error': 'method_not_allowed'}, status=405)
    payload = json.loads(request.body.decode('utf-8') or '{}')
    input_model = _coerce_value(ApproveOrderCommand, payload)
    if _service is None or _context is None:
        return JsonResponse({'error': 'generated_views_not_configured'}, status=500)
    result = _service.execute_approveOrder(input_model, _context)
    return JsonResponse(dataclasses.asdict(result))

@csrf_exempt
def action_createOrder(request: HttpRequest) -> HttpResponse:
    if request.method != 'POST':
        return JsonResponse({'error': 'method_not_allowed'}, status=405)
    payload = json.loads(request.body.decode('utf-8') or '{}')
    input_model = _coerce_value(CreateOrderCommand, payload)
    if _service is None or _context is None:
        return JsonResponse({'error': 'generated_views_not_configured'}, status=500)
    result = _service.execute_createOrder(input_model, _context)
    return JsonResponse(dataclasses.asdict(result))

@csrf_exempt
def action_shipOrder(request: HttpRequest) -> HttpResponse:
    if request.method != 'POST':
        return JsonResponse({'error': 'method_not_allowed'}, status=405)
    payload = json.loads(request.body.decode('utf-8') or '{}')
    input_model = _coerce_value(ShipOrderCommand, payload)
    if _service is None or _context is None:
        return JsonResponse({'error': 'generated_views_not_configured'}, status=500)
    result = _service.execute_shipOrder(input_model, _context)
    return JsonResponse(dataclasses.asdict(result))

def list_order(request: HttpRequest) -> HttpResponse:
    page = int(request.GET.get('page', '0'))
    size = int(request.GET.get('size', '20'))
    if _repositories is None:
        return JsonResponse({'error': 'generated_views_not_configured'}, status=500)
    result = _repositories.order.list(page, size)
    return JsonResponse(dataclasses.asdict(result))

def get_order(request: HttpRequest, id: str) -> HttpResponse:
    if _repositories is None:
        return JsonResponse({'error': 'generated_views_not_configured'}, status=500)
    item = _repositories.order.get_by_id(OrderRef(orderId=id))
    if item is None:
        return JsonResponse({'error': 'not_found'}, status=404)
    return JsonResponse(dataclasses.asdict(item))

@csrf_exempt
def query_order(request: HttpRequest) -> HttpResponse:
    if request.method != 'POST':
        return JsonResponse({'error': 'method_not_allowed'}, status=405)
    page = int(request.GET.get('page', '0'))
    size = int(request.GET.get('size', '20'))
    payload = json.loads(request.body.decode('utf-8') or '{}')
    filter_model = _coerce_value(OrderQueryFilter, payload)
    if _repositories is None:
        return JsonResponse({'error': 'generated_views_not_configured'}, status=500)
    result = _repositories.order.query(filter_model, page, size)
    return JsonResponse(dataclasses.asdict(result))

def list_user(request: HttpRequest) -> HttpResponse:
    page = int(request.GET.get('page', '0'))
    size = int(request.GET.get('size', '20'))
    if _repositories is None:
        return JsonResponse({'error': 'generated_views_not_configured'}, status=500)
    result = _repositories.user.list(page, size)
    return JsonResponse(dataclasses.asdict(result))

def get_user(request: HttpRequest, id: str) -> HttpResponse:
    if _repositories is None:
        return JsonResponse({'error': 'generated_views_not_configured'}, status=500)
    item = _repositories.user.get_by_id(UserRef(userId=id))
    if item is None:
        return JsonResponse({'error': 'not_found'}, status=404)
    return JsonResponse(dataclasses.asdict(item))

@csrf_exempt
def query_user(request: HttpRequest) -> HttpResponse:
    if request.method != 'POST':
        return JsonResponse({'error': 'method_not_allowed'}, status=405)
    page = int(request.GET.get('page', '0'))
    size = int(request.GET.get('size', '20'))
    payload = json.loads(request.body.decode('utf-8') or '{}')
    filter_model = _coerce_value(UserQueryFilter, payload)
    if _repositories is None:
        return JsonResponse({'error': 'generated_views_not_configured'}, status=500)
    result = _repositories.user.query(filter_model, page, size)
    return JsonResponse(dataclasses.asdict(result))
