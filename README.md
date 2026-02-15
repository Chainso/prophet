<p align="center">
  <img src="brand/exports/logo-horizontal-color.png" alt="Prophet logo" />
</p>

---

Prophet is a tool that turns your business model into working software scaffolding.

Instead of hand-writing the same model in many places, you define it once and Prophet generates the repetitive pieces for you.

## What Is an Ontology?

In Prophet, an ontology is a structured definition of your domain:
- what things exist (for example: `Order`, `User`)
- what data each thing has (fields and types)
- how those things relate to each other
- what actions exist and what they accept/return

Think of it as a single source of truth for your system design.

## Why This Matters

Without a source of truth, teams duplicate domain definitions across:
- API contracts
- database schemas
- service code
- framework wiring

That duplication causes drift and bugs. Prophet reduces that by compiling one domain definition into consistent outputs.

## What Prophet Generates

From a `.prophet` ontology file, Prophet can generate:
- SQL schema files
- OpenAPI contracts
- Spring Boot integration code (DTOs, JPA entities/repositories, query and action endpoints)
- Node/Express integration code (typed contracts, zod validation, action/query routes, event emitter interfaces)
- Prisma schema + repository adapters for Node targets
- TypeORM entities + repository adapters for Node targets (wired through your application-owned `DataSource`)
- Flyway/Liquibase migration artifacts
- generation manifests for ownership and extension hooks

## How Prophet Is Used

1. Define your domain in Prophet DSL.
2. Run validation.
3. Generate artifacts.
4. Add your business logic in user-owned extension points.
5. Evolve safely with compatibility/version checks.

## Install

From PyPI:

```bash
python3 -m pip install --upgrade prophet-cli
prophet --help
```

From source (editable install):

```bash
python3 -m venv .venv --system-site-packages
.venv/bin/pip install --no-build-isolation -e ./prophet-cli
```

## Get Started

- First run guide: [Quickstart](docs/quickstart/quickstart.md)
- Full user reference: [Reference Index](docs/reference/index.md)
- Developer docs: [Developer Index](docs/developer/index.md)

## Supported Stacks

Implemented stacks:
- `java` + `spring_boot` + `jpa`
- `node` + `express` + `prisma`
- `node` + `express` + `typeorm`

Examples:
- [Spring Example](examples/java/prophet_example_spring)
- [Express + Prisma Example](examples/node/prophet_example_express_prisma)
- [Express + TypeORM Example](examples/node/prophet_example_express_typeorm)

## License

Apache-2.0. See [LICENSE](LICENSE).
