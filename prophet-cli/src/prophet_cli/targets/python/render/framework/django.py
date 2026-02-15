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
        "import types",
        "",
        "from typing import Any, Union, get_args, get_origin, get_type_hints",
        "",
        "from django.http import HttpRequest, HttpResponse, JsonResponse",
        "from django.views.decorators.csrf import csrf_exempt",
        "",
        "from .action_handlers import GeneratedActionContext",
        "from .action_service import GeneratedActionExecutionService",
        "from .actions import *",
        "from .persistence import GeneratedRepositories",
        "from .query import *",
        "",
        "_service: GeneratedActionExecutionService | None = None",
        "_context: GeneratedActionContext | None = None",
        "_repositories: GeneratedRepositories | None = None",
        "",
        "_TYPE_HINT_CACHE: dict[type, dict[str, Any]] = {}",
        "",
        "def _coerce_value(expected_type: Any, value: Any) -> Any:",
        "    if value is None:",
        "        return None",
        "    origin = get_origin(expected_type)",
        "    if origin is list:",
        "        (item_type,) = get_args(expected_type) or (Any,)",
        "        if not isinstance(value, list):",
        "            return value",
        "        return [_coerce_value(item_type, item) for item in value]",
        "    if origin is dict:",
        "        return value",
        "    if origin in (types.UnionType, Union):",
        "        args = [item for item in get_args(expected_type) if item is not type(None)]",
        "        if len(args) == 1:",
        "            return _coerce_value(args[0], value)",
        "        for arg in args:",
        "            try:",
        "                return _coerce_value(arg, value)",
        "            except Exception:",
        "                continue",
        "        return value",
        "    if isinstance(expected_type, type) and dataclasses.is_dataclass(expected_type):",
        "        if isinstance(value, expected_type):",
        "            return value",
        "        if not isinstance(value, dict):",
        "            return value",
        "        hints = _TYPE_HINT_CACHE.get(expected_type)",
        "        if hints is None:",
        "            hints = get_type_hints(expected_type, globalns=globals(), localns=globals())",
        "            _TYPE_HINT_CACHE[expected_type] = hints",
        "        kwargs: dict[str, Any] = {}",
        "        for field in dataclasses.fields(expected_type):",
        "            if field.name in value:",
        "                field_type = hints.get(field.name, Any)",
        "                kwargs[field.name] = _coerce_value(field_type, value[field.name])",
        "        return expected_type(**kwargs)",
        "    return value",
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
        lines.append(f"    input_model = _coerce_value({input_name}, payload)")
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
        lines.append(f"    filter_model = _coerce_value({query_filter_name}, payload)")
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
