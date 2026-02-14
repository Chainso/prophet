from __future__ import annotations

import sys
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "prophet-cli" / "src"))

from prophet_cli.cli import build_ir
from prophet_cli.cli import load_config
from prophet_cli.cli import parse_ontology


EXAMPLE_ROOT = PROJECT_ROOT / "examples" / "java" / "prophet_example_spring"


def load_example_ir() -> dict:
    cfg = load_config(EXAMPLE_ROOT / "prophet.yaml")
    ontology = parse_ontology((EXAMPLE_ROOT / "ontology" / "local" / "main.prophet").read_text(encoding="utf-8"))
    return build_ir(ontology, cfg)


class SemanticContractTests(unittest.TestCase):
    def test_action_contracts_reference_declared_shapes(self) -> None:
        ir = load_example_ir()
        input_ids = {item["id"] for item in ir.get("action_inputs", [])}
        output_ids = {item["id"] for item in ir.get("action_outputs", [])}
        for action in ir.get("actions", []):
            self.assertIn(action.get("input_shape_id"), input_ids)
            self.assertIn(action.get("output_shape_id"), output_ids)

    def test_query_contracts_align_with_object_fields(self) -> None:
        ir = load_example_ir()
        objects_by_id = {item["id"]: item for item in ir.get("objects", [])}
        for contract in ir.get("query_contracts", []):
            object_id = contract.get("object_id")
            self.assertIn(object_id, objects_by_id)
            field_ids = {field["id"] for field in objects_by_id[object_id].get("fields", [])}
            for item in contract.get("filters", []):
                field_id = item.get("field_id")
                if field_id == "__current_state__":
                    continue
                self.assertIn(field_id, field_ids)

    def test_struct_and_object_ref_types_are_preserved(self) -> None:
        ir = load_example_ir()
        structs_by_id = {item["id"] for item in ir.get("structs", [])}
        objects_by_id = {item["id"] for item in ir.get("objects", [])}
        found_struct = False
        found_object_ref = False

        for obj in ir.get("objects", []):
            for field in obj.get("fields", []):
                field_type = field.get("type", {})
                if field_type.get("kind") == "struct":
                    found_struct = True
                    self.assertIn(field_type.get("target_struct_id"), structs_by_id)

        for struct in ir.get("structs", []):
            for field in struct.get("fields", []):
                field_type = field.get("type", {})
                if field_type.get("kind") == "list":
                    element = field_type.get("element", {})
                    if element.get("kind") == "object_ref":
                        found_object_ref = True
                        self.assertIn(element.get("target_object_id"), objects_by_id)

        self.assertTrue(found_struct, "expected at least one struct-typed field in example IR")
        self.assertTrue(found_object_ref, "expected at least one object-ref list field in example IR")

    def test_query_paths_include_required_endpoints(self) -> None:
        ir = load_example_ir()
        for contract in ir.get("query_contracts", []):
            paths = contract.get("paths", {})
            self.assertIn("list", paths)
            self.assertIn("get_by_id", paths)
            self.assertIn("typed_query", paths)


if __name__ == "__main__":
    unittest.main()
