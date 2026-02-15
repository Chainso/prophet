from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from prophet_cli.codegen.contracts import GenerationContext
from prophet_cli.codegen.stacks import StackSpec
from prophet_cli.core.ir_reader import IRReader
from prophet_cli.targets.node_express.render.common.action_handlers import _render_action_handlers
from prophet_cli.targets.node_express.render.common.action_routes import _render_action_routes
from prophet_cli.targets.node_express.render.common.action_service import _render_action_service
from prophet_cli.targets.node_express.render.common.actions import _render_action_contracts
from prophet_cli.targets.node_express.render.common.domain import _render_domain_types
from prophet_cli.targets.node_express.render.common.event_contracts import _render_event_contracts
from prophet_cli.targets.node_express.render.common.events import _render_event_emitter
from prophet_cli.targets.node_express.render.common.index_file import _render_index_file
from prophet_cli.targets.node_express.render.common.package_files import _render_node_package_json
from prophet_cli.targets.node_express.render.common.package_files import _render_node_tsconfig
from prophet_cli.targets.node_express.render.common.persistence import _render_persistence_contracts
from prophet_cli.targets.node_express.render.common.query import _render_query_filters
from prophet_cli.targets.node_express.render.common.query import _render_query_routes
from prophet_cli.targets.node_express.render.common.validation import _render_validation
from prophet_cli.targets.node_express.render.orm.mongoose import _render_mongoose_adapter
from prophet_cli.targets.node_express.render.orm.mongoose import _render_mongoose_models
from prophet_cli.targets.node_express.render.orm.prisma import _render_prisma_adapter
from prophet_cli.targets.node_express.render.orm.prisma import _render_prisma_schema
from prophet_cli.targets.node_express.render.orm.typeorm import _render_typeorm_adapter
from prophet_cli.targets.node_express.render.orm.typeorm import _render_typeorm_entities
from prophet_cli.targets.node_express.render.support import _append_js_extensions_to_relative_imports
from prophet_cli.targets.node_express.render.support import _pascal_case


def _render_detection_report(cfg: Dict[str, Any]) -> Optional[str]:
    autodetect_payload = cfg.get("_autodetect")
    if not isinstance(autodetect_payload, dict):
        return None
    return json.dumps(autodetect_payload, indent=2, sort_keys=False) + "\n"


@dataclass(frozen=True)
class NodeExpressDeps:
    cfg_get: Callable[[Dict[str, Any], List[str], Any], Any]
    resolve_stack_spec: Callable[[Dict[str, Any]], StackSpec]
    render_sql: Callable[[IRReader], str]
    render_openapi: Callable[[IRReader], str]
    toolchain_version: str


def generate_outputs(context: GenerationContext, deps: NodeExpressDeps) -> Dict[str, str]:
    cfg = context.cfg
    out_dir = str(deps.cfg_get(cfg, ["generation", "out_dir"], "gen"))
    stack = deps.resolve_stack_spec(cfg)
    targets = deps.cfg_get(cfg, ["generation", "targets"], list(stack.default_targets))
    if not isinstance(targets, list):
        targets = list(stack.default_targets)

    ir = context.ir_reader.as_dict()
    outputs: Dict[str, str] = {}

    if "sql" in targets:
        outputs[f"{out_dir}/sql/schema.sql"] = deps.render_sql(context.ir_reader)

    if "openapi" in targets:
        outputs[f"{out_dir}/openapi/openapi.yaml"] = deps.render_openapi(context.ir_reader)

    node_prefix = f"{out_dir}/node-express"
    if "node_express" in targets:
        outputs[f"{node_prefix}/package.json"] = _render_node_package_json(stack)
        outputs[f"{node_prefix}/tsconfig.json"] = _render_node_tsconfig()
        outputs[f"{node_prefix}/src/generated/domain.ts"] = _render_domain_types(ir)
        outputs[f"{node_prefix}/src/generated/actions.ts"] = _render_action_contracts(ir)
        outputs[f"{node_prefix}/src/generated/event-contracts.ts"] = _render_event_contracts(ir)
        outputs[f"{node_prefix}/src/generated/validation.ts"] = _render_validation(ir)
        outputs[f"{node_prefix}/src/generated/query.ts"] = _render_query_filters(ir)
        outputs[f"{node_prefix}/src/generated/persistence.ts"] = _render_persistence_contracts(ir)
        outputs[f"{node_prefix}/src/generated/action-handlers.ts"] = _render_action_handlers(ir)
        outputs[f"{node_prefix}/src/generated/events.ts"] = _render_event_emitter(ir)
        outputs[f"{node_prefix}/src/generated/action-service.ts"] = _render_action_service(ir)
        outputs[f"{node_prefix}/src/generated/action-routes.ts"] = _render_action_routes(ir)
        outputs[f"{node_prefix}/src/generated/query-routes.ts"] = _render_query_routes(ir)
        outputs[f"{node_prefix}/src/generated/index.ts"] = _render_index_file(ir)

    if stack.orm == "prisma" and "prisma" in targets:
        configured_provider = str(
            deps.cfg_get(cfg, ["generation", "node_express", "prisma", "provider"], "sqlite")
        ).strip()
        supported_providers = {"sqlite", "postgresql", "mysql", "sqlserver", "cockroachdb"}
        prisma_provider = configured_provider if configured_provider in supported_providers else "sqlite"
        outputs[f"{node_prefix}/prisma/schema.prisma"] = _render_prisma_schema(ir, provider=prisma_provider)
        outputs[f"{node_prefix}/src/generated/prisma-adapters.ts"] = _render_prisma_adapter(ir, provider=prisma_provider)

    if stack.orm == "typeorm" and "typeorm" in targets:
        outputs[f"{node_prefix}/src/generated/typeorm-entities.ts"] = _render_typeorm_entities(ir)
        outputs[f"{node_prefix}/src/generated/typeorm-adapters.ts"] = _render_typeorm_adapter(ir)

    if stack.orm == "mongoose" and "mongoose" in targets:
        outputs[f"{node_prefix}/src/generated/mongoose-models.ts"] = _render_mongoose_models(ir)
        outputs[f"{node_prefix}/src/generated/mongoose-adapters.ts"] = _render_mongoose_adapter(ir)

    for rel, content in list(outputs.items()):
        if rel.startswith(f"{node_prefix}/src/generated/") and rel.endswith(".ts"):
            outputs[rel] = _append_js_extensions_to_relative_imports(content)

    extension_hooks = []
    for action in sorted(context.ir_reader.action_contracts(), key=lambda item: item.name):
        action_name = action.name
        handler_name = f"{_pascal_case(action_name)}ActionHandler"
        extension_hooks.append(
            {
                "kind": "action_handler",
                "action_id": action.id,
                "action_name": action_name,
                "typescript_interface": f"generated.{handler_name}",
                "default_implementation": f"generated.{handler_name}Default",
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

    detection_report = _render_detection_report(cfg)
    if detection_report is not None:
        outputs[f"{out_dir}/manifest/node-autodetect.json"] = detection_report

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
