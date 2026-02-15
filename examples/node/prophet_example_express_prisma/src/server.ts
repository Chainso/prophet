import express from 'express';

import { mountProphet } from '../gen/node-express/src/generated/index';
import {
  ApproveOrderActionHandlerDefault,
  CreateOrderActionHandlerDefault,
  ShipOrderActionHandlerDefault,
} from '../gen/node-express/src/generated/action-handlers';
import { PrismaGeneratedRepositories } from '../gen/node-express/src/generated/prisma-adapters';

const app = express();
app.use(express.json());

mountProphet(app, {
  repositories: new PrismaGeneratedRepositories(),
  handlers: {
    createOrder: new CreateOrderActionHandlerDefault(),
    approveOrder: new ApproveOrderActionHandlerDefault(),
    shipOrder: new ShipOrderActionHandlerDefault(),
  },
});

app.listen(8080, () => {
  // eslint-disable-next-line no-console
  console.log('prophet_example_express_prisma listening on :8080');
});
