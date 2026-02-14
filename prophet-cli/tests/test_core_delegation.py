from __future__ import annotations

import sys
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "prophet-cli" / "src"))

from prophet_cli import cli
from prophet_cli.core import compatibility as core_compat
from prophet_cli.core import ir as core_ir
from prophet_cli.core import parser as core_parser
from prophet_cli.core import validation as core_validation

EXAMPLE_ROOT = PROJECT_ROOT / "examples" / "java" / "prophet_example_spring"


class CoreDelegationTests(unittest.TestCase):
    def test_cli_function_delegation_targets_core_modules(self) -> None:
        self.assertIs(cli.parse_ontology, core_parser.parse_ontology)
        self.assertIs(cli.validate_ontology, core_validation.validate_ontology)
        self.assertIs(cli.compare_irs, core_compat.compare_irs)
        self.assertIs(cli.required_level_to_bump, core_compat.required_level_to_bump)

    def test_cli_build_ir_matches_core_build_ir(self) -> None:
        cfg = cli.load_config(EXAMPLE_ROOT / "prophet.yaml")
        ontology_text = (EXAMPLE_ROOT / "ontology" / "local" / "main.prophet").read_text(encoding="utf-8")
        ont = cli.parse_ontology(ontology_text)

        cli_ir = cli.build_ir(ont, cfg)
        core_generated_ir = core_ir.build_ir(
            ont,
            cfg,
            toolchain_version=cli.TOOLCHAIN_VERSION,
            ir_version=cli.IR_VERSION,
        )
        self.assertEqual(cli_ir, core_generated_ir)


if __name__ == "__main__":
    unittest.main()

