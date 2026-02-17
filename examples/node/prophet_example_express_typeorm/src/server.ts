import express from 'express';
import 'reflect-metadata';
import { randomUUID } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { DataSource } from 'typeorm';
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
import type * as EventContracts from '../gen/node-express/src/generated/event-contracts.js';
import { TransitionServices } from '../gen/node-express/src/generated/transitions.js';
import { TypeOrmRepositories } from '../gen/node-express/src/generated/typeorm-adapters.js';
import { OrderEntity, OrderStateHistoryEntity, UserEntity } from '../gen/node-express/src/generated/typeorm-entities.js';

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
    const transitions = new TransitionServices(context.repositories);
    const draft = await transitions.order.approveOrder(input.order);
    return draft.build();
  }
}

class ShipOrderHandler implements ShipOrderActionHandler {
  async handle(input: Actions.ShipOrderCommand, context: ActionContext): Promise<EventContracts.OrderShipTransition> {
    const existing = await context.repositories.order.getById({ orderId: input.order.orderId });
    if (!existing) {
      throw new Error(`order not found: ${input.order.orderId}`);
    }
    const transitions = new TransitionServices(context.repositories);
    const draft = await transitions.order.shipOrder(input.order);
    return draft.build();
  }
}

export interface AppRuntime {
  app: express.Express;
  close: () => Promise<void>;
}

export async function createAppRuntime(): Promise<AppRuntime> {
  const dataSource = new DataSource({
    type: 'sqlite',
    database: './prophet_example.sqlite',
    synchronize: true,
    entities: [OrderEntity, OrderStateHistoryEntity, UserEntity],
  });
  await dataSource.initialize();

  const app = express();
  app.use(express.json());

  mountProphet(app, {
    repositories: new TypeOrmRepositories(dataSource),
    handlers: {
      createOrder: new CreateOrderHandler(),
      approveOrder: new ApproveOrderHandler(),
      shipOrder: new ShipOrderHandler(),
    },
  });

  return {
    app,
    close: async () => {
      await dataSource.destroy();
    },
  };
}

export async function startServer(port: number): Promise<{ server: Server; close: () => Promise<void> }> {
  const runtime = await createAppRuntime();
  const server = runtime.app.listen(port, () => {
    // eslint-disable-next-line no-console
    console.log(`prophet_example_express_typeorm listening on :${port}`);
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
