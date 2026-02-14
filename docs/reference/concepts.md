# Concepts

## Ontology

A Prophet ontology is a domain contract describing:
- Objects and fields
- Optional object state models (states and transitions)
- Action inputs and outputs
- Actions, events, and triggers

## DSL -> IR -> Artifacts

Prophet compiles `.prophet` files into:
1. Validated canonical IR (`.prophet/ir/current.ir.json`)
2. Deterministic generated outputs (`gen/**`)

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

Details: `docs/reference/compatibility.md`.
