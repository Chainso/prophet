from __future__ import annotations

import sys
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "prophet-cli" / "src"))

from prophet_cli.codegen.contracts import GenerationContext
from prophet_cli.codegen.pipeline import run_generation_pipeline
from prophet_cli.core.errors import ProphetError


class CodegenPipelineTests(unittest.TestCase):
    def test_pipeline_routes_to_registered_stack_generator(self) -> None:
        context = GenerationContext(
            stack_id="java_spring_jpa",
            ir={"ir_hash": "abc"},
            cfg={},
            root=Path("."),
        )

        def generator(ctx: GenerationContext) -> dict[str, str]:
            self.assertEqual(ctx.stack_id, "java_spring_jpa")
            return {"gen/example.txt": "ok\n"}

        outputs = run_generation_pipeline(context, {"java_spring_jpa": generator})
        self.assertEqual(outputs, {"gen/example.txt": "ok\n"})

    def test_pipeline_rejects_unimplemented_stack(self) -> None:
        context = GenerationContext(
            stack_id="python_fastapi_sqlalchemy",
            ir={},
            cfg={},
            root=Path("."),
        )
        with self.assertRaises(ProphetError) as ctx:
            run_generation_pipeline(context, {"java_spring_jpa": lambda _: {}})
        self.assertIn("no generator implementation is registered", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

