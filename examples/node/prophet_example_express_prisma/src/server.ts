import express from 'express';
import { randomUUID } from 'node:crypto';
import { PrismaClient } from '@prisma/client';

import { mountProphet } from '../gen/node-express/src/generated/index.js';
import {
  type ApproveOrderActionHandler,
  type CreateOrderActionHandler,
  type GeneratedActionContext,
  type ShipOrderActionHandler,
} from '../gen/node-express/src/generated/action-handlers.js';
import type * as Actions from '../gen/node-express/src/generated/actions.js';
import type * as Domain from '../gen/node-express/src/generated/domain.js';
import { PrismaGeneratedRepositories } from '../gen/node-express/src/generated/prisma-adapters.js';

const app = express();
app.use(express.json());

class CreateOrderHandler implements CreateOrderActionHandler {
  async handle(input: Actions.CreateOrderCommand, context: GeneratedActionContext): Promise<Actions.CreateOrderResult> {
    await context.repositories.user.save({
      userId: input.customer.userId,
      email: `${input.customer.userId}@example.local`,
    });

    const orderId = randomUUID();
    const order: Domain.Order = {
      orderId,
      customer: input.customer,
      totalAmount: input.totalAmount,
      discountCode: input.discountCode,
      tags: input.tags,
      shippingAddress: input.shippingAddress,
      currentState: 'created',
    };
    await context.repositories.order.save(order);
    return {
      order: { orderId },
      currentState: 'created',
    };
  }
}

class ApproveOrderHandler implements ApproveOrderActionHandler {
  async handle(input: Actions.ApproveOrderCommand, context: GeneratedActionContext): Promise<Actions.ApproveOrderResult> {
    const existing = await context.repositories.order.getById({ orderId: input.order.orderId });
    if (!existing) {
      throw new Error(`order not found: ${input.order.orderId}`);
    }
    await context.repositories.order.save({
      ...existing,
      currentState: 'approved',
    });
    return {
      order: input.order,
      decision: 'approved',
      warnings: input.notes?.length ? ['notes_attached'] : undefined,
    };
  }
}

class ShipOrderHandler implements ShipOrderActionHandler {
  async handle(input: Actions.ShipOrderCommand, context: GeneratedActionContext): Promise<Actions.ShipOrderResult> {
    const existing = await context.repositories.order.getById({ orderId: input.order.orderId });
    if (!existing) {
      throw new Error(`order not found: ${input.order.orderId}`);
    }
    await context.repositories.order.save({
      ...existing,
      currentState: 'shipped',
    });
    return {
      order: input.order,
      shipmentStatus: 'shipped',
      labels: input.packageIds.map((packageId) => `${input.carrier}-${packageId}`),
      labelBatches: [input.packageIds],
    };
  }
}

const prismaClient = new PrismaClient();

mountProphet(app, {
  repositories: new PrismaGeneratedRepositories(prismaClient),
  handlers: {
    createOrder: new CreateOrderHandler(),
    approveOrder: new ApproveOrderHandler(),
    shipOrder: new ShipOrderHandler(),
  },
});

app.listen(8080, () => {
  // eslint-disable-next-line no-console
  console.log('prophet_example_express_prisma listening on :8080');
});
