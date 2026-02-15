from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from prophet_cli.codegen.contracts import GenerationContext
from prophet_cli.codegen.stacks import StackSpec
from prophet_cli.core.ir_reader import IRReader


@dataclass(frozen=True)
class PythonDeps:
    cfg_get: Callable[[Dict[str, Any], List[str], Any], Any]
    resolve_stack_spec: Callable[[Dict[str, Any]], StackSpec]
    render_sql: Callable[[IRReader], str]
    render_openapi: Callable[[IRReader], str]
    toolchain_version: str


def _render_pyproject(stack: StackSpec) -> str:
    deps: List[str] = []
    if stack.framework == "fastapi":
        deps.extend(["fastapi>=0.112,<1.0", "uvicorn>=0.30,<1.0"])
    elif stack.framework == "flask":
        deps.append("flask>=3.0,<4.0")
    elif stack.framework == "django":
        deps.append("django>=5.0,<6.0")

    if stack.orm == "sqlalchemy":
        deps.append("sqlalchemy>=2.0,<3.0")
    elif stack.orm == "sqlmodel":
        deps.append("sqlmodel>=0.0.22,<1.0")
        deps.append("sqlalchemy>=2.0,<3.0")

    payload = {
        "name": "prophet-generated-python",
        "private": True,
        "requires-python": ">=3.10",
        "dependencies": deps,
    }
    return "# GENERATED FILE: do not edit directly.\n" + json.dumps(payload, indent=2, sort_keys=False) + "\n"


def generate_outputs(context: GenerationContext, deps: PythonDeps) -> Dict[str, str]:
    cfg = context.cfg
    out_dir = str(deps.cfg_get(cfg, ["generation", "out_dir"], "gen"))
    stack = deps.resolve_stack_spec(cfg)
    targets = deps.cfg_get(cfg, ["generation", "targets"], list(stack.default_targets))
    if not isinstance(targets, list):
        targets = list(stack.default_targets)

    outputs: Dict[str, str] = {}
    if "sql" in targets:
        outputs[f"{out_dir}/sql/schema.sql"] = deps.render_sql(context.ir_reader)
    if "openapi" in targets:
        outputs[f"{out_dir}/openapi/openapi.yaml"] = deps.render_openapi(context.ir_reader)

    if "python" in targets:
        outputs[f"{out_dir}/python/pyproject.json"] = _render_pyproject(stack)
        outputs[f"{out_dir}/python/src/generated/__init__.py"] = "# GENERATED FILE: do not edit directly.\n"

    extension_hooks = []
    for action in sorted(context.ir_reader.action_contracts(), key=lambda item: item.name):
        extension_hooks.append(
            {
                "kind": "action_handler",
                "action_id": action.id,
                "action_name": action.name,
                "python_protocol": f"generated.action_handlers.{action.name}Handler",
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
        "outputs": [{"path": rel, "sha256": digest} for rel, digest in sorted(hashed_outputs.items())],
    }
    outputs[manifest_rel] = json.dumps(manifest_payload, indent=2, sort_keys=False) + "\n"
    return outputs
