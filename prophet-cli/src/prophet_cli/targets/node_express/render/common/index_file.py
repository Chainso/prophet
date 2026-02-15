from __future__ import annotations

from typing import Any, Dict

def _render_index_file(ir: Dict[str, Any]) -> str:
    lines = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import type { Application } from 'express';",
        "import { buildGeneratedActionRouter } from './action-routes';",
        "import { buildGeneratedQueryRouter } from './query-routes';",
        "import { GeneratedActionExecutionService } from './action-service';",
        "import { GeneratedEventEmitterNoOp, type GeneratedEventEmitter } from './events';",
        "import type { GeneratedActionContext, GeneratedActionHandlers } from './action-handlers';",
        "import type { GeneratedRepositories } from './persistence';",
        "",
        "export interface GeneratedMountDependencies {",
        "  repositories: GeneratedRepositories;",
        "  handlers: GeneratedActionHandlers;",
        "  eventEmitter?: GeneratedEventEmitter;",
        "}",
        "",
        "export function mountProphet(app: Application, deps: GeneratedMountDependencies): void {",
        "  const eventEmitter = deps.eventEmitter ?? new GeneratedEventEmitterNoOp();",
        "  const context: GeneratedActionContext = {",
        "    repositories: deps.repositories,",
        "    eventEmitter,",
        "  };",
        "  const service = new GeneratedActionExecutionService(deps.handlers, eventEmitter);",
        "  app.use(buildGeneratedActionRouter(service, context));",
        "  app.use(buildGeneratedQueryRouter(deps.repositories));",
        "}",
        "",
    ]
    return "\n".join(lines)


