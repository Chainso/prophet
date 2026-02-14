# Changelog

All notable changes to `prophet-cli` are documented in this file.

## [Unreleased]

## [0.4.0] - 2026-02-14

### Added
- Standardized `IRReader` boundary for target generation and target-level IRReader contract tests.
- Typed IR contract views (`ActionContractView`, `QueryContractView`) and reference-target adoption for extension hook generation.
- Extension hook manifest output (`gen/manifest/extension-hooks.json`) and `prophet hooks` / `prophet hooks --json` command.
- Schema-validated stack manifest governance (`prophet_cli.codegen.stack_manifest`) with stricter stack matrix validation.
- `prophet stacks --json` output for automation and CI tooling.
- Generator registry contract test to enforce mapping between implemented stacks and concrete generators.
- Semantic conformance tests for canonical IR action/query/struct/object-ref contracts independent of file snapshots.
- Dedicated cache module (`prophet_cli.codegen.cache`) with deterministic signature and cache IO tests.
- Regeneration safety integration tests and extension policy documentation.
- Reproducible no-op benchmark script and published baseline benchmark report.
- Formal modularization phase closeout artifact documenting milestone completion and validation evidence.

### Changed
- `prophet gen --skip-unchanged` now uses modular cache helpers and `prophet clean` removes generation cache metadata.
- Plan/check JSON stack payloads now include explicit `status` and `implemented` fields.
- Stack diagnostics now include manifest schema metadata, stack descriptions, and default target metadata.

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
