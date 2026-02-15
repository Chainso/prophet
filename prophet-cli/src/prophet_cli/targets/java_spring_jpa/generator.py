from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from prophet_cli.codegen.contracts import GenerationContext
from prophet_cli.codegen.stacks import StackSpec
from prophet_cli.core.ir_reader import IRReader
from prophet_cli.targets.java_common.render.support import effective_base_package
from prophet_cli.targets.java_spring_jpa.render.spring import render_liquibase_prophet_changelog
from prophet_cli.targets.java_spring_jpa.render.spring import render_liquibase_root_changelog
from prophet_cli.targets.java_spring_jpa.render.spring import render_spring_files


def _pascal_case(value: str) -> str:
    chunks = [part for part in value.replace("-", "_").split("_") if part]
    return "".join(chunk[:1].upper() + chunk[1:] for chunk in chunks)


@dataclass(frozen=True)
class JavaSpringJpaDeps:
    cfg_get: Callable[[Dict[str, Any], List[str], Any], Any]
    resolve_stack_spec: Callable[[Dict[str, Any]], StackSpec]
    render_sql: Callable[[IRReader], str]
    compute_delta_from_baseline: Callable[[Path, Dict[str, Any], IRReader], Tuple[Optional[str], List[str], Optional[Path], Optional[str], Dict[str, Any]]]
    render_openapi: Callable[[IRReader], str]
    toolchain_version: str


def generate_outputs(context: GenerationContext, deps: JavaSpringJpaDeps) -> Dict[str, str]:
    cfg = context.cfg
    work_root = context.root
    outputs: Dict[str, str] = {}
    out_dir = deps.cfg_get(cfg, ["generation", "out_dir"], "gen")
    stack = deps.resolve_stack_spec(cfg)
    targets = deps.cfg_get(cfg, ["generation", "targets"], ["sql", "openapi", "spring_boot", "flyway", "liquibase"])
    schema_sql = deps.render_sql(context.ir_reader)
    delta_sql, delta_warnings, baseline_path, baseline_hash, delta_meta = deps.compute_delta_from_baseline(
        work_root, cfg, context.ir_reader
    )

    if "sql" in targets:
        outputs[f"{out_dir}/sql/schema.sql"] = schema_sql
    if "flyway" in targets:
        outputs[f"{out_dir}/migrations/flyway/V1__prophet_init.sql"] = schema_sql
        if delta_sql:
            outputs[f"{out_dir}/migrations/flyway/V2__prophet_delta.sql"] = delta_sql
    if "liquibase" in targets:
        outputs[f"{out_dir}/migrations/liquibase/db.changelog-master.yaml"] = render_liquibase_root_changelog()
        outputs[f"{out_dir}/migrations/liquibase/prophet/changelog-master.yaml"] = render_liquibase_prophet_changelog(
            bool(delta_sql)
        )
        outputs[f"{out_dir}/migrations/liquibase/prophet/0001-init.sql"] = schema_sql
        if delta_sql:
            outputs[f"{out_dir}/migrations/liquibase/prophet/0002-delta.sql"] = delta_sql
    if delta_sql:
        report = {
            "baseline_ir": str(baseline_path.relative_to(work_root)) if baseline_path is not None else None,
            "from_ir_hash": baseline_hash,
            "to_ir_hash": context.ir_reader.ir_hash,
            "warnings": delta_warnings,
            "summary": {
                "safe_auto_apply_count": delta_meta.get("safe_auto_apply_count", 0),
                "manual_review_count": delta_meta.get("manual_review_count", 0),
                "destructive_count": delta_meta.get("destructive_count", 0),
            },
            "findings": delta_meta.get("findings", []),
        }
        outputs[f"{out_dir}/migrations/delta/report.json"] = json.dumps(report, indent=2, sort_keys=False) + "\n"
    if "openapi" in targets:
        outputs[f"{out_dir}/openapi/openapi.yaml"] = deps.render_openapi(context.ir_reader)
    if "spring_boot" in targets:
        spring_files = render_spring_files(
            context.ir_reader.as_dict(),
            cfg,
            root=work_root,
            generated_schema_sql=schema_sql,
            delta_schema_sql=delta_sql,
            toolchain_version=deps.toolchain_version,
        )
        for rel_path, content in spring_files.items():
            outputs[f"{out_dir}/spring-boot/{rel_path}"] = content

    configured_base_package = str(deps.cfg_get(cfg, ["generation", "spring_boot", "base_package"], "com.example.prophet"))
    ontology_name = str(context.ir_reader.get("ontology", {}).get("name", "prophet"))
    base_package = effective_base_package(configured_base_package, ontology_name)
    extension_hooks = []
    for action in sorted(context.ir_reader.action_contracts(), key=lambda item: item.name):
        action_name = action.name
        action_id = action.id
        interface_name = f"{_pascal_case(action_name)}ActionHandler"
        extension_hooks.append(
            {
                "kind": "action_handler",
                "action_id": action_id,
                "action_name": action_name,
                "java_interface": f"{base_package}.generated.actions.handlers.{interface_name}",
                "default_implementation_class": f"{base_package}.generated.actions.handlers.defaults.{interface_name}Default",
            }
        )
    outputs[f"{out_dir}/manifest/extension-hooks.json"] = json.dumps(
        {
            "schema_version": 1,
            "stack": stack.id,
            "hooks": extension_hooks,
        },
        indent=2,
        sort_keys=False,
    ) + "\n"

    manifest_rel = f"{out_dir}/manifest/generated-files.json"
    hashed_outputs = {
        rel: hashlib.sha256(content.encode("utf-8")).hexdigest()
        for rel, content in sorted(outputs.items())
    }
    manifest_payload = {
        "schema_version": 1,
        "toolchain_version": deps.toolchain_version,
        "stack": {
            "id": stack.id,
            "language": stack.language,
            "framework": stack.framework,
            "orm": stack.orm,
        },
        "ir_hash": context.ir_reader.ir_hash,
        "outputs": [
            {"path": rel, "sha256": digest}
            for rel, digest in sorted(hashed_outputs.items())
        ],
    }
    outputs[manifest_rel] = json.dumps(manifest_payload, indent=2, sort_keys=False) + "\n"

    return outputs
