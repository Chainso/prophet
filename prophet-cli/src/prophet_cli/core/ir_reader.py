from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from .errors import ProphetError


REQUIRED_TOP_LEVEL_KEYS = (
    "ir_version",
    "toolchain_version",
    "ontology",
    "types",
    "objects",
    "structs",
    "action_inputs",
    "actions",
    "events",
    "triggers",
)


@dataclass(frozen=True)
class ActionContractView:
    id: str
    name: str
    kind: str
    input_shape_id: str
    output_event_id: str


@dataclass(frozen=True)
class QueryFilterView:
    field_id: str
    field_name: str
    operators: List[str]


@dataclass(frozen=True)
class QueryContractView:
    object_id: str
    object_name: str
    list_path: str
    get_by_id_path: str
    typed_query_path: str
    pageable_supported: bool
    default_page_size: int
    filters: List[QueryFilterView]


@dataclass(frozen=True)
class IRReader:
    _ir: Dict[str, Any]

    @staticmethod
    def from_dict(ir: Dict[str, Any]) -> "IRReader":
        reader = IRReader(ir)
        reader.validate()
        return reader

    def validate(self) -> None:
        for key in REQUIRED_TOP_LEVEL_KEYS:
            if key not in self._ir:
                raise ProphetError(f"IR missing required key: {key}")
        list_keys = (
            "types",
            "objects",
            "structs",
            "action_inputs",
            "actions",
            "events",
            "triggers",
        )
        for key in list_keys:
            if not isinstance(self._ir.get(key), list):
                raise ProphetError(f"IR key '{key}' must be a list")
        if not isinstance(self._ir.get("ontology"), dict):
            raise ProphetError("IR key 'ontology' must be an object")

    def as_dict(self) -> Dict[str, Any]:
        return self._ir

    def get(self, key: str, default: Any = None) -> Any:
        return self._ir.get(key, default)

    @property
    def ir_hash(self) -> str:
        return str(self._ir.get("ir_hash", ""))

    @property
    def query_contracts_version(self) -> str:
        return str(self._ir.get("query_contracts_version", ""))

    @property
    def ontology_version(self) -> str:
        ont = self._ir.get("ontology", {})
        if not isinstance(ont, dict):
            return "0.0.0"
        return str(ont.get("version", "0.0.0"))

    def types(self) -> List[Dict[str, Any]]:
        return list(self._ir.get("types", []))

    def objects(self) -> List[Dict[str, Any]]:
        return list(self._ir.get("objects", []))

    def structs(self) -> List[Dict[str, Any]]:
        return list(self._ir.get("structs", []))

    def action_inputs(self) -> List[Dict[str, Any]]:
        return list(self._ir.get("action_inputs", []))

    def actions(self) -> List[Dict[str, Any]]:
        return list(self._ir.get("actions", []))

    def events(self) -> List[Dict[str, Any]]:
        return list(self._ir.get("events", []))

    def triggers(self) -> List[Dict[str, Any]]:
        return list(self._ir.get("triggers", []))

    def query_contracts(self) -> List[Dict[str, Any]]:
        return list(self._ir.get("query_contracts", []))

    def action_contracts(self) -> List[ActionContractView]:
        contracts: List[ActionContractView] = []
        for action in self.actions():
            contracts.append(
                ActionContractView(
                    id=str(action.get("id", "")),
                    name=str(action.get("name", "")),
                    kind=str(action.get("kind", "")),
                    input_shape_id=str(action.get("input_shape_id", "")),
                    output_event_id=str(action.get("output_event_id", "")),
                )
            )
        return contracts

    def query_contract_views(self) -> List[QueryContractView]:
        views: List[QueryContractView] = []
        for contract in self.query_contracts():
            paths = contract.get("paths", {}) if isinstance(contract.get("paths"), dict) else {}
            pageable = contract.get("pageable", {}) if isinstance(contract.get("pageable"), dict) else {}
            filters: List[QueryFilterView] = []
            for item in contract.get("filters", []):
                if not isinstance(item, dict):
                    continue
                operators_raw = item.get("operators", [])
                operators = [str(op) for op in operators_raw] if isinstance(operators_raw, list) else []
                filters.append(
                    QueryFilterView(
                        field_id=str(item.get("field_id", "")),
                        field_name=str(item.get("field_name", "")),
                        operators=operators,
                    )
                )

            views.append(
                QueryContractView(
                    object_id=str(contract.get("object_id", "")),
                    object_name=str(contract.get("object_name", "")),
                    list_path=str(paths.get("list", "")),
                    get_by_id_path=str(paths.get("get_by_id", "")),
                    typed_query_path=str(paths.get("typed_query", "")),
                    pageable_supported=bool(pageable.get("supported", False)),
                    default_page_size=int(pageable.get("default_size", 0)),
                    filters=filters,
                )
            )
        return views

    @staticmethod
    def index_by_id(items: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        return {
            str(item["id"]): item
            for item in items
            if isinstance(item, dict) and "id" in item
        }

    def object_by_id(self) -> Dict[str, Dict[str, Any]]:
        return self.index_by_id(self.objects())

    def type_by_id(self) -> Dict[str, Dict[str, Any]]:
        return self.index_by_id(self.types())

    def action_by_id(self) -> Dict[str, Dict[str, Any]]:
        return self.index_by_id(self.actions())
