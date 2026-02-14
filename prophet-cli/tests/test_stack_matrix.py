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

    def test_supported_matrix_contains_planned_stacks(self) -> None:
        ids = {row["id"] for row in supported_stack_table()}
        self.assertIn("java_spring_jpa", ids)
        self.assertIn("node_express_typeorm", ids)
        self.assertIn("node_express_prisma", ids)
        self.assertIn("node_express_mongoose", ids)
        self.assertIn("python_fastapi_sqlalchemy", ids)
        self.assertIn("python_flask_sqlalchemy", ids)
        self.assertIn("python_django_orm", ids)


if __name__ == "__main__":
    unittest.main()

