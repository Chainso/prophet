from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from prophet_cli.codegen.contracts import GenerationContext
from prophet_cli.codegen.stacks import StackSpec


@dataclass(frozen=True)
class JavaSpringJpaDeps:
    cfg_get: Callable[[Dict[str, Any], List[str], Any], Any]
    resolve_stack_spec: Callable[[Dict[str, Any]], StackSpec]
    render_sql: Callable[[Dict[str, Any]], str]
    compute_delta_from_baseline: Callable[[Path, Dict[str, Any], Dict[str, Any]], Tuple[Optional[str], List[str], Optional[Path], Optional[str], Dict[str, Any]]]
    render_liquibase_root_changelog: Callable[[], str]
    render_liquibase_prophet_changelog: Callable[[bool], str]
    render_openapi: Callable[[Dict[str, Any]], str]
    render_spring_files: Callable[[Dict[str, Any], Dict[str, Any], Path, str, Optional[str]], Dict[str, str]]
    toolchain_version: str


def generate_outputs(context: GenerationContext, deps: JavaSpringJpaDeps) -> Dict[str, str]:
    ir = context.ir
    cfg = context.cfg
    work_root = context.root
    outputs: Dict[str, str] = {}
    out_dir = deps.cfg_get(cfg, ["generation", "out_dir"], "gen")
    stack = deps.resolve_stack_spec(cfg)
    targets = deps.cfg_get(cfg, ["generation", "targets"], ["sql", "openapi", "spring_boot", "flyway", "liquibase"])
    schema_sql = deps.render_sql(ir)
    delta_sql, delta_warnings, baseline_path, baseline_hash, delta_meta = deps.compute_delta_from_baseline(work_root, cfg, ir)

    if "sql" in targets:
        outputs[f"{out_dir}/sql/schema.sql"] = schema_sql
    if "flyway" in targets:
        outputs[f"{out_dir}/migrations/flyway/V1__prophet_init.sql"] = schema_sql
        if delta_sql:
            outputs[f"{out_dir}/migrations/flyway/V2__prophet_delta.sql"] = delta_sql
    if "liquibase" in targets:
        outputs[f"{out_dir}/migrations/liquibase/db.changelog-master.yaml"] = deps.render_liquibase_root_changelog()
        outputs[f"{out_dir}/migrations/liquibase/prophet/changelog-master.yaml"] = deps.render_liquibase_prophet_changelog(
            bool(delta_sql)
        )
        outputs[f"{out_dir}/migrations/liquibase/prophet/0001-init.sql"] = schema_sql
        if delta_sql:
            outputs[f"{out_dir}/migrations/liquibase/prophet/0002-delta.sql"] = delta_sql
    if delta_sql:
        report = {
            "baseline_ir": str(baseline_path.relative_to(work_root)) if baseline_path is not None else None,
            "from_ir_hash": baseline_hash,
            "to_ir_hash": ir.get("ir_hash"),
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
        outputs[f"{out_dir}/openapi/openapi.yaml"] = deps.render_openapi(ir)
    if "spring_boot" in targets:
        spring_files = deps.render_spring_files(
            ir,
            cfg,
            work_root,
            schema_sql,
            delta_sql,
        )
        for rel_path, content in spring_files.items():
            outputs[f"{out_dir}/spring-boot/{rel_path}"] = content

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
        "ir_hash": ir.get("ir_hash"),
        "outputs": [
            {"path": rel, "sha256": digest}
            for rel, digest in sorted(hashed_outputs.items())
        ],
    }
    outputs[manifest_rel] = json.dumps(manifest_payload, indent=2, sort_keys=False) + "\n"

    return outputs

