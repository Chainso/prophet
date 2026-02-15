from __future__ import annotations

from typing import Any, Dict, List

from ..support import _camel_case
from ..support import _object_primary_key_fields
from ..support import _pascal_case
from ..support import _sort_dict_entries


def render_fastapi_routes(ir: Dict[str, Any]) -> str:
    action_input_by_id = {item["id"]: item for item in ir.get("action_inputs", []) if isinstance(item, dict) and "id" in item}
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}

    lines: List[str] = [
        "# GENERATED FILE: do not edit directly.",
        "from __future__ import annotations",
        "",
        "import dataclasses",
        "",
        "from fastapi import APIRouter, HTTPException, Query",
        "",
        "from .action_handlers import GeneratedActionContext",
        "from .action_service import GeneratedActionExecutionService",
        "from .actions import *",
        "from .persistence import GeneratedRepositories",
        "",
        "def build_generated_router(service: GeneratedActionExecutionService, context: GeneratedActionContext, repositories: GeneratedRepositories) -> APIRouter:",
        "    router = APIRouter()",
        "",
    ]

    for action in _sort_dict_entries([item for item in ir.get("actions", []) if isinstance(item, dict)]):
        action_name = str(action.get("name", "action"))
        camel = _camel_case(action_name)
        input_shape = action_input_by_id.get(str(action.get("input_shape_id", "")), {})
        input_name = _pascal_case(str(input_shape.get("name", "ActionInput")))
        lines.append(f"    @router.post('/actions/{action_name}')")
        lines.append(f"    async def action_{camel}(payload: dict):")
        lines.append(f"        input_model = {input_name}(**(payload or {{}}))")
        lines.append(f"        result = await service.execute_{camel}(input_model, context)")
        lines.append("        return dataclasses.asdict(result)")
        lines.append("")

    for contract in _sort_dict_entries([item for item in ir.get("query_contracts", []) if isinstance(item, dict)]):
        object_id = str(contract.get("object_id", ""))
        obj = object_by_id.get(object_id, {})
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        repo_name = _camel_case(obj_name)
        query_filter_name = f"{obj_name}QueryFilter"
        paths = contract.get("paths", {}) if isinstance(contract.get("paths"), dict) else {}
        list_path = str(paths.get("list", f"/{repo_name}s"))
        get_path = str(paths.get("get_by_id", f"/{repo_name}s/{{id}}"))
        typed_path = str(paths.get("typed_query", f"/{repo_name}s/query"))

        lines.append(f"    @router.get('{list_path}')")
        lines.append(f"    async def list_{repo_name}(page: int = Query(default=0), size: int = Query(default=20)):")
        lines.append(f"        result = await repositories.{repo_name}.list(page, size)")
        lines.append("        return dataclasses.asdict(result)")
        lines.append("")

        pk_fields = _object_primary_key_fields(obj)
        lines.append(f"    @router.get('{get_path}')")
        lines.append(f"    async def get_{repo_name}(id: str):")
        if len(pk_fields) == 1:
            pk_field = pk_fields[0]
            pk_prop = _camel_case(str(pk_field.get("name", "id")))
            lines.append(f"        item = await repositories.{repo_name}.get_by_id({obj_name}Ref({pk_prop}=id))")
        else:
            lines.append("        raise HTTPException(status_code=501, detail='composite_get_by_id_requires_custom_route')")
            lines.append("")
            continue
        lines.append("        if item is None:")
        lines.append("            raise HTTPException(status_code=404, detail='not_found')")
        lines.append("        return dataclasses.asdict(item)")
        lines.append("")

        lines.append(f"    @router.post('{typed_path}')")
        lines.append(f"    async def query_{repo_name}(payload: dict, page: int = Query(default=0), size: int = Query(default=20)):")
        lines.append(f"        filter_model = {query_filter_name}(**(payload or {{}}))")
        lines.append(f"        result = await repositories.{repo_name}.query(filter_model, page, size)")
        lines.append("        return dataclasses.asdict(result)")
        lines.append("")

    lines.append("    return router")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"
