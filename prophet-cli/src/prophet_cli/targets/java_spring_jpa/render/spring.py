from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from prophet_cli.core.config import cfg_get
from prophet_cli.codegen.rendering import render_sql
from prophet_cli.targets.java_common.render.support import annotate_generated_java_files
from prophet_cli.targets.java_common.render.support import effective_base_package
from prophet_cli.targets.java_spring_jpa.render.common import render_action_runtime_artifacts
from prophet_cli.targets.java_spring_jpa.render.common import render_contract_artifacts
from prophet_cli.targets.java_spring_jpa.render.common import render_domain_artifacts
from prophet_cli.targets.java_spring_jpa.render.common import render_transition_runtime_artifacts
from prophet_cli.targets.java_spring_jpa.render.orm import render_jpa_persistence_artifacts
from prophet_cli.targets.java_spring_jpa.render.orm import render_jpa_query_artifacts
from prophet_cli.targets.runtime_versions import resolve_java_runtime_group
from prophet_cli.targets.runtime_versions import resolve_runtime_version

def render_gradle_file(
    boot_version: str,
    dependency_management_version: str,
    toolchain_version: str,
    runtime_group: str,
    runtime_version: str,
) -> str:
    return f"""plugins {{
    java
    id(\"org.springframework.boot\") version \"{boot_version}\"
    id(\"io.spring.dependency-management\") version \"{dependency_management_version}\"
}}

group = \"com.example\"
version = \"{toolchain_version}\"

java {{
    toolchain {{
        languageVersion = JavaLanguageVersion.of(21)
    }}
}}

repositories {{
    mavenLocal()
    mavenCentral()
}}

dependencies {{
    implementation(\"org.springframework.boot:spring-boot-starter-web\")
    implementation(\"org.springframework.boot:spring-boot-starter-validation\")
    implementation(\"org.springframework.boot:spring-boot-starter-data-jpa\")
    implementation(\"{runtime_group}:prophet-events-runtime:{runtime_version}\")
    runtimeOnly(\"org.postgresql:postgresql\")
    testImplementation(\"org.springframework.boot:spring-boot-starter-test\")
}}
"""


def detect_gradle_plugin_versions(
    root: Path,
    fallback_boot_version: str,
    fallback_dependency_management_version: str,
) -> Tuple[str, str]:
    build_kts = root / "build.gradle.kts"
    build_groovy = root / "build.gradle"
    build_path: Optional[Path] = build_kts if build_kts.exists() else build_groovy if build_groovy.exists() else None
    if build_path is None:
        return fallback_boot_version, fallback_dependency_management_version

    text = build_path.read_text(encoding="utf-8")

    boot_version = fallback_boot_version
    dep_mgmt_version = fallback_dependency_management_version

    boot_patterns = [
        re.compile(r'id\("org\.springframework\.boot"\)\s+version\s+"([^"]+)"'),
        re.compile(r"id\s+'org\.springframework\.boot'\s+version\s+'([^']+)'"),
    ]
    dep_patterns = [
        re.compile(r'id\("io\.spring\.dependency-management"\)\s+version\s+"([^"]+)"'),
        re.compile(r"id\s+'io\.spring\.dependency-management'\s+version\s+'([^']+)'"),
    ]

    for pattern in boot_patterns:
        m = pattern.search(text)
        if m:
            boot_version = m.group(1)
            break

    for pattern in dep_patterns:
        m = pattern.search(text)
        if m:
            dep_mgmt_version = m.group(1)
            break

    return boot_version, dep_mgmt_version


def detect_gradle_migration_tools(root: Path) -> set[str]:
    build_kts = root / "build.gradle.kts"
    build_groovy = root / "build.gradle"
    build_path: Optional[Path] = build_kts if build_kts.exists() else build_groovy if build_groovy.exists() else None
    if build_path is None:
        return set()

    text = build_path.read_text(encoding="utf-8")
    tools: set[str] = set()

    if (
        "org.flywaydb:flyway-core" in text
        or 'id("org.flywaydb.flyway")' in text
        or "id 'org.flywaydb.flyway'" in text
    ):
        tools.add("flyway")
    if (
        "org.liquibase:liquibase-core" in text
        or 'id("org.liquibase.gradle")' in text
        or "id 'org.liquibase.gradle'" in text
    ):
        tools.add("liquibase")

    return tools


def resolve_migration_runtime_modes(cfg: Dict[str, Any], root: Path) -> Tuple[set[str], set[str], set[str], List[str]]:
    targets = set(cfg_get(cfg, ["generation", "targets"], ["sql", "openapi", "spring_boot", "flyway", "liquibase"]))
    requested = {"flyway", "liquibase"}.intersection(targets)
    detected = detect_gradle_migration_tools(root)
    enabled = requested.intersection(detected)
    warnings: List[str] = []

    if "flyway" in requested and "flyway" not in detected:
        warnings.append(
            "Flyway target is enabled, but Flyway was not detected in host Gradle config; "
            "skipping Spring runtime Flyway resource wiring."
        )
    if "liquibase" in requested and "liquibase" not in detected:
        warnings.append(
            "Liquibase target is enabled, but Liquibase was not detected in host Gradle config; "
            "skipping Spring runtime Liquibase resource wiring."
        )
    if "flyway" in enabled and "liquibase" in enabled:
        warnings.append(
            "Both Flyway and Liquibase were detected in host Gradle config; "
            "Spring runtime resources are generated for both. Ensure runtime activates only one migration engine."
        )

    return requested, detected, enabled, warnings


def render_liquibase_root_changelog() -> str:
    return (
        "# GENERATED FILE: do not edit directly.\n"
        "databaseChangeLog:\n"
        "  - include:\n"
        "      file: prophet/changelog-master.yaml\n"
        "      relativeToChangelogFile: true\n"
    )


