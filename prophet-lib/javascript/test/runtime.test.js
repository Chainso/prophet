import test from 'node:test';
import assert from 'node:assert/strict';

import { NoOpEventPublisher, createEventId, nowIso } from '../dist/index.js';

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
  });
  await publisher.publishBatch([]);
});
