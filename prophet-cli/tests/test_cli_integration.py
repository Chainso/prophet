from __future__ import annotations

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

            settings_after = (root / "settings.gradle.kts").read_text(encoding="utf-8")
            build_after = (root / "build.gradle.kts").read_text(encoding="utf-8")
            self.assertNotIn('include(":prophet_generated")', settings_after)
            self.assertNotIn('implementation(project(":prophet_generated"))', build_after)

            verify_after_clean = run_cli(root, "generate", "--verify-clean", expect_code=1)
            self.assertIn("Generated outputs are not clean", verify_after_clean.stdout)

    def test_missing_config_includes_actionable_hint(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prophet-cli-hints-") as tmp:
            root = Path(tmp)
            result = run_cli(root, "validate", expect_code=1)
            self.assertIn("prophet.yaml not found", result.stderr)
            self.assertIn("Run `prophet init`", result.stderr)


if __name__ == "__main__":
    unittest.main()
