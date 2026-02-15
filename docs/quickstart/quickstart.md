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
  version "0.1.0"

  object Order {
    field orderId { type string key primary }
    field customerUserId { type string }
    field totalAmount { type decimal }
    field discountCode { type string optional }
    field tags { type string[] optional }
  }

  struct ShippingAddress {
    field line1 { type string }
    field city { type string }
    field countryCode { type string }
  }

  action createOrder {
    kind process
    input {
      field customerUserId { type string }
      field totalAmount { type decimal }
      field shippingAddress { type ShippingAddress }
    }
    output {
      field order { type ref(Order) }
      field currentState { type string }
    }
  }

  signal PaymentCaptured {
    field order { type ref(Order) }
    field providerRef { type string }
  }
}
```

## 4. Configure Generation

Set your stack and targets in `prophet.yaml`.

Java Spring + JPA:

```yaml
generation:
  stack:
    id: java_spring_jpa
  targets: [sql, openapi, spring_boot, manifest]
  spring_boot:
    base_package: com.example
```

Node Express + Prisma:

```yaml
generation:
  stack:
    id: node_express_prisma
  targets: [sql, openapi, node_express, prisma, manifest]
```

Python FastAPI + SQLAlchemy:

```yaml
generation:
  stack:
    id: python_fastapi_sqlalchemy
  targets: [sql, openapi, python, fastapi, sqlalchemy, manifest]
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
- stack-specific generated runtime code under `gen/**`

## 6. Implement User-Owned Extension Points

Prophet generates contracts, routes/controllers, repositories, and handler interfaces.
You implement business logic in generated extension seams:
- action handler implementations
- repository wiring and DB connection ownership
- optional event emitter implementation

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
- Integration examples: [Examples](../reference/examples.md)
