from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "prophet-cli" / "src"))

from prophet_cli.cli import build_generated_outputs
from prophet_cli.cli import build_ir
from prophet_cli.cli import load_config
from prophet_cli.cli import parse_ontology
from prophet_cli.targets.node_express.autodetect import apply_node_autodetect
from prophet_cli.targets.node_express.autodetect import detect_node_stack

EXAMPLE_ROOT = PROJECT_ROOT / "examples" / "java" / "prophet_example_spring"


class NodeTargetTests(unittest.TestCase):
    def _base_cfg(self) -> dict:
        cfg = load_config(EXAMPLE_ROOT / "prophet.yaml")
        cfg = copy.deepcopy(cfg)
        cfg["generation"]["targets"] = ["sql", "openapi", "node_express", "manifest"]
        return cfg

    def _ontology(self):
        return parse_ontology((EXAMPLE_ROOT / "ontology" / "local" / "main.prophet").read_text(encoding="utf-8"))

    def test_node_prisma_stack_generates_expected_artifacts(self) -> None:
        cfg = self._base_cfg()
        cfg["generation"]["stack"] = {"id": "node_express_prisma"}
        cfg["generation"]["targets"] = ["sql", "openapi", "node_express", "prisma", "manifest"]

        ir = build_ir(self._ontology(), cfg)
        with tempfile.TemporaryDirectory(prefix="prophet-node-prisma-") as tmp:
            outputs = build_generated_outputs(ir, cfg, root=Path(tmp))

        self.assertIn("gen/node-express/src/generated/index.ts", outputs)
        self.assertIn("gen/node-express/src/generated/action-routes.ts", outputs)
        self.assertIn("gen/node-express/src/generated/prisma-adapters.ts", outputs)
        self.assertIn("gen/node-express/prisma/schema.prisma", outputs)
        self.assertIn("gen/manifest/generated-files.json", outputs)

        manifest = json.loads(outputs["gen/manifest/generated-files.json"])
        self.assertEqual(manifest["stack"]["id"], "node_express_prisma")

    def test_node_typeorm_stack_generates_expected_artifacts(self) -> None:
        cfg = self._base_cfg()
        cfg["generation"]["stack"] = {"id": "node_express_typeorm"}
        cfg["generation"]["targets"] = ["sql", "openapi", "node_express", "typeorm", "manifest"]

        ir = build_ir(self._ontology(), cfg)
        with tempfile.TemporaryDirectory(prefix="prophet-node-typeorm-") as tmp:
            outputs = build_generated_outputs(ir, cfg, root=Path(tmp))

        self.assertIn("gen/node-express/src/generated/index.ts", outputs)
        self.assertIn("gen/node-express/src/generated/query-routes.ts", outputs)
        self.assertIn("gen/node-express/src/generated/typeorm-entities.ts", outputs)
        self.assertIn("gen/node-express/src/generated/typeorm-adapters.ts", outputs)

        manifest = json.loads(outputs["gen/manifest/generated-files.json"])
        self.assertEqual(manifest["stack"]["id"], "node_express_typeorm")

    def test_autodetect_selects_node_prisma_and_rewrites_default_targets(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prophet-autodetect-prisma-") as tmp:
            root = Path(tmp)
            (root / "package.json").write_text(
                json.dumps(
                    {
                        "name": "node-app",
                        "type": "module",
                        "dependencies": {
                            "express": "^4.19.2",
                            "@prisma/client": "^5.0.0",
                        },
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")

            cfg = {
                "generation": {
                    "stack": {},
                    "targets": ["sql", "openapi", "spring_boot", "flyway", "liquibase"],
                }
            }
            mutated = apply_node_autodetect(copy.deepcopy(cfg), root)
            self.assertEqual(mutated["generation"]["stack"]["id"], "node_express_prisma")
            self.assertEqual(mutated["generation"]["targets"], ["sql", "openapi", "node_express", "prisma", "manifest"])

            report = mutated.get("_autodetect", {})
            self.assertEqual(report.get("package_manager"), "pnpm")
            self.assertEqual(report.get("confidence"), "high")

    def test_autodetect_reports_ambiguous_orm_choice(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prophet-autodetect-ambiguous-") as tmp:
            root = Path(tmp)
            (root / "package.json").write_text(
                json.dumps(
                    {
                        "name": "node-app",
                        "dependencies": {
                            "express": "^4.19.2",
                            "@prisma/client": "^5.0.0",
                            "typeorm": "^0.3.20",
                        },
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            report = detect_node_stack(root)
            self.assertEqual(report.get("confidence"), "ambiguous")
            self.assertEqual(report.get("stack_id"), "")
            self.assertTrue(any("both Prisma and TypeORM" in item for item in report.get("warnings", [])))


if __name__ == "__main__":
    unittest.main()
