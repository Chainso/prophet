from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "prophet-cli" / "src"))

from prophet_cli.codegen.stack_manifest import STACK_MANIFEST
from prophet_cli.codegen.stack_manifest import validate_stack_manifest
from prophet_cli.core.errors import ProphetError


class StackManifestTests(unittest.TestCase):
    def test_manifest_validates_current_entries(self) -> None:
        normalized = validate_stack_manifest(STACK_MANIFEST)
        self.assertGreaterEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["id"], "java_spring_jpa")

    def test_manifest_rejects_duplicate_ids(self) -> None:
        manifest = copy.deepcopy(STACK_MANIFEST)
        duplicate = copy.deepcopy(manifest[0])
        duplicate["language"] = "java2"
        duplicate["framework"] = "spring_boot2"
        duplicate["orm"] = "jpa2"
        manifest.append(duplicate)
        with self.assertRaises(ProphetError) as ctx:
            validate_stack_manifest(manifest)
        self.assertIn("duplicate id", str(ctx.exception))

    def test_manifest_rejects_unknown_capability(self) -> None:
        manifest = copy.deepcopy(STACK_MANIFEST)
        manifest[0]["capabilities"] = manifest[0]["capabilities"] + ["does_not_exist"]
        with self.assertRaises(ProphetError) as ctx:
            validate_stack_manifest(manifest)
        self.assertIn("unknown capabilities", str(ctx.exception))

    def test_manifest_rejects_missing_required_key(self) -> None:
        manifest = copy.deepcopy(STACK_MANIFEST)
        del manifest[0]["status"]
        with self.assertRaises(ProphetError) as ctx:
            validate_stack_manifest(manifest)
        self.assertIn("missing keys", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
