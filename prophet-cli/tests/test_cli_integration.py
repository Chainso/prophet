from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import os
from pathlib import Path


THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
CLI_MODULE = "prophet_cli"
EXAMPLE_ONTOLOGY = PROJECT_ROOT / "examples" / "java" / "prophet_example_spring" / "ontology" / "local" / "main.prophet"


def run_cli(cwd: Path, *args: str, expect_code: int = 0) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "prophet-cli" / "src")
    result = subprocess.run(
        [sys.executable, "-m", CLI_MODULE, *args],
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != expect_code:
        raise AssertionError(
            f"CLI exited with code {result.returncode} (expected {expect_code})\n"
            f"cmd: prophet {' '.join(args)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result


class CliIntegrationTests(unittest.TestCase):
    def test_stacks_command_lists_supported_matrix(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prophet-cli-stacks-") as tmp:
            root = Path(tmp)
            result = run_cli(root, "stacks")
            self.assertIn("java_spring_jpa", result.stdout)
            self.assertIn("node_express_typeorm", result.stdout)
            self.assertIn("python_django_orm", result.stdout)
            self.assertIn("[implemented]", result.stdout)
            self.assertIn("[planned]", result.stdout)

            json_result = run_cli(root, "stacks", "--json")
            payload = json.loads(json_result.stdout)
            self.assertIn("stacks", payload)
            self.assertTrue(any(item.get("id") == "java_spring_jpa" for item in payload["stacks"]))

    def test_end_to_end_cli_flow(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prophet-cli-it-") as tmp:
            root = Path(tmp)

            run_cli(root, "init")
            self.assertTrue((root / "prophet.yaml").exists())
            self.assertTrue((root / ".prophet" / "ir").exists())
            self.assertTrue((root / ".prophet" / "baselines").exists())

            ontology_dst = root / "domain" / "main.prophet"
            ontology_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(EXAMPLE_ONTOLOGY, ontology_dst)

            cfg_path = root / "prophet.yaml"
            cfg_text = cfg_path.read_text(encoding="utf-8")
            cfg_text = cfg_text.replace(
                "ontology_file: path/to/your-ontology.prophet",
                "ontology_file: domain/main.prophet",
            )
            cfg_path.write_text(cfg_text, encoding="utf-8")

            (root / "settings.gradle.kts").write_text('rootProject.name = "tmp-app"\n', encoding="utf-8")
            (root / "build.gradle.kts").write_text(
                """plugins {
    java
    id("org.springframework.boot") version "3.5.10"
    id("io.spring.dependency-management") version "1.1.7"
}

repositories {
    mavenCentral()
}

dependencies {
}
""",
                encoding="utf-8",
            )

            run_cli(root, "validate")
            run_cli(root, "plan")
            run_cli(root, "gen", "--wire-gradle")
            run_cli(root, "generate", "--verify-clean")
            run_cli(root, "check", "--show-reasons")

            self.assertTrue((root / "gen" / "sql" / "schema.sql").exists())
            self.assertTrue((root / "gen" / "openapi" / "openapi.yaml").exists())
            self.assertTrue((root / ".prophet" / "ir" / "current.ir.json").exists())

            settings_text = (root / "settings.gradle.kts").read_text(encoding="utf-8")
            build_text = (root / "build.gradle.kts").read_text(encoding="utf-8")
            self.assertIn('include(":prophet_generated")', settings_text)
            self.assertIn('implementation(project(":prophet_generated"))', build_text)

            schema_path = root / "gen" / "sql" / "schema.sql"
            schema_path.write_text(schema_path.read_text(encoding="utf-8") + "\n-- local change\n", encoding="utf-8")
            dirty_check = run_cli(root, "check", expect_code=1)
            self.assertIn("Generated outputs are not clean", dirty_check.stdout)
            self.assertIn("How to fix:", dirty_check.stdout)

            run_cli(root, "gen")
            run_cli(root, "clean")

            self.assertFalse((root / "gen").exists())
            self.assertFalse((root / ".prophet" / "ir" / "current.ir.json").exists())
            self.assertFalse((root / ".prophet" / "cache" / "generation.json").exists())

            settings_after = (root / "settings.gradle.kts").read_text(encoding="utf-8")
            build_after = (root / "build.gradle.kts").read_text(encoding="utf-8")
            self.assertNotIn('include(":prophet_generated")', settings_after)
            self.assertNotIn('implementation(project(":prophet_generated"))', build_after)

            verify_after_clean = run_cli(root, "generate", "--verify-clean", expect_code=1)
            self.assertIn("Generated outputs are not clean", verify_after_clean.stdout)

    def test_generate_skip_unchanged_uses_generation_cache(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prophet-cli-skip-unchanged-") as tmp:
            root = Path(tmp)
            run_cli(root, "init")

            ontology_dst = root / "domain" / "main.prophet"
            ontology_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(EXAMPLE_ONTOLOGY, ontology_dst)

            cfg_path = root / "prophet.yaml"
            cfg_text = cfg_path.read_text(encoding="utf-8")
            cfg_text = cfg_text.replace(
                "ontology_file: path/to/your-ontology.prophet",
                "ontology_file: domain/main.prophet",
            )
            cfg_path.write_text(cfg_text, encoding="utf-8")

            run_cli(root, "gen")
            cache_file = root / ".prophet" / "cache" / "generation.json"
            self.assertTrue(cache_file.exists())

            skipped = run_cli(root, "gen", "--skip-unchanged")
            self.assertIn("Skipped generation: configuration and IR unchanged.", skipped.stdout)

    def test_hooks_command_lists_generated_extension_points(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prophet-cli-hooks-") as tmp:
            root = Path(tmp)
            run_cli(root, "init")

            ontology_dst = root / "domain" / "main.prophet"
            ontology_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(EXAMPLE_ONTOLOGY, ontology_dst)

            cfg_path = root / "prophet.yaml"
            cfg_text = cfg_path.read_text(encoding="utf-8")
            cfg_text = cfg_text.replace(
                "ontology_file: path/to/your-ontology.prophet",
                "ontology_file: domain/main.prophet",
            )
            cfg_path.write_text(cfg_text, encoding="utf-8")

            missing = run_cli(root, "hooks", expect_code=1)
            self.assertIn("Extension hook manifest not found", missing.stderr)
            self.assertIn("Run `prophet gen` first", missing.stderr)

            run_cli(root, "gen")
            result = run_cli(root, "hooks")
            self.assertIn("Extension hooks", result.stdout)
            self.assertIn("createOrder", result.stdout)

            json_result = run_cli(root, "hooks", "--json")
            payload = json.loads(json_result.stdout)
            action_names = {item.get("action_name") for item in payload.get("hooks", [])}
            self.assertIn("createOrder", action_names)

    def test_missing_config_includes_actionable_hint(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prophet-cli-hints-") as tmp:
            root = Path(tmp)
            result = run_cli(root, "validate", expect_code=1)
            self.assertIn("prophet.yaml not found", result.stderr)
            self.assertIn("Run `prophet init`", result.stderr)

    def test_check_json_outputs_structured_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prophet-cli-check-json-") as tmp:
            root = Path(tmp)
            run_cli(root, "init")

            ontology_dst = root / "domain" / "main.prophet"
            ontology_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(EXAMPLE_ONTOLOGY, ontology_dst)

            cfg_path = root / "prophet.yaml"
            cfg_text = cfg_path.read_text(encoding="utf-8")
            cfg_text = cfg_text.replace(
                "ontology_file: path/to/your-ontology.prophet",
                "ontology_file: domain/main.prophet",
            )
            cfg_path.write_text(cfg_text, encoding="utf-8")

            run_cli(root, "gen")
            clean_result = run_cli(root, "check", "--json", "--show-reasons")
            clean_payload = json.loads(clean_result.stdout)
            self.assertTrue(clean_payload["ok"])
            self.assertTrue(clean_payload["validation"]["passed"])
            self.assertTrue(clean_payload["generation"]["clean"])
            self.assertTrue(clean_payload["compatibility"]["baseline_found"])
            self.assertTrue(clean_payload["compatibility"]["passed"])
            self.assertIn("delta_migration", clean_payload)
            self.assertIn("migrations", clean_payload)

            schema_path = root / "gen" / "sql" / "schema.sql"
            schema_path.write_text(schema_path.read_text(encoding="utf-8") + "\n-- dirty\n", encoding="utf-8")
            dirty_result = run_cli(root, "check", "--json", expect_code=1)
            dirty_payload = json.loads(dirty_result.stdout)
            self.assertFalse(dirty_payload["ok"])
            self.assertFalse(dirty_payload["generation"]["clean"])
            self.assertGreaterEqual(len(dirty_payload["generation"]["dirty_files"]), 1)

    def test_plan_json_outputs_structured_changes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prophet-cli-plan-json-") as tmp:
            root = Path(tmp)
            run_cli(root, "init")

            ontology_dst = root / "domain" / "main.prophet"
            ontology_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(EXAMPLE_ONTOLOGY, ontology_dst)

            cfg_path = root / "prophet.yaml"
            cfg_text = cfg_path.read_text(encoding="utf-8")
            cfg_text = cfg_text.replace(
                "ontology_file: path/to/your-ontology.prophet",
                "ontology_file: domain/main.prophet",
            )
            cfg_path.write_text(cfg_text, encoding="utf-8")

            result = run_cli(root, "plan", "--json", "--show-reasons")
            payload = json.loads(result.stdout)
            self.assertIn("stack", payload)
            self.assertIn("changes", payload)
            self.assertIn("summary", payload)
            self.assertEqual(payload["stack"]["id"], "java_spring_jpa")
            self.assertEqual(payload["stack"]["status"], "implemented")
            self.assertTrue(payload["stack"]["implemented"])
            self.assertIn("change_count", payload["summary"])

    def test_version_check_succeeds_after_generation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prophet-cli-version-check-") as tmp:
            root = Path(tmp)
            run_cli(root, "init")

            ontology_dst = root / "domain" / "main.prophet"
            ontology_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(EXAMPLE_ONTOLOGY, ontology_dst)

            cfg_path = root / "prophet.yaml"
            cfg_text = cfg_path.read_text(encoding="utf-8")
            cfg_text = cfg_text.replace(
                "ontology_file: path/to/your-ontology.prophet",
                "ontology_file: domain/main.prophet",
            )
            cfg_path.write_text(cfg_text, encoding="utf-8")

            run_cli(root, "gen")
            result = run_cli(root, "version", "check")
            self.assertIn("Compatibility result", result.stdout)
            self.assertIn("Required version bump", result.stdout)

    def test_tuple_stack_config_works_without_stack_id(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prophet-cli-stack-tuple-") as tmp:
            root = Path(tmp)
            run_cli(root, "init")

            ontology_dst = root / "domain" / "main.prophet"
            ontology_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(EXAMPLE_ONTOLOGY, ontology_dst)

            cfg_path = root / "prophet.yaml"
            cfg_text = cfg_path.read_text(encoding="utf-8")
            cfg_text = cfg_text.replace(
                "ontology_file: path/to/your-ontology.prophet",
                "ontology_file: domain/main.prophet",
            )
            cfg_text = cfg_text.replace(
                "  stack:\n    id: java_spring_jpa",
                "  stack:\n    language: java\n    framework: spring_boot\n    orm: jpa",
            )
            cfg_path.write_text(cfg_text, encoding="utf-8")

            result = run_cli(root, "plan", "--json")
            payload = json.loads(result.stdout)
            self.assertEqual(payload["stack"]["id"], "java_spring_jpa")
            self.assertEqual(payload["stack"]["status"], "implemented")


if __name__ == "__main__":
    unittest.main()
