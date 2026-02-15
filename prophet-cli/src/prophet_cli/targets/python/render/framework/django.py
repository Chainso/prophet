from __future__ import annotations

from typing import Any, Dict, List

from ..support import _camel_case
from ..support import _object_primary_key_fields
from ..support import _pascal_case
from ..support import _sort_dict_entries


def _django_path(path: str) -> str:
    return path.replace("{id}", "<str:id>")


def render_django_views(ir: Dict[str, Any]) -> str:
    action_input_by_id = {item["id"]: item for item in ir.get("action_inputs", []) if isinstance(item, dict) and "id" in item}
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}

    lines: List[str] = [
        "# GENERATED FILE: do not edit directly.",
        "from __future__ import annotations",
        "",
        "import dataclasses",
        "import json",
        "",
        "from django.http import HttpRequest, HttpResponse, JsonResponse",
        "from django.views.decorators.csrf import csrf_exempt",
        "",
        "from .action_handlers import GeneratedActionContext",
        "from .action_service import GeneratedActionExecutionService",
        "from .actions import *",
        "from .persistence import GeneratedRepositories",
        "",
        "_service: GeneratedActionExecutionService | None = None",
        "_context: GeneratedActionContext | None = None",
        "_repositories: GeneratedRepositories | None = None",
        "",
        "def configure_generated_views(service: GeneratedActionExecutionService, context: GeneratedActionContext, repositories: GeneratedRepositories) -> None:",
        "    global _service, _context, _repositories",
        "    _service = service",
        "    _context = context",
        "    _repositories = repositories",
        "",
    ]

    for action in _sort_dict_entries([item for item in ir.get("actions", []) if isinstance(item, dict)]):
        action_name = str(action.get("name", "action"))
        camel = _camel_case(action_name)
        input_shape = action_input_by_id.get(str(action.get("input_shape_id", "")), {})
        input_name = _pascal_case(str(input_shape.get("name", "ActionInput")))
        lines.append("@csrf_exempt")
        lines.append(f"def action_{camel}(request: HttpRequest) -> HttpResponse:")
        lines.append("    if request.method != 'POST':")
        lines.append("        return JsonResponse({'error': 'method_not_allowed'}, status=405)")
        lines.append("    payload = json.loads(request.body.decode('utf-8') or '{}')")
        lines.append(f"    input_model = {input_name}(**payload)")
        lines.append("    if _service is None or _context is None:")
        lines.append("        return JsonResponse({'error': 'generated_views_not_configured'}, status=500)")
        lines.append(f"    result = _service.execute_{camel}(input_model, _context)")
        lines.append("    return JsonResponse(dataclasses.asdict(result))")
        lines.append("")

    for contract in _sort_dict_entries([item for item in ir.get("query_contracts", []) if isinstance(item, dict)]):
        object_id = str(contract.get("object_id", ""))
        obj = object_by_id.get(object_id, {})
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        repo_name = _camel_case(obj_name)
        query_filter_name = f"{obj_name}QueryFilter"

        lines.append(f"def list_{repo_name}(request: HttpRequest) -> HttpResponse:")
        lines.append("    page = int(request.GET.get('page', '0'))")
        lines.append("    size = int(request.GET.get('size', '20'))")
        lines.append("    if _repositories is None:")
        lines.append("        return JsonResponse({'error': 'generated_views_not_configured'}, status=500)")
        lines.append(f"    result = _repositories.{repo_name}.list(page, size)")
        lines.append("    return JsonResponse(dataclasses.asdict(result))")
        lines.append("")

        pk_fields = _object_primary_key_fields(obj)
        lines.append(f"def get_{repo_name}(request: HttpRequest, id: str) -> HttpResponse:")
        lines.append("    if _repositories is None:")
        lines.append("        return JsonResponse({'error': 'generated_views_not_configured'}, status=500)")
        if len(pk_fields) == 1:
            pk_prop = _camel_case(str(pk_fields[0].get("name", "id")))
            lines.append(f"    item = _repositories.{repo_name}.get_by_id({obj_name}Ref({pk_prop}=id))")
            lines.append("    if item is None:")
            lines.append("        return JsonResponse({'error': 'not_found'}, status=404)")
            lines.append("    return JsonResponse(dataclasses.asdict(item))")
        else:
            lines.append("    return JsonResponse({'error': 'composite_get_by_id_requires_custom_route'}, status=501)")
        lines.append("")

        lines.append("@csrf_exempt")
        lines.append(f"def query_{repo_name}(request: HttpRequest) -> HttpResponse:")
        lines.append("    if request.method != 'POST':")
        lines.append("        return JsonResponse({'error': 'method_not_allowed'}, status=405)")
        lines.append("    page = int(request.GET.get('page', '0'))")
        lines.append("    size = int(request.GET.get('size', '20'))")
        lines.append("    payload = json.loads(request.body.decode('utf-8') or '{}')")
        lines.append(f"    filter_model = {query_filter_name}(**payload)")
        lines.append("    if _repositories is None:")
        lines.append("        return JsonResponse({'error': 'generated_views_not_configured'}, status=500)")
        lines.append(f"    result = _repositories.{repo_name}.query(filter_model, page, size)")
        lines.append("    return JsonResponse(dataclasses.asdict(result))")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_django_urls(ir: Dict[str, Any]) -> str:
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}

    lines: List[str] = [
        "# GENERATED FILE: do not edit directly.",
        "from __future__ import annotations",
        "",
        "from django.urls import path",
        "",
        "from . import django_views as views",
        "",
        "urlpatterns = [",
    ]

    for action in _sort_dict_entries([item for item in ir.get("actions", []) if isinstance(item, dict)]):
        action_name = str(action.get("name", "action"))
        camel = _camel_case(action_name)
        lines.append(f"    path('actions/{action_name}', views.action_{camel}),")

    for contract in _sort_dict_entries([item for item in ir.get("query_contracts", []) if isinstance(item, dict)]):
        object_id = str(contract.get("object_id", ""))
        obj = object_by_id.get(object_id, {})
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        repo_name = _camel_case(obj_name)
        paths = contract.get("paths", {}) if isinstance(contract.get("paths"), dict) else {}
        list_path = str(paths.get("list", f"/{repo_name}s")).lstrip("/")
        get_path = _django_path(str(paths.get("get_by_id", f"/{repo_name}s/{{id}}"))).lstrip("/")
        typed_path = str(paths.get("typed_query", f"/{repo_name}s/query")).lstrip("/")
        lines.append(f"    path('{list_path}', views.list_{repo_name}),")
        lines.append(f"    path('{get_path}', views.get_{repo_name}),")
        lines.append(f"    path('{typed_path}', views.query_{repo_name}),")

    lines.append("]")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"
