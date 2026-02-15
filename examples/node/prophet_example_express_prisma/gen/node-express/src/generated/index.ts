// GENERATED FILE: do not edit directly.

import type { Application } from 'express';
import { buildGeneratedActionRouter } from './action-routes.js';
import { buildGeneratedQueryRouter } from './query-routes.js';
import { GeneratedActionExecutionService } from './action-service.js';
import { GeneratedEventEmitterNoOp, type GeneratedEventEmitter } from './events.js';
import type { GeneratedActionContext, GeneratedActionHandlers } from './action-handlers.js';
import type { GeneratedRepositories } from './persistence.js';

export interface GeneratedMountDependencies {
  repositories: GeneratedRepositories;
  handlers: GeneratedActionHandlers;
  eventEmitter?: GeneratedEventEmitter;
}

export function mountProphet(app: Application, deps: GeneratedMountDependencies): void {
  const eventEmitter = deps.eventEmitter ?? new GeneratedEventEmitterNoOp();
  const context: GeneratedActionContext = {
    repositories: deps.repositories,
    eventEmitter,
  };
  const service = new GeneratedActionExecutionService(deps.handlers, eventEmitter);
  app.use(buildGeneratedActionRouter(service, context));
  app.use(buildGeneratedQueryRouter(deps.repositories));
}
