export interface EventUpdatedObject {
  object_type: string;
  object_ref: Record<string, unknown>;
  object: Record<string, unknown>;
}

export interface EventWireEnvelope {
  event_id: string;
  trace_id: string;
  event_type: string;
  schema_version: string;
  occurred_at: string;
  source: string;
  payload: Record<string, unknown>;
  attributes?: Record<string, string>;
  updated_objects?: EventUpdatedObject[];
}

export interface EventPublisher {
  publish(envelope: EventWireEnvelope): Promise<void>;
  publishBatch(envelopes: EventWireEnvelope[]): Promise<void>;
}

export declare function createEventId(): string;
export declare function nowIso(): string;

export declare class NoOpEventPublisher implements EventPublisher {
  publish(envelope: EventWireEnvelope): Promise<void>;
  publishBatch(envelopes: EventWireEnvelope[]): Promise<void>;
}

export declare class TransitionValidationResult {
  passesValidation: boolean;
  failureReason?: string;
  constructor(passesValidation: boolean, failureReason?: string);
  static passed(): TransitionValidationResult;
  static failed(failureReason: string): TransitionValidationResult;
}
