# Prophet

Prophet is an ontology compiler kernel for business-domain systems.

## Current State

This repository currently contains:
- `prophet.ttl` (base ontology)
- `docs/prophet-spec-v0.1.md` (product and technical contracts)
- `docs/prophet-dsl-v0.1.md` (DSL language reference and examples)
- `docs/prophet-spring-boot-golden-stack-v0.1.md` (deep integration contract)
- `docs/prophet-jpa-mapping-v0.1.md` (ontology-to-database/JPA translation rules)
- `docs/prophet-compatibility-policy-v0.2.md` (semantic compatibility policy tables)
- `prophet-cli/` Python package for the CLI (`prophet_cli`)
- `prophet-cli/RELEASING.md` + `prophet-cli/CHANGELOG.md` (release process + history)
- `.github/workflows/ci.yml` (Python + Spring validation gates for PRs)
- `./prophet` root launcher script (local convenience wrapper)
- `examples/java/prophet_example_spring` standalone Spring Boot + H2 example app

## Quick Start (Example Project)

```bash
python3 -m venv .venv --system-site-packages
.venv/bin/pip install --no-build-isolation -e ./prophet-cli

cd examples/java/prophet_example_spring
../../../.venv/bin/prophet validate
../../../.venv/bin/prophet plan --show-reasons
../../../.venv/bin/prophet gen --wire-gradle
./gradlew :prophet_generated:compileJava compileJava
./gradlew bootRun
```

Example runtime profiles:
- `h2` (default): embedded local development profile
- `postgres`: production-style profile (`SPRING_DATASOURCE_*` env vars)

Run example profile tests:

```bash
cd examples/java/prophet_example_spring
./gradlew test
```

## What `prophet gen` Produces

- Canonical IR: `.prophet/ir/current.ir.json`
- SQL schema: `gen/sql/schema.sql`
- OpenAPI: `gen/openapi/openapi.yaml`
- Flyway migration: `gen/migrations/flyway/V1__prophet_init.sql`
- Liquibase changelog + SQL:
`gen/migrations/liquibase/db.changelog-master.yaml`, `gen/migrations/liquibase/prophet/*`
- Baseline-aware delta migrations (when baseline differs):
`gen/migrations/flyway/V2__prophet_delta.sql`, `gen/migrations/liquibase/prophet/0002-delta.sql`, `gen/migrations/delta/report.json`
- Spring module: `gen/spring-boot`
: includes generated domain records, JPA entities/repositories, action contracts, action controllers, query controllers, and migration resources auto-wired to the host app's existing migration stack

## Notes

- `gen/` is tool-owned and should be regenerated, not hand-edited.
- `id` values in ontology definitions are immutable compatibility anchors.
- Breaking/additive classification rules are defined in `docs/prophet-spec-v0.1.md`.
- v0.1 golden runtime integration target is Spring Boot.
- In v0.1 codegen, actions are generated as direct API endpoints (`/actions/*`).
- Action API payloads come from DSL `actionInput`/`actionOutput` contracts.
- Generated action endpoints delegate to generated action services; default services delegate to handler beans.
- Generated default handler stubs throw `UnsupportedOperationException` and endpoints return `501` until replaced by user beans.
- DSL fields support scalar and list types (for example `string[]` or `list(string)`).
- DSL supports nested list types (for example `string[][]`) and reusable `struct` types for non-entity nested payloads.
- Event ingestion/dispatch remains an external runtime concern, not Spring codegen output.
- Generated query APIs include:
`GET /<objects>/{id}` and paginated/filterable `GET /<objects>` backed by JPA specifications.
- Generated typed query DSL endpoint:
`POST /<objects>/query` with filter contracts supporting `eq`, `in`, `gte`, `lte`, `contains` (by type).
- List endpoints return generated DTO envelopes (`*ListResponse`) instead of raw Spring `Page` serialization.
- Generated query controllers use generated mapping components (`generated.mapping.*DomainMapper`) for entity-to-domain conversion boundaries.
