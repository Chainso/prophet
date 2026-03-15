from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "prophet-cli" / "src"))

from prophet_cli.cli import parse_ontology
from prophet_cli.cli import validate_ontology

EXAMPLE_ONTOLOGY_PATHS = tuple(sorted(PROJECT_ROOT.glob("examples/**/ontology/local/main.prophet")))
FORBIDDEN_PATTERNS = (
    re.compile(r"^\s*signal\s+\w+", re.MULTILINE),
    re.compile(r"^\s*output\s+signal\s+\w+", re.MULTILINE),
    re.compile(r"^\s*output\s+transition\s+\S+", re.MULTILINE),
    re.compile(r"^\s*state\s*\{", re.MULTILINE),
    re.compile(r"^\s*transition\s+\w+\s*\{", re.MULTILINE),
)


class ExampleOntologyTests(unittest.TestCase):
    def test_all_checked_in_example_ontologies_parse_and_validate(self) -> None:
        self.assertGreaterEqual(len(EXAMPLE_ONTOLOGY_PATHS), 11)

        failures: list[str] = []
        for path in EXAMPLE_ONTOLOGY_PATHS:
            ontology = parse_ontology(path.read_text(encoding="utf-8"))
            errors = validate_ontology(ontology)
            if errors:
                rendered = ", ".join(str(error) for error in errors)
                failures.append(f"{path.relative_to(PROJECT_ROOT)} -> {rendered}")

        if failures:
            self.fail("Example ontology validation failed:\n" + "\n".join(failures))

    def test_checked_in_example_ontologies_use_current_event_and_state_model(self) -> None:
        offenders: list[str] = []
        for path in EXAMPLE_ONTOLOGY_PATHS:
            text = path.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.search(text):
                    offenders.append(f"{path.relative_to(PROJECT_ROOT)} matches {pattern.pattern}")

        if offenders:
            self.fail("Example ontologies still use removed DSL syntax:\n" + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
