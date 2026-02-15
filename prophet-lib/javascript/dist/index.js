import { randomUUID } from 'node:crypto';

export function createEventId() {
  return randomUUID();
}

export function nowIso() {
  return new Date().toISOString();
}

export class NoOpEventPublisher {
  async publish(_envelope) {
    return;
  }

  async publishBatch(_envelopes) {
    return;
  }
}
