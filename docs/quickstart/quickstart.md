# Prophet Quickstart

This guide is for integrating Prophet into your own project.

If you want runnable sample applications, use [Examples](../reference/examples.md).

## 1. Install Prophet CLI

Install from PyPI:

```bash
python3 -m pip install --upgrade prophet-cli
prophet --help
```

Or install from this repository:

```bash
python3 -m venv .venv --system-site-packages
.venv/bin/pip install --no-build-isolation -e ./prophet-cli
```

## 2. Initialize Your Project

Run in your project root:

```bash
prophet init
```

This creates:
- `prophet.yaml`
- `ontology/local/main.prophet`
- `.prophet/` runtime metadata

## 3. Define Your Ontology

Edit `ontology/local/main.prophet` to model objects, structs, actions, and signals.

```prophet
ontology CommerceLocal {
  name "Commerce Local"
  version "0.1.0"

  object Order {
    name "Order"
    field orderId { name "Order ID" type string key primary }
    field customerUserId { name "Customer User ID" type string }
    field totalAmount { name "Total Amount" type decimal }
    field discountCode { name "Discount Code" type string optional }
    field tags { name "Tags" type string[] optional }
    state pending { initial }
    state approved {}
    transition approve {
      from pending
      to approved
    }
  }

  struct ShippingAddress {
    name "Shipping Address"
    field line1 { name "Line 1" type string }
    field city { name "City" type string }
    field countryCode { name "Country Code" type string }
  }

  action createOrder {
    name "Create Order"
    kind process
    input {
      field customerUserId { name "Customer User ID" type string }
      field totalAmount { name "Total Amount" type decimal }
      field shippingAddress { name "Shipping Address" type ShippingAddress }
    }
    output {
      field order { name "Order" type ref(Order) }
    }
  }

  signal PaymentCaptured {
    name "Payment Captured"
    field order { name "Order" type ref(Order) }
    field providerRef { name "Provider Reference" type string }
  }
}
```

Naming guidance:
- Keep technical symbols (`object Order`, `field orderId`) stable for references and wire keys.
- Use `name "..."` metadata for human-facing labels in docs/UIs.

Action output forms:
- `output { ... }` for inline signal payloads (derived event `<ActionName> Result`)
- `output signal <SignalName>`
- `output transition <ObjectName>.<TransitionName>`

Reserved field name:
- `state` is reserved and cannot be declared manually in DSL fields.

## 4. Configure Generation

Set your stack and targets in `prophet.yaml`.

Java Spring + JPA:

```yaml
generation:
  stack:
    id: java_spring_jpa
  targets: [sql, openapi, turtle, spring_boot, manifest]
  spring_boot:
    base_package: com.example
```

Node Express + Prisma:

```yaml
generation:
  stack:
    id: node_express_prisma
  targets: [sql, openapi, turtle, node_express, prisma, manifest]
```

Python FastAPI + SQLAlchemy:

```yaml
generation:
  stack:
    id: python_fastapi_sqlalchemy
  targets: [sql, openapi, turtle, python, fastapi, sqlalchemy, manifest]
```

## 5. Validate and Generate

```bash
prophet validate
prophet plan --show-reasons
prophet gen
```

Generated outputs include:
- `.prophet/ir/current.ir.json`
- `gen/sql/schema.sql`
- `gen/openapi/openapi.yaml`
- `gen/turtle/ontology.ttl` (when `turtle` target is enabled)
- stack-specific generated runtime code under `gen/**`

Optional Turtle conformance check:

```bash
pyshacl -s prophet.ttl -d prophet.ttl gen/turtle/ontology.ttl -e prophet.ttl --advanced --inference owlrl --format turtle
```

## 6. Implement User-Owned Extension Points

Prophet generates contracts, routes/controllers, repositories, and handler interfaces.
You implement business logic in generated extension seams:
- action handler implementations
- repository wiring and DB connection ownership
- optional event publisher implementation

Generated default handlers are intentionally non-functional until replaced.

## 7. Add Verification Gates

Use these checks in CI:

```bash
prophet check --show-reasons
prophet gen --verify-clean
```

## Language-Specific Quickstarts

- Java: [Spring + JPA Quickstart](java.md)
- Node: [Express Quickstart](node.md)
- Python: [FastAPI / Flask / Django Quickstart](python.md)

## Next Reads

- CLI reference: [CLI](../reference/cli.md)
- DSL reference: [DSL](../reference/dsl.md)
- Config reference: [Config](../reference/config.md)
- Turtle target details: [Turtle](../reference/turtle.md)
- Integration examples: [Examples](../reference/examples.md)
