import express from 'express';
import mongoose from 'mongoose';
import { randomUUID } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import type { Server } from 'node:http';

import { mountProphet } from '../gen/node-express/src/generated/index.js';
import {
  type ApproveOrderActionHandler,
  type CreateOrderActionHandler,
  type ActionContext,
  type ShipOrderActionHandler,
} from '../gen/node-express/src/generated/action-handlers.js';
import type * as Actions from '../gen/node-express/src/generated/actions.js';
import type * as Domain from '../gen/node-express/src/generated/domain.js';
import { MongooseRepositories } from '../gen/node-express/src/generated/mongoose-adapters.js';

class CreateOrderHandler implements CreateOrderActionHandler {
  async handle(input: Actions.CreateOrderCommand, context: ActionContext): Promise<Actions.CreateOrderResult> {
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
  async handle(input: Actions.ApproveOrderCommand, context: ActionContext): Promise<Actions.ApproveOrderResult> {
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
  async handle(input: Actions.ShipOrderCommand, context: ActionContext): Promise<Actions.ShipOrderResult> {
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

export interface AppRuntime {
  app: express.Express;
  close: () => Promise<void>;
}

export async function createAppRuntime(): Promise<AppRuntime> {
  const mongoUrl = process.env.MONGO_URL ?? 'mongodb://127.0.0.1:27017/prophet_example_mongoose';
  await mongoose.connect(mongoUrl);

  const app = express();
  app.use(express.json());

  mountProphet(app, {
    repositories: new MongooseRepositories(),
    handlers: {
      createOrder: new CreateOrderHandler(),
      approveOrder: new ApproveOrderHandler(),
      shipOrder: new ShipOrderHandler(),
    },
  });

  return {
    app,
    close: async () => {
      await mongoose.disconnect();
    },
  };
}

export async function startServer(port: number): Promise<{ server: Server; close: () => Promise<void> }> {
  const runtime = await createAppRuntime();
  const server = runtime.app.listen(port, () => {
    // eslint-disable-next-line no-console
    console.log(`prophet_example_express_mongoose listening on :${port}`);
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
