from __future__ import annotations

from typing import Any, Dict, List

from ..support import _camel_case
from ..support import _is_required
from ..support import _object_primary_key_fields
from ..support import _pascal_case
from ..support import _py_type_for_descriptor
from ..support import _sort_dict_entries


def _python_type_for_sqlmodel(type_desc: Dict[str, Any], type_by_id: Dict[str, Dict[str, Any]]) -> str:
    kind = str(type_desc.get("kind", ""))
    if kind == "list":
        return "list"
    if kind in {"struct", "object_ref"}:
        return "dict"
    if kind == "base":
        base = str(type_desc.get("name", "string"))
    elif kind == "custom":
        target = type_by_id.get(str(type_desc.get("target_type_id", "")), {})
        base = str(target.get("base", "string"))
    else:
        return "dict"

    if base == "boolean":
        return "bool"
    if base in {"int", "long", "short", "byte"}:
        return "int"
    if base in {"double", "float", "decimal"}:
        return "float"
    return "str"


def _is_json_descriptor(type_desc: Dict[str, Any]) -> bool:
    return str(type_desc.get("kind", "")) in {"list", "struct", "object_ref"}


def render_sqlmodel_models(ir: Dict[str, Any]) -> str:
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}

    lines: List[str] = [
        "# GENERATED FILE: do not edit directly.",
        "from __future__ import annotations",
        "",
        "from typing import Optional",
        "",
        "from sqlalchemy import JSON, Column",
        "from sqlmodel import Field, SQLModel",
        "",
    ]

    for obj in _sort_dict_entries([item for item in ir.get("objects", []) if isinstance(item, dict)]):
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        table_name = f"{obj_name.lower()}s"
        primary_ids = set(obj.get("keys", {}).get("primary", {}).get("field_ids", []))

        lines.append(f"class {obj_name}Model(SQLModel, table=True):")
        lines.append(f"    __tablename__ = '{table_name}'")

        for field in [item for item in obj.get("fields", []) if isinstance(item, dict)]:
            prop = _camel_case(str(field.get("name", "field")))
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            py_type = _python_type_for_sqlmodel(type_desc, type_by_id)
            required = _is_required(field)
            is_pk = str(field.get("id", "")) in primary_ids
            nullable = not required and not is_pk

            if _is_json_descriptor(type_desc):
                type_hint = py_type
                if nullable:
                    type_hint = f"Optional[{py_type}]"
                    default_expr = "default=None"
                else:
                    default_expr = "default_factory=dict" if py_type == "dict" else "default_factory=list"
                lines.append(
                    f"    {prop}: {type_hint} = Field({default_expr}, "
                    f"sa_column=Column(JSON, nullable={str(nullable)}, primary_key={str(is_pk)}))"
                )
                continue

            if nullable:
                lines.append(f"    {prop}: Optional[{py_type}] = Field(default=None, primary_key={str(is_pk)})")
            else:
                lines.append(f"    {prop}: {py_type} = Field(primary_key={str(is_pk)})")

        if obj.get("states"):
            initial = next(
                (
                    str(item.get("name", ""))
                    for item in obj.get("states", [])
                    if isinstance(item, dict) and item.get("initial")
                ),
                "",
            )
            if initial:
                lines.append(f"    currentState: str = Field(default='{initial}')")
            else:
                lines.append("    currentState: str")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_sqlmodel_adapters(ir: Dict[str, Any], *, async_mode: bool) -> str:
    type_by_id = {item["id"]: item for item in ir.get("types", []) if isinstance(item, dict) and "id" in item}
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}
    struct_by_id = {item["id"]: item for item in ir.get("structs", []) if isinstance(item, dict) and "id" in item}
    query_contract_by_object_id = {
        str(item.get("object_id", "")): item
        for item in ir.get("query_contracts", [])
        if isinstance(item, dict)
    }

    lines: List[str] = [
        "# GENERATED FILE: do not edit directly.",
        "from __future__ import annotations",
        "",
        "import asyncio",
        "import dataclasses",
        "",
        "from typing import Callable, Optional",
        "",
        "from sqlalchemy import func",
        "from sqlmodel import Session, select",
        "",
        "from . import domain as Domain",
        "from . import persistence as Persistence",
        "from . import query as Filters",
        "from . import sqlmodel_models as Models",
        "",
        "def _serialize(value):",
        "    if dataclasses.is_dataclass(value):",
        "        return dataclasses.asdict(value)",
        "    if isinstance(value, list):",
        "        return [_serialize(item) for item in value]",
        "    return value",
        "",
    ]

    for obj in _sort_dict_entries([item for item in ir.get("objects", []) if isinstance(item, dict)]):
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        fields = [item for item in obj.get("fields", []) if isinstance(item, dict)]

        lines.append(f"def _{obj_name.lower()}_to_model(item: Domain.{obj_name}) -> Models.{obj_name}Model:")
        lines.append(f"    return Models.{obj_name}Model(")
        for field in fields:
            prop = _camel_case(str(field.get("name", "field")))
            lines.append(f"        {prop}=_serialize(item.{prop}),")
        if obj.get("states"):
            lines.append("        currentState=item.currentState,")
        lines.append("    )")
        lines.append("")

        lines.append(f"def _{obj_name.lower()}_to_domain(record: Models.{obj_name}Model) -> Domain.{obj_name}:")
        lines.append(f"    return Domain.{obj_name}(")
        for field in fields:
            prop = _camel_case(str(field.get("name", "field")))
            type_desc = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            py_type = _py_type_for_descriptor(
                type_desc,
                type_by_id=type_by_id,
                object_by_id=object_by_id,
                struct_by_id=struct_by_id,
            )
            kind = str(type_desc.get("kind", ""))
            if kind in {"object_ref", "struct"}:
                lines.append(
                    f"        {prop}=Domain.{py_type}(**record.{prop}) if isinstance(record.{prop}, dict) else record.{prop},"
                )
            elif kind == "list":
                element = type_desc.get("element", {}) if isinstance(type_desc.get("element"), dict) else {}
                element_kind = str(element.get("kind", ""))
                if element_kind in {"object_ref", "struct"}:
                    element_type = _py_type_for_descriptor(
                        element,
                        type_by_id=type_by_id,
                        object_by_id=object_by_id,
                        struct_by_id=struct_by_id,
                    )
                    lines.append(
                        f"        {prop}=[Domain.{element_type}(**entry) if isinstance(entry, dict) else entry for entry in (record.{prop} or [])],"
                    )
                else:
                    lines.append(f"        {prop}=record.{prop},")
            else:
                lines.append(f"        {prop}=record.{prop},")
        if obj.get("states"):
            lines.append("        currentState=record.currentState,")
        lines.append("    )")
        lines.append("")

        repo_name = f"{obj_name}SqlModelRepository"
        query_filter_name = f"Filters.{obj_name}QueryFilter"
        lines.append(f"class {repo_name}:")
        lines.append("    def __init__(self, session_factory: Callable[[], Session]):")
        lines.append("        self._session_factory = session_factory")
        lines.append("")

        lines.append(f"    def _apply_filter(self, stmt, filter: {query_filter_name}):")
        contract = query_contract_by_object_id.get(str(obj.get("id", "")), {})
        for filter_def in sorted(
            [item for item in contract.get("filters", []) if isinstance(item, dict)],
            key=lambda item: str(item.get("field_name", "")),
        ):
            field_name = _camel_case(str(filter_def.get("field_name", "field")))
            lines.append(f"        if filter.{field_name} is not None:")
            if str(filter_def.get("field_id", "")) == "__current_state__":
                target = "Models." + obj_name + "Model.currentState"
            else:
                target = "Models." + obj_name + "Model." + field_name
            lines.append(f"            if filter.{field_name}.eq is not None:")
            lines.append(f"                stmt = stmt.where({target} == filter.{field_name}.eq)")
            lines.append(f"            if getattr(filter.{field_name}, 'inValues', None):")
            lines.append(f"                stmt = stmt.where({target}.in_(filter.{field_name}.inValues))")
            lines.append(f"            if getattr(filter.{field_name}, 'contains', None):")
            lines.append(f"                stmt = stmt.where({target}.contains(filter.{field_name}.contains))")
            lines.append(f"            if getattr(filter.{field_name}, 'gte', None) is not None:")
            lines.append(f"                stmt = stmt.where({target} >= filter.{field_name}.gte)")
            lines.append(f"            if getattr(filter.{field_name}, 'lte', None) is not None:")
            lines.append(f"                stmt = stmt.where({target} <= filter.{field_name}.lte)")
        lines.append("        return stmt")
        lines.append("")

        lines.append("    def _list_sync(self, page: int, size: int) -> Persistence.PagedResult:")
        lines.append("        with self._session_factory() as session:")
        lines.append(f"            stmt = select(Models.{obj_name}Model)")
        lines.append(f"            total_stmt = select(func.count()).select_from(Models.{obj_name}Model)")
        lines.append("            total = int(session.exec(total_stmt).one() or 0)")
        lines.append("            rows = list(session.exec(stmt.offset(page * size).limit(size)))")
        lines.append(f"            content = [_{obj_name.lower()}_to_domain(row) for row in rows]")
        lines.append("            total_pages = (total + size - 1) // size if size > 0 else 0")
        lines.append(
            "            return Persistence.PagedResult(content=content, page=page, size=size, totalElements=total, totalPages=total_pages)"
        )
        lines.append("")

        lines.append(f"    def _query_sync(self, filter: {query_filter_name}, page: int, size: int) -> Persistence.PagedResult:")
        lines.append("        with self._session_factory() as session:")
        lines.append(f"            base_stmt = select(Models.{obj_name}Model)")
        lines.append("            stmt = self._apply_filter(base_stmt, filter)")
        lines.append("            rows = list(session.exec(stmt.offset(page * size).limit(size)))")
        lines.append(f"            count_stmt = self._apply_filter(select(func.count()).select_from(Models.{obj_name}Model), filter)")
        lines.append("            total = int(session.exec(count_stmt).one() or 0)")
        lines.append(f"            content = [_{obj_name.lower()}_to_domain(row) for row in rows]")
        lines.append("            total_pages = (total + size - 1) // size if size > 0 else 0")
        lines.append(
            "            return Persistence.PagedResult(content=content, page=page, size=size, totalElements=total, totalPages=total_pages)"
        )
        lines.append("")

        pk_fields = _object_primary_key_fields(obj)
        lines.append(f"    def _get_by_id_sync(self, id: Domain.{obj_name}Ref) -> Optional[Domain.{obj_name}]:")
        lines.append("        with self._session_factory() as session:")
        if pk_fields:
            lines.append(f"            stmt = select(Models.{obj_name}Model)")
            for pk in pk_fields:
                pk_prop = _camel_case(str(pk.get("name", "id")))
                lines.append(f"            stmt = stmt.where(Models.{obj_name}Model.{pk_prop} == id.{pk_prop})")
            lines.append("            record = session.exec(stmt.limit(1)).first()")
        else:
            lines.append("            record = None")
        lines.append("            if record is None:")
        lines.append("                return None")
        lines.append(f"            return _{obj_name.lower()}_to_domain(record)")
        lines.append("")

        lines.append(f"    def _save_sync(self, item: Domain.{obj_name}) -> Domain.{obj_name}:")
        lines.append("        with self._session_factory() as session:")
        lines.append(f"            model = _{obj_name.lower()}_to_model(item)")
        lines.append("            session.merge(model)")
        lines.append("            session.commit()")
        lines.append("        return item")
        lines.append("")

        if async_mode:
            lines.append("    async def list(self, page: int, size: int) -> Persistence.PagedResult:")
            lines.append("        return await asyncio.to_thread(self._list_sync, page, size)")
            lines.append("")
            lines.append(f"    async def query(self, filter: {query_filter_name}, page: int, size: int) -> Persistence.PagedResult:")
            lines.append("        return await asyncio.to_thread(self._query_sync, filter, page, size)")
            lines.append("")
            lines.append(f"    async def get_by_id(self, id: Domain.{obj_name}Ref) -> Optional[Domain.{obj_name}]:")
            lines.append("        return await asyncio.to_thread(self._get_by_id_sync, id)")
            lines.append("")
            lines.append(f"    async def save(self, item: Domain.{obj_name}) -> Domain.{obj_name}:")
            lines.append("        return await asyncio.to_thread(self._save_sync, item)")
        else:
            lines.append("    def list(self, page: int, size: int) -> Persistence.PagedResult:")
            lines.append("        return self._list_sync(page, size)")
            lines.append("")
            lines.append(f"    def query(self, filter: {query_filter_name}, page: int, size: int) -> Persistence.PagedResult:")
            lines.append("        return self._query_sync(filter, page, size)")
            lines.append("")
            lines.append(f"    def get_by_id(self, id: Domain.{obj_name}Ref) -> Optional[Domain.{obj_name}]:")
            lines.append("        return self._get_by_id_sync(id)")
            lines.append("")
            lines.append(f"    def save(self, item: Domain.{obj_name}) -> Domain.{obj_name}:")
            lines.append("        return self._save_sync(item)")
        lines.append("")

    lines.append("class SqlModelGeneratedRepositories:")
    lines.append("    def __init__(self, session_factory: Callable[[], Session]):")
    for obj in _sort_dict_entries([item for item in ir.get("objects", []) if isinstance(item, dict)]):
        obj_name = _pascal_case(str(obj.get("name", "Object")))
        prop = _camel_case(obj_name)
        lines.append(f"        self.{prop} = {obj_name}SqlModelRepository(session_factory)")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"
