# Changelog

All notable changes to `prophet-cli` are documented in this file.

## [0.3.0] - 2026-02-14

### Added
- Real Postgres profile context test coverage via Testcontainers in the Spring example app.
- Delta migration report intelligence:
  - structured `summary` counts,
  - structured `findings`,
  - heuristic `object_rename_hint` and `column_rename_hint` diagnostics.
- Versioned query contract manifest in IR (`query_contracts`, `query_contracts_version`) with explicit compatibility checks for query paths/filters/operators.
- Structured diagnostics mode: `prophet check --json`.
- End-to-end HTTP action-flow integration test in the Spring example (`createOrder -> approveOrder -> shipOrder -> query/get`).

### Changed
- Toolchain version bumped to `0.3.0`.
- Example documentation expanded for typed query endpoints and integration test coverage.

## [0.2.0] - 2026-02-14

### Added
- Baseline-aware delta migration generation for Flyway/Liquibase:
  - `V2__prophet_delta.sql`
  - `0002-delta.sql`
  - `gen/migrations/delta/report.json`
- Delta safety flags and warnings (`destructive_changes`, `backfill_required`, `manual_review_required`).
- Generated action service boundary (`generated.actions.services.*`) with controller delegation.
- Typed filter DSL generation for object queries:
  - generated filter DTOs
  - `POST /<objects>/query` endpoints
  - OpenAPI schemas and paths for typed query contracts.
- Compatibility policy reference output in CLI (`plan`, `version check`, `check`).
- Example runtime profile coverage for `h2` and `postgres` with Spring context tests.
- CI release discipline workflow for Python + Spring validation gates.

### Changed
- Toolchain version bumped to `0.2.0`.
- Generated Spring module version now tracks CLI toolchain version.

## [0.1.0] - 2026-02-14

### Added
- Prophet DSL parser and validator with compatibility-aware IR generation.
- Deterministic code generation targets for SQL, OpenAPI, Spring Boot module, Flyway, and Liquibase.
- Spring Boot golden-path output with generated:
  - domain records and action contracts,
  - action endpoint controllers and handler interfaces,
  - JPA entities/repositories and pagination/filter query APIs.
- Gradle multi-module wiring and unwiring support (`prophet gen --wire-gradle`, `prophet clean`).
- Snapshot and end-to-end integration tests for generator and CLI flows.
- Migration runtime autodetection warnings for host Gradle projects.
- Java record builder generation and builder-based query DTO/domain mapping.

### Notes
- This is the first release baseline for Prophet tooling.
