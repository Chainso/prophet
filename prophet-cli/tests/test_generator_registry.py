from __future__ import annotations

import sys
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "prophet-cli" / "src"))

from prophet_cli.cli import registered_generators
from prophet_cli.codegen.stacks import supported_stack_table


class GeneratorRegistryTests(unittest.TestCase):
    def test_registered_generators_cover_implemented_stacks_only(self) -> None:
        rows = supported_stack_table()
        implemented = {row["id"] for row in rows if row.get("implemented")}
        planned = {row["id"] for row in rows if not row.get("implemented")}
        registered = set(registered_generators().keys())

        self.assertEqual(implemented, registered)
        self.assertTrue(registered.isdisjoint(planned))


if __name__ == "__main__":
    unittest.main()
