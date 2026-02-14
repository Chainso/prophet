from __future__ import annotations

import os
import copy
import json
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "prophet-cli" / "src"))

from prophet_cli.cli import build_generated_outputs
from prophet_cli.cli import build_ir
from prophet_cli.cli import compare_irs
from prophet_cli.cli import load_config
from prophet_cli.cli import parse_ontology
from prophet_cli.cli import resolve_migration_runtime_modes
from prophet_cli.cli import validate_ontology

ROOT = PROJECT_ROOT
EXAMPLE_ROOT = ROOT / "examples" / "java" / "prophet_example_spring"


@contextmanager
def pushd(path: Path):
    old = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def build_outputs_from_example() -> tuple[dict[str, str], dict]:
    cfg = load_config(EXAMPLE_ROOT / "prophet.yaml")
    ontology = parse_ontology((EXAMPLE_ROOT / "ontology" / "local" / "main.prophet").read_text(encoding="utf-8"))
    errors = validate_ontology(ontology, strict_enums=bool(cfg.get("compatibility", {}).get("strict_enums", False)))
    if errors:
        raise AssertionError(f"Example ontology failed validation: {errors}")

    with pushd(EXAMPLE_ROOT):
        ir = build_ir(ontology, cfg)
        outputs = build_generated_outputs(ir, cfg)
    return outputs, ir


