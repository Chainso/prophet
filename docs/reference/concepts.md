# Concepts

## Ontology

A Prophet ontology is a domain contract describing:
- Objects and fields
- Optional field-level lifecycle state metadata
- Action inputs and produced events
- Actions, events, and triggers

Naming model:
- Technical symbols are the DSL identifiers (`object Order`, `field orderId`).
- Display labels are optional `name "..."` metadata for human-facing surfaces.
- Generated wire keys and references stay technical-symbol based.

Event model:
- Events are explicitly defined in DSL with `event` blocks.
- Inline action `output { ... }` blocks derive an event payload named `<ActionName> Result`.
- Actions can reference existing events via `output event <EventName>`.
- There is no secondary event subtype.

Event emission behavior in generated action services:
- The action's produced event is auto-published through generated event publisher wiring.
- Additional user-returned events are published after the produced event in deterministic order.

State model:
- Lifecycle state is a normal enum field on an object.
- Mark that field with `state`.
- Set its initial value with `initial <EnumValue>`.
- Generated persistence and query code use the declared field name directly.

## DSL -> IR -> Artifacts

Prophet compiles `.prophet` files into:
1. Validated canonical IR (`.prophet/ir/current.ir.json`)
2. Deterministic generated outputs (`gen/**`) such as SQL, OpenAPI, Turtle, and stack runtime artifacts

## Deterministic Generation

Given the same ontology/config/toolchain version, Prophet should produce stable output paths and content.

## Action Model

Actions are generated as HTTP endpoints (`POST /actions/<actionName>`).
Prophet generates contracts and extension hooks, not business logic implementations.

## Query Model

Generated object APIs separate concerns:
- `GET /<objects>` for pagination/sort
- `POST /<objects>/query` for typed filtering
- `GET /<objects>/{id}` for by-id fetch

## Compatibility Model

Version checks compare current IR with baseline IR:
- breaking -> major
- additive -> minor
- non-functional -> patch

Details: [Compatibility](compatibility.md).
