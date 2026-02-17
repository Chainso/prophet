import test from 'node:test';
import assert from 'node:assert/strict';

import { NoOpEventPublisher, TransitionValidationResult, createEventId, nowIso } from '../dist/index.js';

test('createEventId returns non-empty id', () => {
  const id = createEventId();
  assert.equal(typeof id, 'string');
  assert.ok(id.length > 0);
});

test('nowIso returns ISO string', () => {
  const timestamp = nowIso();
  assert.ok(/\d{4}-\d{2}-\d{2}T/.test(timestamp));
});

test('NoOpEventPublisher resolves publish methods', async () => {
  const publisher = new NoOpEventPublisher();
  await publisher.publish({
    event_id: 'evt-1',
    trace_id: 'trace-1',
    event_type: 'Example',
    schema_version: '1.0.0',
    occurred_at: nowIso(),
    source: 'test',
    payload: {},
    updated_objects: [
      {
        object_type: 'Order',
        object_ref: { orderId: 'ord-1' },
        object: { orderId: 'ord-1', totalAmount: 42 },
      },
    ],
  });
  await publisher.publishBatch([]);
});

test('TransitionValidationResult helper factories shape values', () => {
  const passed = TransitionValidationResult.passed();
  assert.equal(passed.passesValidation, true);
  assert.equal(passed.failureReason, undefined);

  const failed = TransitionValidationResult.failed('blocked');
  assert.equal(failed.passesValidation, false);
  assert.equal(failed.failureReason, 'blocked');
});
