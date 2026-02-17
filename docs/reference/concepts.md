# Concepts

## Ontology

A Prophet ontology is a domain contract describing:
- Objects and fields
- Optional object state models (states and transitions)
- Action inputs and outputs
- Actions, signals, and triggers

Event categories in the model:
- Signals are explicitly defined in DSL (`signal` blocks).
- Action outputs are events by definition (derived from action output contracts).
- Object transitions are events by definition (derived from object transition definitions).

Event emission behavior in generated action services:
- Action-output and signal domain events are auto-published through generated event publisher wiring.
- Transition events remain user-controlled (explicitly emitted by user code when needed).

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
