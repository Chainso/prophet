import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import request from 'supertest';

import { createAppRuntime } from '../dist/src/server.js';

describe('Prophet Express Prisma HTTP flow', function () {
  this.timeout(30_000);

  let runtime;
  let client;

  before(async () => {
    runtime = await createAppRuntime();
    client = request(runtime.app);
  });

  after(async () => {
    if (runtime) {
      await runtime.close();
    }
  });

  it('supports create -> approve -> ship -> get -> query', async () => {
    const runId = randomUUID();
    const customerId = `user-${runId}`;

    const created = await client.post('/actions/createOrder').send({
      customer: { userId: customerId },
      totalAmount: 123.45,
      discountCode: 'TEST',
      tags: ['integration', 'node'],
      shippingAddress: {
        line1: '1 Test St',
        city: 'San Francisco',
        countryCode: 'US',
      },
    });
    assert.equal(created.status, 200);
    assert.equal(created.body.currentState, 'created');
    const orderId = created.body.order?.orderId;
    assert.equal(typeof orderId, 'string');

    const approved = await client.post('/actions/approveOrder').send({
      order: { orderId },
      notes: ['approved'],
    });
    assert.equal(approved.status, 200);
    assert.equal(approved.body.decision, 'approved');
    assert.equal(approved.body.order?.orderId, orderId);

    const shipped = await client.post('/actions/shipOrder').send({
      order: { orderId },
      carrier: 'UPS',
      trackingNumber: `trk-${runId}`,
      packageIds: ['pkg-1', 'pkg-2'],
    });
    assert.equal(shipped.status, 200);
    assert.equal(shipped.body.shipmentStatus, 'shipped');
    assert.equal(shipped.body.order?.orderId, orderId);

    const fetched = await client.get(`/orders/${orderId}`);
    assert.equal(fetched.status, 200);
    assert.equal(fetched.body.orderId, orderId);
    assert.equal(fetched.body.currentState, 'shipped');

    const queried = await client.post('/orders/query?page=0&size=10').send({
      currentState: { eq: 'shipped' },
    });
    assert.equal(queried.status, 200);
    assert.ok(Array.isArray(queried.body.items));
    assert.ok(queried.body.items.some((item) => item.orderId === orderId));
  });
});
