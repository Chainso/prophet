export interface EventWireEnvelope {
  event_id: string;
  trace_id: string;
  event_type: string;
  schema_version: string;
  occurred_at: string;
  source: string;
  payload: Record<string, unknown>;
  attributes?: Record<string, string>;
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
