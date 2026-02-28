# Concepts

## Ontology

A Prophet ontology is a domain contract describing:
- Objects and fields
- Optional object state models (states and transitions)
- Action inputs and produced events
- Actions, signals, and triggers

Naming model:
- Technical symbols are the DSL identifiers (`object Order`, `field orderId`).
- Display labels are optional `name "..."` metadata for human-facing surfaces.
- Generated wire keys and references stay technical-symbol based.

Event categories in the model:
- Signals are explicitly defined in DSL (`signal` blocks).
- Inline action `output { ... }` blocks derive a signal event (`<ActionName> Result`).
- Actions can also reference existing events via `output signal <SignalName>` and `output transition <Object>.<transition>`.
- Object transitions are events by definition (derived from object transition definitions).

Event emission behavior in generated action services:
- The action's produced event is auto-published through generated event publisher wiring.
- Additional user-returned events are published after the produced event in deterministic order.
- For transition-producing actions, handlers can use generated transition services/handlers that return transition drafts, then build the final transition event payload.

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
