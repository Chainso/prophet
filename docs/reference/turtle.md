# Turtle Target Reference

Prophet can emit a Turtle projection of canonical IR as an additional generated artifact.

## Target Name

- `turtle`

## Output Path

- `gen/turtle/ontology.ttl`

## Prefix and Vocabulary Rules

- Generated triples use the base Prophet vocabulary prefix: `prophet: <http://prophet.platform/ontology#>`
- Standard base types use: `std: <http://prophet.platform/standard-types#>`
- The local ontology prefix is derived from the ontology name (for example `support_local:`), not a hardcoded `example` prefix.

## How to Enable

Add `turtle` to `generation.targets` for any supported stack.

Example (Java stack):

```yaml
generation:
  stack:
    id: java_spring_jpa
  targets: [sql, openapi, turtle, spring_boot, manifest]
```

Example (Node stack):

```yaml
generation:
  stack:
    id: node_express_prisma
  targets: [sql, openapi, turtle, node_express, prisma, manifest]
```

Example (Python stack):

```yaml
generation:
  stack:
    id: python_fastapi_sqlalchemy
  targets: [sql, openapi, turtle, python, fastapi, sqlalchemy, manifest]
```

## Generated Content Shape

The Turtle output is generated deterministically from IR and includes:
- local ontology metadata
- custom types
- structs and property definitions
- object models, keys, states, transitions
- action inputs/outputs and actions
- signals/events and triggers
- derived list type nodes

The output is aligned to the base metamodel in [`prophet.ttl`](../../prophet.ttl), including:
- SHACL `NodeShape` resources for custom type constraints (`prophet:hasConstraint`)
- `prophet:ObjectReference` resources for `ref(Object)` field types
- `prophet:initialState` on object models (instead of per-state flags)

## Constraint Escaping

Regex constraints from DSL are decoded once from DSL string form and then escaped for Turtle literals.
For example, this DSL pattern:

```prophet
constraint pattern "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"
```

is emitted as:

```turtle
sh:pattern "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"
```

and validated by SHACL exactly as intended.

## SHACL Validation

Validate generated Turtle against the base ontology/shapes with:

```bash
# Minimal example
cd examples/turtle/prophet_example_turtle_minimal
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
cd $(git rev-parse --show-toplevel)
pyshacl -s prophet.ttl -d prophet.ttl examples/turtle/prophet_example_turtle_minimal/gen/turtle/ontology.ttl -e prophet.ttl --advanced --inference owlrl --format turtle

# Complex small-business example
cd examples/turtle/prophet_example_turtle_small_business
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
cd $(git rev-parse --show-toplevel)
pyshacl -s prophet.ttl -d prophet.ttl examples/turtle/prophet_example_turtle_small_business/gen/turtle/ontology.ttl -e prophet.ttl --advanced --inference owlrl --format turtle
```

## Minimal Turtle Example

A minimal initialized Turtle example is provided at:
- [examples/turtle/prophet_example_turtle_minimal](../../examples/turtle/prophet_example_turtle_minimal)

This example includes Prophet project scaffolding plus a minimal ontology, but no runtime app code.

## Complex Turtle Example

A richer small-business Turtle example is also available at:
- [examples/turtle/prophet_example_turtle_small_business](../../examples/turtle/prophet_example_turtle_small_business)

This model includes multiple related entities, lifecycle transitions, reusable structs, and trigger wiring intended for more realistic testing scenarios.
