<p align="center">
  <img src="https://raw.githubusercontent.com/Chainso/prophet/main/brand/exports/logo-horizontal-color.png" alt="Prophet logo" />
</p>

---

# @prophet-ontology/events-runtime

`@prophet-ontology/events-runtime` is the shared Node runtime contract used by Prophet-generated action services.

Main project repository:
- https://github.com/Chainso/prophet

It defines:
- an async `EventPublisher` interface
- a canonical `EventWireEnvelope` shape
- utility helpers (`createEventId`, `nowIso`)
- a `NoOpEventPublisher` for local wiring and tests

## Install

```bash
npm install @prophet-ontology/events-runtime
```

## API

```ts
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
```

Exports:
- `createEventId(): string`
- `nowIso(): string`
- `NoOpEventPublisher`

## Implement a Platform Publisher

```ts
import type { EventPublisher, EventWireEnvelope } from "@prophet-ontology/events-runtime";

type PlatformClient = {
  sendEvent(payload: unknown): Promise<void>;
  sendEvents(payloads: unknown[]): Promise<void>;
};

export class PlatformEventPublisher implements EventPublisher {
  constructor(private readonly client: PlatformClient) {}

  async publish(envelope: EventWireEnvelope): Promise<void> {
    await this.client.sendEvent(envelope);
  }

  async publishBatch(envelopes: EventWireEnvelope[]): Promise<void> {
    await this.client.sendEvents(envelopes);
  }
}
```

## With Prophet-Generated Code

Generated Node action services call `publish`/`publishBatch` after successful handler execution.
If you do not provide an implementation, you can wire `NoOpEventPublisher` for local development.

## Local Validation

From repository root:

```bash
npm --prefix prophet-lib/javascript test
npm --prefix prophet-lib/javascript pack --dry-run
```

## More Information

- Main repository README: https://github.com/Chainso/prophet#readme
- Runtime index: https://github.com/Chainso/prophet/tree/main/prophet-lib
- Event wire contract: https://github.com/Chainso/prophet/tree/main/prophet-lib/specs/wire-contract.md
- Event wire JSON schema: https://github.com/Chainso/prophet/tree/main/prophet-lib/specs/wire-event-envelope.schema.json
- Node/Express reference: https://github.com/Chainso/prophet/tree/main/docs/reference/node-express.md
- Example app: https://github.com/Chainso/prophet/tree/main/examples/node/prophet_example_express_prisma
