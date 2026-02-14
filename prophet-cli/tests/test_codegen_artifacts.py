from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "prophet-cli" / "src"))

from prophet_cli.codegen.artifacts import managed_existing_files
from prophet_cli.codegen.artifacts import remove_stale_outputs
from prophet_cli.codegen.artifacts import write_outputs


class CodegenArtifactsTests(unittest.TestCase):
    def test_manifest_driven_managed_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prophet-artifacts-manifest-") as tmp:
            root = Path(tmp)
            manifest_path = root / "gen" / "manifest" / "generated-files.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "outputs": [
                            {"path": "gen/sql/schema.sql", "sha256": "abc"},
                            {"path": "gen/openapi/openapi.yaml", "sha256": "def"},
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            managed = managed_existing_files(root, "gen")
            self.assertIn("gen/sql/schema.sql", managed)
            self.assertIn("gen/openapi/openapi.yaml", managed)
            self.assertIn("gen/manifest/generated-files.json", managed)

    def test_remove_stale_outputs_respects_desired_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prophet-artifacts-stale-") as tmp:
            root = Path(tmp)
            write_outputs(
                {
                    "gen/sql/schema.sql": "schema\n",
                    "gen/openapi/openapi.yaml": "openapi\n",
                },
                root,
            )
            remove_stale_outputs(root, "gen", {"gen/sql/schema.sql": "schema\n"})
            self.assertTrue((root / "gen" / "sql" / "schema.sql").exists())
            self.assertFalse((root / "gen" / "openapi" / "openapi.yaml").exists())


if __name__ == "__main__":
    unittest.main()

