from __future__ import annotations

import sys
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "prophet-cli" / "src"))

from prophet_cli.codegen.stacks import resolve_stack_spec
from prophet_cli.codegen.stacks import supported_stack_table
from prophet_cli.core.errors import ProphetError


class StackMatrixTests(unittest.TestCase):
    def test_default_stack_is_java_spring_jpa(self) -> None:
        cfg = {"generation": {}}
        stack = resolve_stack_spec(cfg)
        self.assertEqual(stack.id, "java_spring_jpa")

    def test_invalid_stack_rejected_with_actionable_message(self) -> None:
        cfg = {"generation": {"stack": {"id": "unknown_stack"}}}
        with self.assertRaises(ProphetError) as ctx:
            resolve_stack_spec(cfg)
        self.assertIn("Unsupported generation stack", str(ctx.exception))
        self.assertIn("generation.stack.id", str(ctx.exception))

    def test_tuple_based_stack_resolution_without_id(self) -> None:
        cfg = {
            "generation": {
                "stack": {
                    "language": "python",
                    "framework": "fastapi",
                    "orm": "sqlalchemy",
                }
            }
        }
        stack = resolve_stack_spec(cfg)
        self.assertEqual(stack.id, "python_fastapi_sqlalchemy")

    def test_id_and_tuple_mismatch_is_rejected(self) -> None:
        cfg = {
            "generation": {
                "stack": {
                    "id": "java_spring_jpa",
                    "framework": "express",
                }
            }
        }
        with self.assertRaises(ProphetError) as ctx:
            resolve_stack_spec(cfg)
        self.assertIn("does not match stack id", str(ctx.exception))

    def test_unknown_stack_keys_are_rejected(self) -> None:
        cfg = {
            "generation": {
                "stack": {
                    "id": "java_spring_jpa",
                    "transport": "http",
                }
            }
        }
        with self.assertRaises(ProphetError) as ctx:
            resolve_stack_spec(cfg)
        self.assertIn("Invalid config keys under generation.stack", str(ctx.exception))

    def test_supported_matrix_contains_planned_stacks(self) -> None:
        rows = supported_stack_table()
        ids = {row["id"] for row in rows}
        by_id = {row["id"]: row for row in rows}
        self.assertIn("java_spring_jpa", ids)
        self.assertIn("node_express_typeorm", ids)
        self.assertIn("node_express_prisma", ids)
        self.assertIn("node_express_mongoose", ids)
        self.assertIn("python_fastapi_sqlalchemy", ids)
        self.assertIn("python_fastapi_sqlmodel", ids)
        self.assertIn("python_flask_sqlalchemy", ids)
        self.assertIn("python_flask_sqlmodel", ids)
        self.assertIn("python_django_django_orm", ids)
        self.assertTrue(by_id["java_spring_jpa"]["implemented"])
        self.assertEqual(by_id["java_spring_jpa"]["status"], "implemented")
        self.assertTrue(by_id["node_express_prisma"]["implemented"])
        self.assertEqual(by_id["node_express_prisma"]["status"], "implemented")
        self.assertIn("node_express", by_id["node_express_prisma"]["default_targets"])
        self.assertIn("prisma", by_id["node_express_prisma"]["default_targets"])
        self.assertTrue(by_id["node_express_typeorm"]["implemented"])
        self.assertEqual(by_id["node_express_typeorm"]["status"], "implemented")
        self.assertIn("typeorm", by_id["node_express_typeorm"]["default_targets"])
        self.assertTrue(by_id["node_express_mongoose"]["implemented"])
        self.assertEqual(by_id["node_express_mongoose"]["status"], "implemented")
        self.assertIn("mongoose", by_id["node_express_mongoose"]["default_targets"])
        self.assertIn("description", by_id["java_spring_jpa"])
        self.assertIn("default_targets", by_id["java_spring_jpa"])
        self.assertIn("spring_boot", by_id["java_spring_jpa"]["default_targets"])
        self.assertTrue(by_id["python_fastapi_sqlalchemy"]["implemented"])
        self.assertEqual(by_id["python_fastapi_sqlalchemy"]["status"], "implemented")
        self.assertIn("python", by_id["python_fastapi_sqlalchemy"]["default_targets"])
        self.assertTrue(by_id["python_fastapi_sqlmodel"]["implemented"])
        self.assertTrue(by_id["python_flask_sqlalchemy"]["implemented"])
        self.assertTrue(by_id["python_flask_sqlmodel"]["implemented"])
        self.assertTrue(by_id["python_django_django_orm"]["implemented"])


if __name__ == "__main__":
    unittest.main()
