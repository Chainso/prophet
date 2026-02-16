from __future__ import annotations

import copy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "prophet-cli" / "src"))

from prophet_cli.cli import build_generated_outputs
from prophet_cli.cli import build_ir
from prophet_cli.cli import parse_ontology

EXAMPLE_ONTOLOGY_PATH = (
    PROJECT_ROOT
    / "examples"
    / "turtle"
    / "prophet_example_turtle_minimal"
    / "ontology"
    / "local"
    / "main.prophet"
)
BASE_TURTLE_PATH = PROJECT_ROOT / "prophet.ttl"


class TurtleTargetTests(unittest.TestCase):
    def _cfg(self) -> dict:
        return {
            "project": {"ontology_file": str(EXAMPLE_ONTOLOGY_PATH)},
            "generation": {
                "out_dir": "gen",
                "stack": {"id": "java_spring_jpa"},
                "targets": ["turtle", "manifest"],
            },
            "compatibility": {"strict_enums": False},
        }

    def test_turtle_target_generates_projection_for_minimal_ontology_example(self) -> None:
        ontology = parse_ontology(EXAMPLE_ONTOLOGY_PATH.read_text(encoding="utf-8"))
        cfg = self._cfg()
        ir = build_ir(ontology, cfg)
        with tempfile.TemporaryDirectory(prefix="prophet-turtle-example-") as tmp:
            outputs = build_generated_outputs(ir, cfg, root=Path(tmp))

        self.assertIn("gen/turtle/ontology.ttl", outputs)
        turtle = outputs["gen/turtle/ontology.ttl"]
        self.assertIn("@prefix prophet:", turtle)
        self.assertIn("@prefix support_local:", turtle)
        self.assertIn("prophet:LocalOntology", turtle)
        self.assertIn("prophet:CustomType", turtle)
        self.assertIn("prophet:ObjectModel", turtle)
        self.assertIn("prophet:Process", turtle)
        self.assertIn("prophet:EventTrigger", turtle)
        self.assertIn("prophet:hasConstraint", turtle)
        self.assertIn("sh:NodeShape", turtle)
        self.assertIn('sh:pattern "^[^@\\\\s]+@[^@\\\\s]+\\\\.[^@\\\\s]+$"', turtle)
        self.assertNotIn('sh:pattern "^[^@\\\\\\\\s]+', turtle)

    def test_turtle_target_output_is_deterministic(self) -> None:
        ontology = parse_ontology(EXAMPLE_ONTOLOGY_PATH.read_text(encoding="utf-8"))
        cfg = self._cfg()
        ir = build_ir(ontology, cfg)

        with tempfile.TemporaryDirectory(prefix="prophet-turtle-deterministic-") as tmp:
            root = Path(tmp)
            outputs_a = build_generated_outputs(copy.deepcopy(ir), cfg, root=root)
            outputs_b = build_generated_outputs(copy.deepcopy(ir), cfg, root=root)

        self.assertEqual(outputs_a["gen/turtle/ontology.ttl"], outputs_b["gen/turtle/ontology.ttl"])

    def test_turtle_target_conforms_to_prophet_shacl(self) -> None:
        if shutil.which("pyshacl") is None:
            self.fail("pyshacl binary is required for Turtle SHACL conformance tests")

        ontology = parse_ontology(EXAMPLE_ONTOLOGY_PATH.read_text(encoding="utf-8"))
        cfg = self._cfg()
        ir = build_ir(ontology, cfg)
        with tempfile.TemporaryDirectory(prefix="prophet-turtle-shacl-") as tmp:
            root = Path(tmp)
            outputs = build_generated_outputs(ir, cfg, root=root)
            generated_turtle_path = root / "generated.ttl"
            generated_turtle_path.write_text(outputs["gen/turtle/ontology.ttl"], encoding="utf-8")

            result = subprocess.run(
                [
                    "pyshacl",
                    "-s",
                    str(BASE_TURTLE_PATH),
                    "-d",
                    str(BASE_TURTLE_PATH),
                    str(generated_turtle_path),
                    "-e",
                    str(BASE_TURTLE_PATH),
                    "--advanced",
                    "--inference",
                    "owlrl",
                    "--format",
                    "turtle",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"pyshacl failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
        )
        self.assertIn("sh:conforms true", result.stdout)


if __name__ == "__main__":
    unittest.main()
