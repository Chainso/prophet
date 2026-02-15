// GENERATED FILE: do not edit directly.

import type * as Actions from './actions.js';
import type { GeneratedActionContext, GeneratedActionHandlers } from './action-handlers.js';
import type { GeneratedEventEmitter } from './events.js';

export class GeneratedActionExecutionService {
  constructor(
    private readonly handlers: GeneratedActionHandlers,
    private readonly eventEmitter: GeneratedEventEmitter,
  ) {}

  async approveOrder(input: Actions.ApproveOrderCommand, context: GeneratedActionContext): Promise<Actions.ApproveOrderResult> {
    const output = await this.handlers.approveOrder.handle(input, context);
    await this.eventEmitter.emitApproveOrderResult(output);
    return output;
  }

  async createOrder(input: Actions.CreateOrderCommand, context: GeneratedActionContext): Promise<Actions.CreateOrderResult> {
    const output = await this.handlers.createOrder.handle(input, context);
    await this.eventEmitter.emitCreateOrderResult(output);
    return output;
  }

  async shipOrder(input: Actions.ShipOrderCommand, context: GeneratedActionContext): Promise<Actions.ShipOrderResult> {
    const output = await this.handlers.shipOrder.handle(input, context);
    await this.eventEmitter.emitShipOrderResult(output);
    return output;
  }

}
