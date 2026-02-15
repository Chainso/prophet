// GENERATED FILE: do not edit directly.

import type * as Actions from './actions.js';
import type { GeneratedRepositories } from './persistence.js';
import type { GeneratedEventEmitter } from './events.js';

export interface GeneratedActionContext {
  repositories: GeneratedRepositories;
  eventEmitter: GeneratedEventEmitter;
}

export interface ApproveOrderActionHandler {
  handle(input: Actions.ApproveOrderCommand, context: GeneratedActionContext): Promise<Actions.ApproveOrderResult>;
}

export class ApproveOrderActionHandlerDefault implements ApproveOrderActionHandler {
  async handle(_input: Actions.ApproveOrderCommand): Promise<Actions.ApproveOrderResult> {
    throw new Error('No implementation registered for action: approveOrder');
  }
}

export interface CreateOrderActionHandler {
  handle(input: Actions.CreateOrderCommand, context: GeneratedActionContext): Promise<Actions.CreateOrderResult>;
}

export class CreateOrderActionHandlerDefault implements CreateOrderActionHandler {
  async handle(_input: Actions.CreateOrderCommand): Promise<Actions.CreateOrderResult> {
    throw new Error('No implementation registered for action: createOrder');
  }
}

export interface ShipOrderActionHandler {
  handle(input: Actions.ShipOrderCommand, context: GeneratedActionContext): Promise<Actions.ShipOrderResult>;
}

export class ShipOrderActionHandlerDefault implements ShipOrderActionHandler {
  async handle(_input: Actions.ShipOrderCommand): Promise<Actions.ShipOrderResult> {
    throw new Error('No implementation registered for action: shipOrder');
  }
}

export interface GeneratedActionHandlers {
  approveOrder: ApproveOrderActionHandler;
  createOrder: CreateOrderActionHandler;
  shipOrder: ShipOrderActionHandler;
}
