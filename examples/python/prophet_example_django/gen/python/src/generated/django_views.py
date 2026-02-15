# GENERATED FILE: do not edit directly.
from __future__ import annotations

import dataclasses
import json

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .action_handlers import GeneratedActionContext
from .action_service import GeneratedActionExecutionService
from .actions import *
from .persistence import GeneratedRepositories

_service: GeneratedActionExecutionService | None = None
_context: GeneratedActionContext | None = None
_repositories: GeneratedRepositories | None = None

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
    input_model = ApproveOrderCommand(**payload)
    if _service is None or _context is None:
        return JsonResponse({'error': 'generated_views_not_configured'}, status=500)
    result = _service.execute_approveOrder(input_model, _context)
    return JsonResponse(dataclasses.asdict(result))

@csrf_exempt
def action_createOrder(request: HttpRequest) -> HttpResponse:
    if request.method != 'POST':
        return JsonResponse({'error': 'method_not_allowed'}, status=405)
    payload = json.loads(request.body.decode('utf-8') or '{}')
    input_model = CreateOrderCommand(**payload)
    if _service is None or _context is None:
        return JsonResponse({'error': 'generated_views_not_configured'}, status=500)
    result = _service.execute_createOrder(input_model, _context)
    return JsonResponse(dataclasses.asdict(result))

@csrf_exempt
def action_shipOrder(request: HttpRequest) -> HttpResponse:
    if request.method != 'POST':
        return JsonResponse({'error': 'method_not_allowed'}, status=405)
    payload = json.loads(request.body.decode('utf-8') or '{}')
    input_model = ShipOrderCommand(**payload)
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
    filter_model = OrderQueryFilter(**payload)
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
    filter_model = UserQueryFilter(**payload)
    if _repositories is None:
        return JsonResponse({'error': 'generated_views_not_configured'}, status=500)
    result = _repositories.user.query(filter_model, page, size)
    return JsonResponse(dataclasses.asdict(result))
