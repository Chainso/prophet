from __future__ import annotations

from typing import Any, Dict, List

from ..support import _camel_case
from ..support import _express_path
from ..support import _extract_path_params
from ..support import _field_index
from ..support import _is_required
from ..support import _object_primary_key_fields
from ..support import _pascal_case
from ..support import _render_property
from ..support import _snake_case
from ..support import _ts_type_for_descriptor
from ..support import _pluralize

def _render_query_filters(ir: Dict[str, Any]) -> str:
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}
    struct_by_id = {item["id"]: item for item in ir.get("structs", []) if isinstance(item, dict) and "id" in item}
    lines: List[str] = ["// GENERATED FILE: do not edit directly.", ""]

    domain_imports = sorted(
        {
            f"{_pascal_case(str(item.get('name', 'Object')))}Ref"
            for item in ir.get("objects", [])
            if isinstance(item, dict)
        }
        | {
            f"{_pascal_case(str(item.get('name', 'Object')))}State"
            for item in ir.get("objects", [])
            if isinstance(item, dict) and item.get("states")
        }
    )
    if domain_imports:
        lines.extend(
            [
                "import type {",
                "  " + ",\n  ".join(domain_imports),
                "} from './domain';",
                "",
            ]
        )

    for contract in sorted(ir.get("query_contracts", []), key=lambda item: str(item.get("object_id", ""))):
        if not isinstance(contract, dict):
            continue
        object_id = str(contract.get("object_id", ""))
        obj = object_by_id.get(object_id, {})
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        fields_by_id = _field_index(list(obj.get("fields", [])))

        lines.append(f"export interface {obj_name}QueryFilter {{")
        for item in list(contract.get("filters", [])):
            if not isinstance(item, dict):
                continue
            field_id = str(item.get("field_id", ""))
            field_name = _camel_case(str(item.get("field_name", "field")))
            if field_id == "__current_state__":
                ts_type = f"{obj_name}State"
            else:
                field = fields_by_id.get(field_id, {})
                type_desc = field.get("type", {}) if isinstance(field, dict) and isinstance(field.get("type"), dict) else {}
                ts_type = _ts_type_for_descriptor(type_desc, type_by_id=type_by_id, object_by_id=object_by_id, struct_by_id=struct_by_id)
            ops = [str(op) for op in item.get("operators", []) if isinstance(op, str)]
            lines.append(f"  {field_name}?: {{")
            if "eq" in ops:
                lines.append(f"    eq?: {ts_type};")
            if "in" in ops:
                lines.append(f"    in?: {ts_type}[];")
            if "contains" in ops:
                lines.append("    contains?: string;")
            if "gte" in ops:
                lines.append(f"    gte?: {ts_type};")
            if "lte" in ops:
                lines.append(f"    lte?: {ts_type};")
            lines.append("  };")
        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"



def _render_query_routes(ir: Dict[str, Any]) -> str:
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}

    lines: List[str] = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import { Router, type Request, type Response, type NextFunction } from 'express';",
        "import type { GeneratedRepositories } from './persistence';",
        "import type * as Filters from './query';",
        "",
        "function parsePage(value: unknown, fallback: number): number {",
        "  const n = Number(value);",
        "  if (!Number.isFinite(n) || n < 0) return fallback;",
        "  return Math.trunc(n);",
        "}",
        "",
        "export function buildGeneratedQueryRouter(repositories: GeneratedRepositories): Router {",
        "  const router = Router();",
        "",
    ]

    for contract in sorted(ir.get("query_contracts", []), key=lambda item: str(item.get("object_id", ""))):
        if not isinstance(contract, dict):
            continue
        object_id = str(contract.get("object_id", ""))
        obj = object_by_id.get(object_id, {})
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        repo_prop = _camel_case(obj_name)
        filter_type = f"Filters.{obj_name}QueryFilter"
        pk_fields = _object_primary_key_fields(obj)
        pk_props = [_camel_case(str(field.get("name", "id"))) for field in pk_fields]

        paths = contract.get("paths", {}) if isinstance(contract.get("paths"), dict) else {}
        list_path = str(paths.get("list", f"/{_pluralize(_snake_case(obj_name))}"))
        get_by_id_path = str(paths.get("get_by_id", f"/{_pluralize(_snake_case(obj_name))}/{{id}}"))
        typed_query_path = str(paths.get("typed_query", f"/{_pluralize(_snake_case(obj_name))}/query"))

        default_size = int(contract.get("pageable", {}).get("default_size", 20))

        lines.append(f"  router.get('{_express_path(list_path)}', async (req: Request, res: Response, next: NextFunction) => {{")
        lines.append("    try {")
        lines.append("      const page = parsePage(req.query.page, 0);")
        lines.append(f"      const size = parsePage(req.query.size, {default_size});")
        lines.append(f"      const result = await repositories.{repo_prop}.list(page, size);")
        lines.append("      res.json(result);")
        lines.append("    } catch (error) {")
        lines.append("      next(error);")
        lines.append("    }")
        lines.append("  });")
        lines.append("")

        params = _extract_path_params(get_by_id_path)
        lines.append(f"  router.get('{_express_path(get_by_id_path)}', async (req: Request, res: Response, next: NextFunction) => {{")
        lines.append("    try {")
        if params and len(params) == 1 and params[0] == "id" and len(pk_props) == 1:
            lines.append("      const id = {")
            lines.append(f"        {pk_props[0]}: String(req.params['id']),")
            lines.append("      };")
        elif params:
            lines.append("      const id = {")
            for idx, param in enumerate(params):
                prop = _camel_case(param)
                if idx < len(pk_props):
                    prop = pk_props[idx]
                lines.append(f"        {prop}: String(req.params['{param}']),")
            lines.append("      };")
        else:
            if pk_props:
                lines.append("      const id = {")
                lines.append(f"        {pk_props[0]}: String(req.params.id),")
                lines.append("      };")
            else:
                lines.append("      const id = { id: String(req.params.id) };")
        lines.append(f"      const item = await repositories.{repo_prop}.getById(id);")
        lines.append("      if (!item) {")
        lines.append("        res.status(404).json({ error: 'not_found' });")
        lines.append("        return;")
        lines.append("      }")
        lines.append("      res.json(item);")
        lines.append("    } catch (error) {")
        lines.append("      next(error);")
        lines.append("    }")
        lines.append("  });")
        lines.append("")

        lines.append(f"  router.post('{_express_path(typed_query_path)}', async (req: Request, res: Response, next: NextFunction) => {{")
        lines.append("    try {")
        lines.append("      const page = parsePage(req.query.page, 0);")
        lines.append(f"      const size = parsePage(req.query.size, {default_size});")
        lines.append(f"      const filter = (req.body ?? {{}}) as {filter_type};")
        lines.append(f"      const result = await repositories.{repo_prop}.query(filter, page, size);")
        lines.append("      res.json(result);")
        lines.append("    } catch (error) {")
        lines.append("      next(error);")
        lines.append("    }")
        lines.append("  });")
        lines.append("")

    lines.extend(["  return router;", "}", ""])
    return "\n".join(lines).rstrip() + "\n"

