from __future__ import annotations

import sys
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "prophet-cli" / "src"))

from prophet_cli.codegen.contracts import GenerationContext
from prophet_cli.codegen.stacks import StackSpec
from prophet_cli.core.ir_reader import IRReader
from prophet_cli.targets.java_spring_jpa.generator import JavaSpringJpaDeps
from prophet_cli.targets.java_spring_jpa.generator import generate_outputs


def minimal_ir() -> dict:
    return {
        "ir_version": "0.1",
        "toolchain_version": "0.4.0",
        "ontology": {"id": "ont", "name": "Ont", "version": "0.1.0"},
        "types": [],
        "objects": [],
        "structs": [],
        "action_inputs": [],
        "action_outputs": [],
        "actions": [],
        "events": [],
        "triggers": [],
        "ir_hash": "abc123",
    }


class JavaTargetIRReaderTests(unittest.TestCase):
    def test_target_generator_consumes_ir_reader_contract(self) -> None:
        calls = {"render_sql": 0, "render_openapi": 0, "compute_delta": 0}
        reader = IRReader.from_dict(minimal_ir())
        context = GenerationContext(
            stack_id="java_spring_jpa",
            ir=reader.as_dict(),
            ir_reader=reader,
            cfg={"generation": {"out_dir": "gen", "targets": ["sql", "openapi", "spring_boot"]}},
            root=Path("."),
        )

        deps = JavaSpringJpaDeps(
            cfg_get=_cfg_get,
            resolve_stack_spec=lambda cfg: StackSpec(
                id="java_spring_jpa",
                language="java",
                framework="spring_boot",
                orm="jpa",
                status="implemented",
                implemented=True,
                description="test stack",
                default_targets=("sql", "openapi", "spring_boot"),
                notes="",
                capabilities={"action_endpoints"},
            ),
            render_sql=lambda r: _count_and_return(calls, "render_sql", r, "-- sql\n"),
            compute_delta_from_baseline=lambda root, cfg, r: _count_and_delta(calls, "compute_delta", r),
            render_openapi=lambda r: _count_and_return(calls, "render_openapi", r, "openapi: 3.0.3\n"),
            toolchain_version="0.4.0",
        )

        outputs = generate_outputs(context, deps)
        self.assertIn("gen/sql/schema.sql", outputs)
        self.assertIn("gen/openapi/openapi.yaml", outputs)
        self.assertIn("gen/manifest/generated-files.json", outputs)
        self.assertEqual(calls["render_sql"], 1)
        self.assertEqual(calls["render_openapi"], 1)
        self.assertEqual(calls["compute_delta"], 1)


def _count_and_return(calls: dict, key: str, reader: IRReader, value: str) -> str:
    if not isinstance(reader, IRReader):
        raise AssertionError("expected IRReader")
    calls[key] += 1
    return value


def _count_and_delta(calls: dict, key: str, reader: IRReader):
    if not isinstance(reader, IRReader):
        raise AssertionError("expected IRReader")
    calls[key] += 1
    return None, [], None, None, {"safe_auto_apply_count": 0, "manual_review_count": 0, "destructive_count": 0, "findings": []}


def _cfg_get(cfg: dict, keys: list[str], default=None):
    cur = cfg
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


if __name__ == "__main__":
    unittest.main()
