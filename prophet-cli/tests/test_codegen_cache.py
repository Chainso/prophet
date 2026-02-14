from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "prophet-cli" / "src"))

from prophet_cli.codegen.cache import compute_generation_signature
from prophet_cli.codegen.cache import generation_cache_path
from prophet_cli.codegen.cache import load_generation_cache
from prophet_cli.codegen.cache import write_generation_cache


class CodegenCacheTests(unittest.TestCase):
    def test_signature_is_deterministic_for_same_inputs(self) -> None:
        one = compute_generation_signature(
            toolchain_version="0.4.0",
            stack_id="java_spring_jpa",
            ir_hash="abc",
            out_dir="gen",
            targets=["sql", "openapi"],
            baseline_ir=".prophet/baselines/main.ir.json",
        )
        two = compute_generation_signature(
            toolchain_version="0.4.0",
            stack_id="java_spring_jpa",
            ir_hash="abc",
            out_dir="gen",
            targets=["sql", "openapi"],
            baseline_ir=".prophet/baselines/main.ir.json",
        )
        self.assertEqual(one, two)

    def test_signature_changes_when_ir_hash_changes(self) -> None:
        one = compute_generation_signature(
            toolchain_version="0.4.0",
            stack_id="java_spring_jpa",
            ir_hash="abc",
            out_dir="gen",
            targets=["sql", "openapi"],
            baseline_ir=".prophet/baselines/main.ir.json",
        )
        two = compute_generation_signature(
            toolchain_version="0.4.0",
            stack_id="java_spring_jpa",
            ir_hash="def",
            out_dir="gen",
            targets=["sql", "openapi"],
            baseline_ir=".prophet/baselines/main.ir.json",
        )
        self.assertNotEqual(one, two)

    def test_write_and_load_cache_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prophet-cache-") as tmp:
            root = Path(tmp)
            payload = {"signature": "abc", "stack_id": "java_spring_jpa"}
            write_generation_cache(root, payload)
            loaded = load_generation_cache(root)
            self.assertEqual(loaded, payload)
            self.assertTrue(generation_cache_path(root).exists())

    def test_load_cache_handles_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prophet-cache-invalid-") as tmp:
            root = Path(tmp)
            cache = generation_cache_path(root)
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text("{not-valid", encoding="utf-8")
            loaded = load_generation_cache(root)
            self.assertEqual(loaded, {})


if __name__ == "__main__":
    unittest.main()
