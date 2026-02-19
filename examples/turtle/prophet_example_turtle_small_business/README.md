# Prophet Example: Turtle Small Business (Complex Domain)

This is a realistic, multi-entity Prophet ontology intended for integration and model-stress testing.

## What This Example Models

A neighborhood bakery operations domain with connected business workflows:
- Customers and employees
- Suppliers and products
- Inventory tracking and restocking
- Sales orders, purchase orders, invoices, deliveries
- Payments and low-stock event automation

## What This Example Showcases

- Rich relationship graph via `ref(...)` across many objects
- Self-reference (`Employee.manager -> ref(Employee)`)
- Reusable structs (`Address`, `ContactPoint`, line-item structs, payment details)
- Custom constrained types (`Money`, `Quantity`, `Email`, `CurrencyCode`, `PhoneNumber`)
- Multiple state machines with transitions:
  - `PurchaseOrder`: `draft -> submitted -> received -> closed`
  - `SalesOrder`: `pending_payment -> paid -> fulfilled` and cancellation path
  - `Invoice`: `issued -> paid` and overdue path
- All action output styles:
  - inline `output { ... }`
  - `output signal <SignalName>`
  - `output transition <Object>.<transition>`
- Trigger-driven orchestration:
  - low stock to purchase flow
  - purchase receipt to restock flow
  - payment signal to invoice state transition
  - sales payment transition to fulfillment

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
- multiple transition/event paths
- higher-volume Turtle output for ontology tooling tests
- regression coverage beyond the minimal happy path
