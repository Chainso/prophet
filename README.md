# Prophet

Prophet is an ontology compiler kernel for business-domain systems.  
It turns a domain DSL into deterministic artifacts: schema, API contracts, and a Spring Boot integration module.

## Status

- Toolchain release: `0.3.0`
- Golden runtime target: Spring Boot
- Example app: `examples/java/prophet_example_spring`

## What You Get

- Ontology validation and canonical IR generation
- Deterministic codegen:
  - SQL schema
  - OpenAPI
  - Flyway/Liquibase migrations (init + baseline-aware delta)
  - Spring Boot module (domain DTOs, JPA layer, action/query APIs)
- Compatibility/version checks against a baseline IR
- CI-ready `prophet check` command

## Repository Map

- `prophet-cli/`: CLI package (`prophet`)
- `prophet-cli/src/prophet_cli/core/`: modularized compiler core (parser, validation, IR, compatibility)
- `docs/`: DSL, architecture, JPA mapping, compatibility policy
- `docs/prophet-generator-modularization-roadmap-v0.1.md`: modularization strategy and contributor-ready execution roadmap
- `examples/java/prophet_example_spring/`: runnable Spring example + profile tests
- `.github/workflows/ci.yml`: CI gates for Python + Spring validation
- `prophet.ttl`: base ontology model

## Quick Start

```bash
python3 -m venv .venv --system-site-packages
.venv/bin/pip install --no-build-isolation -e ./prophet-cli

cd examples/java/prophet_example_spring
$(git rev-parse --show-toplevel)/.venv/bin/prophet validate
$(git rev-parse --show-toplevel)/.venv/bin/prophet plan --show-reasons
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen --wire-gradle
$(git rev-parse --show-toplevel)/.venv/bin/prophet check --show-reasons
$(git rev-parse --show-toplevel)/.venv/bin/prophet check --json
./gradlew :prophet_generated:compileJava compileJava
./gradlew test
./gradlew bootRun
```

## Example Runtime Profiles

- `h2` (default): embedded development profile
- `postgres`: production-style profile (driven by `SPRING_DATASOURCE_*`)

Profile tests run via:

```bash
cd examples/java/prophet_example_spring
./gradlew test
```

## Generated Outputs

From `prophet gen`:

- `.prophet/ir/current.ir.json`
  - includes `query_contracts` + `query_contracts_version` for explicit API/filter compatibility tracking
- `gen/sql/schema.sql`
- `gen/openapi/openapi.yaml`
- `gen/migrations/flyway/V1__prophet_init.sql`
- `gen/migrations/liquibase/prophet/0001-init.sql`
- Baseline-aware delta outputs when baseline differs:
  - `gen/migrations/flyway/V2__prophet_delta.sql`
  - `gen/migrations/liquibase/prophet/0002-delta.sql`
  - `gen/migrations/delta/report.json`
  - report includes `summary` counts and structured `findings` (including rename hints for manual review)
- `gen/spring-boot/**` (generated integration module)

## Query and Action Surface

- Actions are generated as API endpoints at `/actions/*`
- Controllers delegate to generated action services (`generated.actions.services.*`)
- Object APIs include:
  - `GET /<objects>`
  - `GET /<objects>/{id}`
  - `POST /<objects>/query` with typed filter DSL (`eq`, `in`, `gte`, `lte`, `contains`)
- Query layer maps entities via generated mappers (`generated.mapping.*DomainMapper`)

## Compatibility Policy

Compatibility/version rules are documented in:

- `docs/prophet-compatibility-policy-v0.2.md`

The CLI prints this path during `prophet plan`, `prophet version check`, and `prophet check`.

## Release and Changelog

- Release process: `prophet-cli/RELEASING.md`
- Changelog: `prophet-cli/CHANGELOG.md`

## Contributing

- Contribution guide: `CONTRIBUTING.md`
- AI agent guide: `AGENTS.md`
- Open items/backlog: `CONTRIBUTING.md` (`Open Items`)
