from __future__ import annotations

import re
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]


class VersionSyncTests(unittest.TestCase):
    def test_toolchain_version_matches_pyproject(self) -> None:
        pyproject_text = (PROJECT_ROOT / "prophet-cli" / "pyproject.toml").read_text(encoding="utf-8")
        cli_text = (PROJECT_ROOT / "prophet-cli" / "src" / "prophet_cli" / "cli.py").read_text(encoding="utf-8")

        pyproject_match = re.search(r'^version\s*=\s*"([^"]+)"\s*$', pyproject_text, re.MULTILINE)
        self.assertIsNotNone(pyproject_match, "Unable to find [project].version in pyproject.toml")

        toolchain_match = re.search(r'^TOOLCHAIN_VERSION\s*=\s*"([^"]+)"\s*$', cli_text, re.MULTILINE)
        self.assertIsNotNone(toolchain_match, "Unable to find TOOLCHAIN_VERSION in cli.py")

        self.assertEqual(
            pyproject_match.group(1),  # type: ignore[union-attr]
            toolchain_match.group(1),  # type: ignore[union-attr]
            "pyproject version and TOOLCHAIN_VERSION must stay in sync for releases",
        )


if __name__ == "__main__":
    unittest.main()
