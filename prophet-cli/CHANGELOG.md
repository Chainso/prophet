# Changelog

All notable changes to `prophet-cli` are documented in this file.

## [Unreleased]

## [0.8.3] - 2026-02-15

### Fixed
- Node Express transition event contracts now match the simplified transition model and no longer generate `fromState` / `toState` payload fields.

### Changed
- Java Spring example ontology version updated to `1.0.0` so compatibility checks align with required major bump semantics.
- README wording updated to use `Generation manifests` capitalization.
- Toolchain/package version advanced to `0.8.3`.

## [0.8.2] - 2026-02-15

### Fixed
- Node Express ESM codegen now emits explicit `.js` relative import specifiers in generated TypeScript sources to satisfy `moduleResolution: NodeNext` builds.
- Node Express + TypeORM codegen nullability/strictness fixes:
  - generated entity fields now use strict-property-safe declarations for required columns,
  - nullable columns now emit `| null`-aware field types,
  - generated adapters map optional domain values to nullable persistence columns consistently.
- Node target test expectations aligned with strict TypeORM entity output.

### Changed
- Added Node example build output ignore rule for `examples/node/**/dist/`.
- Toolchain/package version advanced to `0.8.2`.

## [0.8.1] - 2026-02-15

### Fixed
- Node Express + TypeORM runtime initialization bug in generated repositories:
  - generated `TypeOrmRepository` classes now initialize `repo` inside constructors (after `DataSource` is available),
  - prevents `Cannot read properties of undefined (reading 'getRepository')` on app startup.
- Node Express + Prisma generation compatibility improvements:
  - Prisma datasource provider is generated as a concrete provider value (default `sqlite`, configurable in `prophet.yaml`),
  - provider/env and list/struct schema edge cases resolved for generated Prisma schema and adapters.

### Changed
- Expanded docs and references for Node runtime behavior and TypeORM production DB ownership (`DataSource` configuration in host app).
- Updated AGENTS/developer/user docs structure and removed obsolete Node roadmap document.
- Added repository ignore rules for local Node example SQLite test DB files.
- Added and track `package-lock.json` files for Node example projects.
- Toolchain/package version advanced to `0.8.1`.

## [0.8.0] - 2026-02-15

### Added
- Automatic source hydration for missing DSL IDs:
  - parsing commands now materialize generated `id "..."` lines back into the ontology file,
  - stable, non-conflicting IDs are synthesized for ontology elements when omitted.
- Integration coverage for source ID hydration behavior in CLI tests.

### Changed
- Action contract syntax is now inline-only:
  - `input { ... }`
  - `output { ... }`
- DSL field ergonomics updated so fields are required by default; users only write `optional` for nullable fields.
- Updated DSL reference and canonical Spring example ontology to reflect the new contract and requiredness rules.
- Toolchain/package version advanced to `0.8.0`.

## [0.7.0] - 2026-02-14

### Added
- Generated event contracts for ontology events under `generated.events.*`:
  - `action_output` event payload wrappers,
  - `signal` event contracts,
  - `transition` event contracts including `fromState`/`toState`.
- Generated `GeneratedEventEmitter` interface with one typed emit method per event.
- Generated default `GeneratedEventEmitterNoOp` Spring component for zero-config event emission wiring.

### Changed
- Generated action service defaults now emit their corresponding `action_output` events automatically after handler execution.
- Event model generation now includes object reference records required by event payload contracts.
- Toolchain/package version advanced to `0.7.0`.

## [0.6.2] - 2026-02-14

### Changed
- Restructured documentation into separate quickstart, user reference, and developer sections.
- Rewrote top-level README for first-time users with a plain-language ontology explanation.
- Added Prophet brand assets and usage guidelines under `brand/`.
- Updated CLI compatibility policy reference path to `docs/reference/compatibility.md`.

## [0.6.1] - 2026-02-14

### Changed
- Patch release to validate trusted-publisher PyPI release flow from GitHub Actions.
- Version and generated example manifests updated to toolchain `0.6.1`.

## [0.6.0] - 2026-02-14

### Added
- Dedicated PyPI publish workflow (`.github/workflows/publish-pypi.yml`) triggered by release tags and manual dispatch.
- Package build validation in CI (`python -m build`, `twine check`, wheel install smoke test).
- Repository Apache-2.0 license (`LICENSE`) and package-distributed license file (`prophet-cli/LICENSE`).

### Changed
- Hardened CI into separate package and Spring integration jobs, with generated-output cleanliness verification and tracked-file drift checks.
- Removed the repository root `./prophet` wrapper; CLI usage now relies on installed `prophet` console scripts from the package.

## [0.5.3] - 2026-02-14

### Changed
- Updated the Spring example README to reflect current generated API behavior:
  - `GET /<objects>` as pagination/sort only.
  - typed filtering centralized on `POST /<objects>/query`.
  - ontology-scoped generated package path examples.
- Synced generated example manifest/module metadata to toolchain version `0.5.3`.

## [0.5.2] - 2026-02-14

### Changed
- `GET /<objects>` list endpoints are now pagination/sort only.
- All field/state filtering is now centralized on `POST /<objects>/query`.
- Updated generated Spring query controllers, OpenAPI docs, and project documentation to reflect query-only filtering.

## [0.5.1] - 2026-02-14

### Fixed
- Updated Spring example action handlers to import generated classes from ontology-scoped package paths (`com.example.prophet.commerce_local.generated.*`).
- Restored clean example build after `0.5.0` package namespace changes.

## [0.5.0] - 2026-02-14

### Added
- DSL metadata support via `description "..."` / `documentation "..."` across ontology entities.
- Composite primary key declarations via object-level `key primary (fieldA, fieldB)` syntax.
- Optional object-level display key marker via `key display (...)` metadata.
- Composite-key-aware SQL/JPA/query/openapi generation, including multi-segment get-by-id paths.
- New DSL feature tests for metadata and composite-key validation coverage.

### Changed
- Spring generated package root is now ontology-scoped: `<base_package>.<ontology_name>`.
- Generated JavaDoc and OpenAPI summaries now derive from DSL metadata when provided.
- Validation now enforces current object-reference constraint: target object refs require single-field primary keys.
- Compatibility diffing ignores description-only changes for actions/events/triggers.

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