def render_liquibase_prophet_changelog(include_delta: bool = False) -> str:
    changelog = (
        "# GENERATED FILE: do not edit directly.\n"
        "databaseChangeLog:\n"
        "  - changeSet:\n"
        "      id: prophet-0001-init\n"
        "      author: prophet-cli\n"
        "      changes:\n"
        "        - sqlFile:\n"
        "            path: 0001-init.sql\n"
        "            relativeToChangelogFile: true\n"
        "            splitStatements: true\n"
        "            stripComments: false\n"
    )
    if include_delta:
        changelog += (
            "  - changeSet:\n"
            "      id: prophet-0002-delta\n"
            "      author: prophet-cli\n"
            "      changes:\n"
            "        - sqlFile:\n"
            "            path: 0002-delta.sql\n"
            "            relativeToChangelogFile: true\n"
            "            splitStatements: true\n"
            "            stripComments: false\n"
        )
    return changelog


def render_spring_files(
    ir: Dict[str, Any],
    cfg: Dict[str, Any],
    root: Optional[Path] = None,
    generated_schema_sql: Optional[str] = None,
    delta_schema_sql: Optional[str] = None,
    toolchain_version: str = "0.0.0",
) -> Dict[str, str]:
    files: Dict[str, str] = {}

    configured_base_package = str(cfg_get(cfg, ["generation", "spring_boot", "base_package"], "com.example.prophet"))
    base_package = effective_base_package(configured_base_package, str(ir.get("ontology", {}).get("name", "prophet")))
    fallback_boot_version = str(cfg_get(cfg, ["generation", "spring_boot", "boot_version"], "3.3.2"))
    fallback_dep_mgmt_version = str(
        cfg_get(cfg, ["generation", "spring_boot", "dependency_management_version"], "1.1.6")
    )
    work_root = root if root is not None else Path.cwd()
    runtime_group = resolve_java_runtime_group(work_root)
    runtime_version = resolve_runtime_version(work_root)
    boot_version, dep_mgmt_version = detect_gradle_plugin_versions(
        work_root,
        fallback_boot_version,
        fallback_dep_mgmt_version,
    )
    _, _, enabled_modes, _ = resolve_migration_runtime_modes(cfg, work_root)
    include_flyway = "flyway" in enabled_modes
    include_liquibase = "liquibase" in enabled_modes
    init_schema_sql = generated_schema_sql if generated_schema_sql is not None else render_sql(ir)
    package_path = base_package.replace(".", "/")

    objects = ir["objects"]
    structs = ir.get("structs", [])
    actions = ir.get("actions", [])
    action_inputs = ir.get("action_inputs", [])
    events = ir.get("events", [])
    type_by_id = {t["id"]: t for t in ir.get("types", [])}
    object_by_id = {o["id"]: o for o in objects}
    struct_by_id = {s["id"]: s for s in structs}
    action_input_by_id = {s["id"]: s for s in action_inputs}
    event_by_id = {e["id"]: e for e in events if isinstance(e, dict) and "id" in e}

    files["build.gradle.kts"] = render_gradle_file(
        boot_version,
        dep_mgmt_version,
        toolchain_version,
        runtime_group=runtime_group,
        runtime_version=runtime_version,
    )
    application_prophet_yml = (
        "prophet:\n"
        f"  ontology-id: {ir['ontology']['id']}\n"
        "  compatibility-profile:\n"
        f"    strict-enums: {'true' if ir.get('compatibility_profile', {}).get('strict_enums') else 'false'}\n"
        "  actions:\n"
        "    base-path: /actions\n"
    )
    if include_liquibase:
        application_prophet_yml += (
            "spring:\n"
            "  liquibase:\n"
            "    change-log: classpath:db/changelog/db.changelog-master.yaml\n"
        )
    files["src/main/resources/application-prophet.yml"] = application_prophet_yml

    if include_flyway:
        files["src/main/resources/db/migration/V1__prophet_init.sql"] = init_schema_sql
        if delta_schema_sql:
            files["src/main/resources/db/migration/V2__prophet_delta.sql"] = delta_schema_sql
    if include_liquibase:
        files["src/main/resources/db/changelog/db.changelog-master.yaml"] = render_liquibase_root_changelog()
        files["src/main/resources/db/changelog/prophet/changelog-master.yaml"] = render_liquibase_prophet_changelog(
            include_delta=bool(delta_schema_sql)
        )
        files["src/main/resources/db/changelog/prophet/0001-init.sql"] = init_schema_sql
        if delta_schema_sql:
            files["src/main/resources/db/changelog/prophet/0002-delta.sql"] = delta_schema_sql

    state: Dict[str, Any] = {
        "objects": objects,
        "structs": structs,
        "actions": actions,
        "action_inputs": action_inputs,
        "events": events,
        "type_by_id": type_by_id,
        "object_by_id": object_by_id,
        "struct_by_id": struct_by_id,
        "action_input_by_id": action_input_by_id,
        "event_by_id": event_by_id,
        "base_package": base_package,
        "package_path": package_path,
        "ontology_name": str(ir.get("ontology", {}).get("name", "prophet")),
        "ontology_version": str(ir.get("ontology", {}).get("version", "1.0.0")),
    }

    render_domain_artifacts(files, state)
    render_jpa_persistence_artifacts(files, state)
    render_contract_artifacts(files, state)
    render_action_runtime_artifacts(files, state)
    render_transition_runtime_artifacts(files, state)
    render_jpa_query_artifacts(files, state)

    annotate_generated_java_files(files)
    return files
