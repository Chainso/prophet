# Prophet Example: Turtle Small Business (Complex Domain)

This is a realistic, multi-entity Prophet ontology intended for integration and model-stress testing.

## What This Example Models

A neighborhood bakery operations domain with connected business workflows:
- Customers and employees
- Suppliers and products
- Inventory tracking and restocking
- Sales orders, purchase orders, invoices, deliveries
- Payments and low-stock event automation

## Status

This example is fully migrated to the current field-level state model. Stateful objects use enum fields marked with `state`, and actions emit explicit domain events.

## What This Example Showcases

- Rich relationship graph via `ref(...)` across many objects
- Self-reference (`Employee.manager -> ref(Employee)`)
- Reusable structs (`Address`, `ContactPoint`, line-item structs, payment details)
- Custom constrained types (`Money`, `Quantity`, `Email`, `CurrencyCode`, `PhoneNumber`)
- Human-facing labels via DSL `name "..."` metadata
- Field-level state metadata on enum fields
- Explicit domain events and trigger-driven automation across a dense ontology

## Files to Inspect

- DSL source: `ontology/local/main.prophet`
- Project config: `prophet.yaml`
- Generated Turtle: `gen/turtle/ontology.ttl`

## Generate

```bash
cd examples/turtle/prophet_example_turtle_small_business
$(git rev-parse --show-toplevel)/.venv/bin/prophet validate
$(git rev-parse --show-toplevel)/.venv/bin/prophet check --show-reasons
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
```

## SHACL Validate Generated Turtle

```bash
cd $(git rev-parse --show-toplevel)
pyshacl -s prophet.ttl -d prophet.ttl examples/turtle/prophet_example_turtle_small_business/gen/turtle/ontology.ttl -e prophet.ttl --advanced --inference owlrl --format turtle
```

## Why Use This Example

Use this model when you need:
- realistic relationship density
- higher-volume Turtle output for ontology tooling tests
- a larger example with field-level state and explicit event flows
