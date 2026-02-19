# Prophet Example: Turtle Minimal (Support Domain)

This is the smallest end-to-end Turtle-focused Prophet example.

## What This Example Models

A simple support workflow:
- `Ticket` object with basic fields and lifecycle state
- `UserRef` struct for assignee details
- `Email` custom type with regex constraint
- `triageTicket` action and `TicketCreated` signal
- `onTicketCreated` trigger that invokes triage

## What This Example Showcases

- Custom type constraints (`constraint pattern`) and SHACL projection
- Structs embedded in objects (`assignee: UserRef`)
- Object references (`ref(Ticket)`) for action/signal payloads
- Lists (`string[]`) in object fields
- Human-facing labels via DSL `name "..."` metadata
- State machine basics: `state`, `transition`, `initial`
- Action inline output (`output { ... }`) deriving `<ActionName>Result`
- Deterministic Turtle generation in `gen/turtle/ontology.ttl`

## Files to Inspect

- DSL source: `ontology/local/main.prophet`
- Project config: `prophet.yaml`
- Generated Turtle: `gen/turtle/ontology.ttl`

## Generate

```bash
cd examples/turtle/prophet_example_turtle_minimal
$(git rev-parse --show-toplevel)/.venv/bin/prophet validate
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
```

## SHACL Validate Generated Turtle

```bash
cd $(git rev-parse --show-toplevel)
pyshacl -s prophet.ttl -d prophet.ttl examples/turtle/prophet_example_turtle_minimal/gen/turtle/ontology.ttl -e prophet.ttl --advanced --inference owlrl --format turtle
```
