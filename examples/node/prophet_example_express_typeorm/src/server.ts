import express from 'express';
import 'reflect-metadata';

import { mountProphet } from '../gen/node-express/src/generated/index';
import {
  ApproveOrderActionHandlerDefault,
  CreateOrderActionHandlerDefault,
  ShipOrderActionHandlerDefault,
} from '../gen/node-express/src/generated/action-handlers';
import { TypeOrmGeneratedRepositories } from '../gen/node-express/src/generated/typeorm-adapters';

const app = express();
app.use(express.json());

mountProphet(app, {
  repositories: new TypeOrmGeneratedRepositories(),
  handlers: {
    createOrder: new CreateOrderActionHandlerDefault(),
    approveOrder: new ApproveOrderActionHandlerDefault(),
    shipOrder: new ShipOrderActionHandlerDefault(),
  },
});

app.listen(8080, () => {
  // eslint-disable-next-line no-console
  console.log('prophet_example_express_typeorm listening on :8080');
});