class CodegenSnapshotTests(unittest.TestCase):
    def test_generated_outputs_match_example_snapshot(self) -> None:
        outputs, _ = build_outputs_from_example()

        expected: dict[str, str] = {}
        for rel in outputs:
            full = EXAMPLE_ROOT / rel
            self.assertTrue(full.exists(), f"missing generated snapshot file: {full}")
            expected[rel] = full.read_text(encoding="utf-8")

        self.assertEqual(set(outputs.keys()), set(expected.keys()))
        for rel in sorted(outputs):
            self.assertEqual(outputs[rel], expected[rel], f"mismatch in {rel}")

    def test_codegen_is_deterministic(self) -> None:
        outputs_a, ir_a = build_outputs_from_example()
        outputs_b, ir_b = build_outputs_from_example()

        self.assertEqual(ir_a["ir_hash"], ir_b["ir_hash"])
        self.assertEqual(ir_a, ir_b)
        self.assertEqual(outputs_a, outputs_b)

    def test_migration_generation_and_spring_autodetect_behavior(self) -> None:
        outputs, _ = build_outputs_from_example()

        self.assertIn("gen/migrations/flyway/V1__prophet_init.sql", outputs)
        self.assertIn("gen/migrations/liquibase/db.changelog-master.yaml", outputs)
        self.assertIn("gen/migrations/liquibase/prophet/changelog-master.yaml", outputs)
        self.assertIn("gen/migrations/liquibase/prophet/0001-init.sql", outputs)
        self.assertNotIn("gen/migrations/flyway/V2__prophet_delta.sql", outputs)
        self.assertNotIn("gen/migrations/liquibase/prophet/0002-delta.sql", outputs)
        self.assertNotIn("gen/migrations/delta/report.json", outputs)

        spring_db_keys = [
            key for key in outputs if key.startswith("gen/spring-boot/src/main/resources/db/")
        ]
        self.assertEqual(
            spring_db_keys,
            [],
            "spring runtime migration resources should only be generated when Flyway/Liquibase is detected in host Gradle config",
        )

    def test_migration_runtime_mode_warnings_when_nothing_detected(self) -> None:
        cfg = {
            "generation": {
                "targets": ["sql", "openapi", "spring_boot", "flyway", "liquibase"],
            }
        }
        with tempfile.TemporaryDirectory(prefix="prophet-modes-none-") as tmp:
            requested, detected, enabled, warnings = resolve_migration_runtime_modes(cfg, Path(tmp))

        self.assertEqual(requested, {"flyway", "liquibase"})
        self.assertEqual(detected, set())
        self.assertEqual(enabled, set())
        self.assertTrue(any("Flyway target is enabled" in warning for warning in warnings))
        self.assertTrue(any("Liquibase target is enabled" in warning for warning in warnings))

    def test_migration_runtime_mode_warnings_when_both_detected(self) -> None:
        cfg = {
            "generation": {
                "targets": ["sql", "openapi", "spring_boot", "flyway", "liquibase"],
            }
        }
        with tempfile.TemporaryDirectory(prefix="prophet-modes-both-") as tmp:
            root = Path(tmp)
            (root / "build.gradle.kts").write_text(
                """plugins {
    id("org.flywaydb.flyway") version "10.0.0"
    id("org.liquibase.gradle") version "2.2.0"
}
dependencies {
    implementation("org.flywaydb:flyway-core")
    implementation("org.liquibase:liquibase-core")
}
""",
                encoding="utf-8",
            )
            requested, detected, enabled, warnings = resolve_migration_runtime_modes(cfg, root)

        self.assertEqual(requested, {"flyway", "liquibase"})
        self.assertEqual(detected, {"flyway", "liquibase"})
        self.assertEqual(enabled, {"flyway", "liquibase"})
        self.assertTrue(any("Both Flyway and Liquibase were detected" in warning for warning in warnings))

    def test_delta_migration_generated_when_baseline_is_behind(self) -> None:
        cfg = load_config(EXAMPLE_ROOT / "prophet.yaml")
        ontology = parse_ontology((EXAMPLE_ROOT / "ontology" / "local" / "main.prophet").read_text(encoding="utf-8"))
        ir = build_ir(ontology, cfg)

        baseline_ir = copy.deepcopy(ir)
        for obj in baseline_ir.get("objects", []):
            if obj.get("name") == "Order":
                obj["fields"] = [f for f in obj.get("fields", []) if f.get("name") != "total_amount"]
                break
        baseline_ir["ir_hash"] = "baseline-behind-for-delta-test"

        with tempfile.TemporaryDirectory(prefix="prophet-delta-") as tmp:
            root = Path(tmp)
            baseline_path = root / ".prophet" / "baselines" / "main.ir.json"
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            baseline_path.write_text(json.dumps(baseline_ir, indent=2) + "\n", encoding="utf-8")

            outputs = build_generated_outputs(ir, cfg, root=root)

        self.assertIn("gen/migrations/flyway/V2__prophet_delta.sql", outputs)
        self.assertIn("gen/migrations/liquibase/prophet/0002-delta.sql", outputs)
        self.assertIn("gen/migrations/delta/report.json", outputs)
        self.assertIn("0002-delta.sql", outputs["gen/migrations/liquibase/prophet/changelog-master.yaml"])

        delta_sql = outputs["gen/migrations/flyway/V2__prophet_delta.sql"]
        self.assertIn("SAFETY: backfill_required=true", delta_sql)
        self.assertIn("alter table orders add column if not exists total_amount", delta_sql)

    def test_delta_report_summary_and_rename_hints(self) -> None:
        cfg = load_config(EXAMPLE_ROOT / "prophet.yaml")
        ontology = parse_ontology((EXAMPLE_ROOT / "ontology" / "local" / "main.prophet").read_text(encoding="utf-8"))
        ir = build_ir(ontology, cfg)

        baseline_ir = copy.deepcopy(ir)
        for obj in baseline_ir.get("objects", []):
            if obj.get("name") == "Order":
                for field in obj.get("fields", []):
                    if field.get("name") == "discount_code":
                        field["id"] = "fld_order_coupon_code"
                        field["name"] = "coupon_code"
                        break
            if obj.get("name") == "User":
                obj["id"] = "obj_customer_legacy"
        baseline_ir["ir_hash"] = "baseline-rename-hints-test"

        with tempfile.TemporaryDirectory(prefix="prophet-delta-rename-") as tmp:
            root = Path(tmp)
            baseline_path = root / ".prophet" / "baselines" / "main.ir.json"
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            baseline_path.write_text(json.dumps(baseline_ir, indent=2) + "\n", encoding="utf-8")
            outputs = build_generated_outputs(ir, cfg, root=root)

        report = json.loads(outputs["gen/migrations/delta/report.json"])
        summary = report.get("summary", {})
        self.assertGreaterEqual(summary.get("manual_review_count", 0), 1)
        self.assertGreaterEqual(summary.get("destructive_count", 0), 1)
        self.assertIn("safe_auto_apply_count", summary)
        findings = report.get("findings", [])
        self.assertTrue(any(item.get("kind") == "object_rename_hint" for item in findings))
        self.assertTrue(any(item.get("kind") == "column_rename_hint" for item in findings))

    def test_query_contract_path_change_is_breaking(self) -> None:
        cfg = load_config(EXAMPLE_ROOT / "prophet.yaml")
        ontology = parse_ontology((EXAMPLE_ROOT / "ontology" / "local" / "main.prophet").read_text(encoding="utf-8"))
        old_ir = build_ir(ontology, cfg)
        new_ir = copy.deepcopy(old_ir)
        for obj in new_ir.get("objects", []):
            if obj.get("id") == "obj_order":
                obj["name"] = "Purchase"
                break
        new_ir["query_contracts"] = []
        new_ir["query_contracts_version"] = "outdated"

        level, reasons = compare_irs(old_ir, new_ir)
        self.assertEqual(level, "breaking")
        self.assertTrue(any("query path changed: object=obj_order" in reason for reason in reasons))

    def test_field_order_only_change_is_non_functional(self) -> None:
        cfg = load_config(EXAMPLE_ROOT / "prophet.yaml")
        ontology = parse_ontology((EXAMPLE_ROOT / "ontology" / "local" / "main.prophet").read_text(encoding="utf-8"))
        old_ir = build_ir(ontology, cfg)
        new_ir = copy.deepcopy(old_ir)
        for obj in new_ir.get("objects", []):
            if obj.get("id") == "obj_order":
                obj["fields"] = list(reversed(obj.get("fields", [])))
                break
        new_ir["query_contracts"] = []
        new_ir["query_contracts_version"] = "outdated"

        level, reasons = compare_irs(old_ir, new_ir)
        self.assertEqual(level, "non_functional")
        self.assertFalse(any("query operator" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
