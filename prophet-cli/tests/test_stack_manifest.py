from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "prophet-cli" / "src"))

from prophet_cli.codegen.stack_manifest import STACK_MANIFEST_DOCUMENT
from prophet_cli.codegen.stack_manifest import validate_stack_manifest_document
from prophet_cli.core.errors import ProphetError


class StackManifestTests(unittest.TestCase):
    def test_manifest_validates_current_entries(self) -> None:
        normalized = validate_stack_manifest_document(STACK_MANIFEST_DOCUMENT)
        self.assertEqual(normalized["schema_version"], 1)
        self.assertGreaterEqual(len(normalized["stacks"]), 1)
        self.assertEqual(normalized["stacks"][0]["id"], "java_spring_jpa")

    def test_manifest_rejects_duplicate_ids(self) -> None:
        manifest = copy.deepcopy(STACK_MANIFEST_DOCUMENT)
        duplicate = copy.deepcopy(manifest["stacks"][0])
        duplicate["language"] = "java2"
        duplicate["framework"] = "spring_boot2"
        duplicate["orm"] = "jpa2"
        manifest["stacks"].append(duplicate)
        with self.assertRaises(ProphetError) as ctx:
            validate_stack_manifest_document(manifest)
        self.assertIn("duplicate id", str(ctx.exception))

    def test_manifest_rejects_unknown_capability(self) -> None:
        manifest = copy.deepcopy(STACK_MANIFEST_DOCUMENT)
        manifest["stacks"][0]["capabilities"] = manifest["stacks"][0]["capabilities"] + ["does_not_exist"]
        with self.assertRaises(ProphetError) as ctx:
            validate_stack_manifest_document(manifest)
        self.assertIn("unknown capabilities", str(ctx.exception))

    def test_manifest_rejects_missing_required_key(self) -> None:
        manifest = copy.deepcopy(STACK_MANIFEST_DOCUMENT)
        del manifest["stacks"][0]["status"]
        with self.assertRaises(ProphetError) as ctx:
            validate_stack_manifest_document(manifest)
        self.assertIn("missing keys", str(ctx.exception))

    def test_manifest_rejects_unknown_default_target(self) -> None:
        manifest = copy.deepcopy(STACK_MANIFEST_DOCUMENT)
        manifest["stacks"][0]["default_targets"].append("nonexistent")
        with self.assertRaises(ProphetError) as ctx:
            validate_stack_manifest_document(manifest)
        self.assertIn("unknown default_targets values", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
