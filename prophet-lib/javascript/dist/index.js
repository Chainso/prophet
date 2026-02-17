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

export class TransitionValidationResult {
  constructor(passesValidation, failureReason) {
    this.passesValidation = passesValidation;
    this.failureReason = failureReason;
  }

  static passed() {
    return new TransitionValidationResult(true);
  }

  static failed(failureReason) {
    return new TransitionValidationResult(false, failureReason);
  }
}
