import express from 'express';
import 'reflect-metadata';
import { randomUUID } from 'node:crypto';
import { DataSource } from 'typeorm';

import { mountProphet } from '../gen/node-express/src/generated/index';
import {
  type ApproveOrderActionHandler,
  type CreateOrderActionHandler,
  type GeneratedActionContext,
  type ShipOrderActionHandler,
} from '../gen/node-express/src/generated/action-handlers';
import type * as Actions from '../gen/node-express/src/generated/actions';
import type * as Domain from '../gen/node-express/src/generated/domain';
import { TypeOrmGeneratedRepositories } from '../gen/node-express/src/generated/typeorm-adapters';
import { OrderEntity, UserEntity } from '../gen/node-express/src/generated/typeorm-entities';

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

async function bootstrap(): Promise<void> {
  const dataSource = new DataSource({
    type: 'sqlite',
    database: './prophet_example.sqlite',
    synchronize: true,
    entities: [OrderEntity, UserEntity],
  });
  await dataSource.initialize();

  const app = express();
  app.use(express.json());

  mountProphet(app, {
    repositories: new TypeOrmGeneratedRepositories(dataSource),
    handlers: {
      createOrder: new CreateOrderHandler(),
      approveOrder: new ApproveOrderHandler(),
      shipOrder: new ShipOrderHandler(),
    },
  });

  app.listen(8080, () => {
    // eslint-disable-next-line no-console
    console.log('prophet_example_express_typeorm listening on :8080');
  });
}

void bootstrap();
