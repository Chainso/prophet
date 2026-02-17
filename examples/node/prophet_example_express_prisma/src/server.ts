import express from 'express';
import { randomUUID } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { PrismaClient } from '@prisma/client';

import { mountProphet } from '../gen/node-express/src/generated/index.js';
import {
  type ApproveOrderActionHandler,
  type CreateOrderActionHandler,
  type ActionContext,
  type ShipOrderActionHandler,
} from '../gen/node-express/src/generated/action-handlers.js';
import type * as Actions from '../gen/node-express/src/generated/actions.js';
import type * as Domain from '../gen/node-express/src/generated/domain.js';
import type * as EventContracts from '../gen/node-express/src/generated/event-contracts.js';
import { PrismaRepositories } from '../gen/node-express/src/generated/prisma-adapters.js';
import { TransitionServices } from '../gen/node-express/src/generated/transitions.js';
import type { Server } from 'node:http';

class CreateOrderHandler implements CreateOrderActionHandler {
  async handle(input: Actions.CreateOrderCommand, context: ActionContext): Promise<EventContracts.CreateOrderResult> {
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
      state: 'created',
    };
    await context.repositories.order.save(order);
    return {
      order: { orderId },
    };
  }
}

class ApproveOrderHandler implements ApproveOrderActionHandler {
  async handle(input: Actions.ApproveOrderCommand, context: ActionContext): Promise<EventContracts.OrderApproveTransition> {
    const existing = await context.repositories.order.getById({ orderId: input.order.orderId });
    if (!existing) {
      throw new Error(`order not found: ${input.order.orderId}`);
    }

    const updatedOrder: Domain.Order = {
      ...existing,
      approvedByUserId: input.approvedBy?.userId,
      approvalNotes: input.notes,
      approvalReason: input.context?.reason,
    };
    const savedOrder = await context.repositories.order.save(updatedOrder);

    const transitions = new TransitionServices(context.repositories);
    const draft = await transitions.order.approveOrder(savedOrder);
    return draft.build({
      approvedByUserId: savedOrder.approvedByUserId,
      noteCount: input.notes?.length ?? 0,
      approvalReason: savedOrder.approvalReason,
    });
  }
}

class ShipOrderHandler implements ShipOrderActionHandler {
  async handle(input: Actions.ShipOrderCommand, context: ActionContext): Promise<EventContracts.OrderShipTransition> {
    const existing = await context.repositories.order.getById({ orderId: input.order.orderId });
    if (!existing) {
      throw new Error(`order not found: ${input.order.orderId}`);
    }

    const updatedOrder: Domain.Order = {
      ...existing,
      shippingCarrier: input.carrier,
      shippingTrackingNumber: input.trackingNumber,
      shippingPackageIds: input.packageIds,
    };
    const savedOrder = await context.repositories.order.save(updatedOrder);

    const transitions = new TransitionServices(context.repositories);
    const draft = await transitions.order.shipOrder(savedOrder);
    return draft.build({
      carrier: input.carrier,
      trackingNumber: input.trackingNumber,
      packageIds: input.packageIds,
    });
  }
}

export interface AppRuntime {
  app: express.Express;
  close: () => Promise<void>;
}

export async function createAppRuntime(): Promise<AppRuntime> {
  const app = express();
  app.use(express.json());

  const prismaClient = new PrismaClient();

  mountProphet(app, {
    repositories: new PrismaRepositories(prismaClient),
    handlers: {
      createOrder: new CreateOrderHandler(),
      approveOrder: new ApproveOrderHandler(),
      shipOrder: new ShipOrderHandler(),
    },
  });

  return {
    app,
    close: async () => {
      await prismaClient.$disconnect();
    },
  };
}

export async function startServer(port: number): Promise<{ server: Server; close: () => Promise<void> }> {
  const runtime = await createAppRuntime();
  const server = runtime.app.listen(port, () => {
    // eslint-disable-next-line no-console
    console.log(`prophet_example_express_prisma listening on :${port}`);
  });

  return {
    server,
    close: async () => {
      await new Promise<void>((resolve, reject) => {
        server.close((error) => {
          if (error) {
            reject(error);
            return;
          }
          resolve();
        });
      });
      await runtime.close();
    },
  };
}

async function main(): Promise<void> {
  const port = Number.parseInt(process.env.PORT ?? '8080', 10);
  await startServer(port);
}

const isMain = process.argv[1] === fileURLToPath(import.meta.url);
if (isMain) {
  void main();
}
