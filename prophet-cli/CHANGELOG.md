# Changelog

All notable changes to `prophet-cli` are documented in this file.

## [Unreleased]

## [0.24.0] - 2026-02-28

### Changed
- Added high-quality descriptions across all maintained example ontologies for all DSL concept blocks that support `description` metadata.
- Regenerated maintained Java/Node/Python/Turtle example artifacts and manifests to reflect ontology description coverage.
- Toolchain/package version advanced to `0.24.0`.

## [0.23.0] - 2026-02-28

### Changed
- Updated inline action-derived contract naming to use spaced names:
  - input shape: `<ActionName> Command`,
  - inline output signal: `<ActionName> Result`.
- Updated derivation to use action display metadata (`name "..."`) as the action-name base when present.
- Updated Java Spring generation to normalize spaced action/event contract names into valid Java type/file identifiers while preserving IR/wire event names.
- Updated DSL/quickstart/concepts/developer docs to reflect spaced action-derived naming.
- Regenerated maintained Java example artifacts and snapshot manifests for the naming behavior change.
- Bumped maintained example ontology versions from `1.0.0` to `2.0.0` and regenerated Java/Node/Python artifacts to satisfy compatibility checks for the breaking event-name change.
- Toolchain/package version advanced to `0.23.0`.

## [0.22.0] - 2026-02-19

### Changed
- Bumped shared runtime libraries to `0.5.0` across:
  - `@prophet-ontology/events-runtime`,
  - `prophet-events-runtime`,
  - `io.github.chainso:prophet-events-runtime`.
- Updated default generator runtime version resolution to `0.5.0`.
- Regenerated maintained Java/Node/Python/Turtle examples so generated runtime dependency pins and manifests align with the runtime bump.
- Toolchain/package version advanced to `0.22.0`.

## [0.21.0] - 2026-02-19

### Added
- Added optional DSL `name "..."` metadata across ontology elements and fields for human-facing display labels.
- Added a realistic Turtle small-business example (`examples/turtle/prophet_example_turtle_small_business`) covering dense entity relationships, reusable structs, transitions, mixed action outputs, and triggers.
- Added dedicated example README coverage for every maintained example with model/surface-focused guidance.

### Changed
- Updated IR and generators to carry display-name metadata (`display_name`) while preserving technical symbols for stable wire keys and references.
- Updated Turtle rendering to source `prophet:name` from display names (with technical fallback) while preserving technical field keys via `prophet:fieldKey`.
- Updated OpenAPI rendering to emit display-name hints (`title`, `x-prophet-display-name`) without changing generated property keys.
- Regenerated maintained example outputs and refreshed example compatibility baselines after the naming rollout.
- Toolchain/package version advanced to `0.21.0`.

## [0.20.0] - 2026-02-17

### Added
- Implemented the transition/event redesign end-to-end:
  - action outputs are modeled as produced events (`signal` or `transition`),
  - DSL supports `output { ... }`, `output signal <SignalName>`, and `output transition <Object>.<Transition>`,
  - transition payloads include implicit object primary keys plus `fromState`/`toState`.
- Added generated per-object transition validator seams across Java/Node/Python and wired runtime `TransitionValidationResult` into default transition handlers.
- Added generated transition draft flow across stacks so transition handlers return drafts seeded with implicit transition fields.

### Changed
- Reworked metamodel/core/compiler/codegen to remove legacy action-output modeling and consume `output_event_id` event contracts.
- Standardized state persistence on internal `__prophet_state` while exposing logical `state` in generated domain/query contracts.
- Regenerated all example stacks at ontology version `1.0.0` with clean baselines (no example `V2` delta migration artifacts).
- Bumped `prophet-lib` runtime packages to `0.4.0` and refreshed generated/runtime version references.
- Toolchain/package version advanced to `0.20.0`.

### Fixed
- Updated FastAPI example HTTP tests to use async `httpx.ASGITransport` clients for stable execution under current Python runtime behavior.
- Updated SQLModel generated history timestamp default to timezone-aware UTC (`datetime.now(timezone.utc)`), removing `datetime.utcnow()` deprecation warnings.

## [0.19.0] - 2026-02-17

### Added
- Added SQL/Flyway/Liquibase display-key index generation (`idx_<table>_display`) when an explicit `key display (...)` declaration is present and differs from the primary key columns.
- Added delta-migration handling for display-key index changes so display index add/remove/change operations are emitted in generated migration SQL.
- Added SQL renderer test coverage for display-key index generation and display-index delta migration behavior.

### Changed
- Updated DSL/reference/Node docs to describe display-key indexing behavior across SQL, Prisma, and Mongoose generation paths.
- Toolchain/package version advanced to `0.19.0`.

## [0.18.0] - 2026-02-17

### Added
- Added generated event payload ref union contracts so object-ref fields accept either refs or full object snapshots (`<Object>RefOrObject` in Java sealed types, `<Object>Ref | <Object>` in Node/Python contracts).
- Added event-envelope extraction of embedded object snapshots into `updated_objects` (`updatedObjects` in Java) while normalizing payload fields back to refs.

### Changed
- Updated generated action-service event publishing flows to normalize ref-or-full payloads for action-output and signal domain events, while keeping transition event emission user-controlled.
- Bumped `prophet-lib` runtime packages to `0.3.0` and refreshed generated/runtime version references.
- Toolchain/package version advanced to `0.18.0`.

## [0.17.3] - 2026-02-17

### Changed
- Updated `publish-pypi` Python smoke-import and integration test steps to prepend `prophet-lib/python/src` to `PYTHONPATH`, ensuring generated modules can import `prophet_events_runtime` during CLI release validation.
- Bumped `prophet-lib` runtime packages to `0.2.9` and refreshed runtime version references.
- Toolchain/package version advanced to `0.17.3`.

## [0.17.2] - 2026-02-17

### Changed
- Updated `publish-pypi` validation to publish `prophet-lib` Java runtime to `mavenLocal` before compiling generated Spring sources, ensuring local runtime dependency resolution succeeds.
- Bumped `prophet-lib` runtime packages to `0.2.8` and refreshed runtime version references.
- Toolchain/package version advanced to `0.17.2`.

## [0.17.1] - 2026-02-17

### Changed
- Added `pyshacl` installation to CI and publish validation workflows so Turtle SHACL conformance tests run reliably in GitHub Actions.
- Bumped `prophet-lib` runtime packages to `0.2.7` and refreshed runtime version references.
- Toolchain/package version advanced to `0.17.1`.

## [0.17.0] - 2026-02-16

### Added
- Added a modular Turtle target implementation under `prophet_cli/targets/turtle/` and wired it as an optional cross-stack generation target.
- Added Turtle-target conformance coverage with deterministic projection tests plus enforced `pyshacl` validation against `prophet.ttl`.
- Added a minimal initialized Turtle sample project at `examples/turtle/prophet_example_turtle_minimal`.

### Changed
- Aligned generated Turtle output to the base Prophet ontology vocabulary (`prophet:` / `std:`) with ontology-derived local prefixes.
- Reworked Turtle custom type constraints to emit SHACL `NodeShape` resources (`prophet:hasConstraint`) instead of JSON-encoded constraint blobs.
- Updated reference/quickstart/developer/agent/contributor documentation surfaces for Turtle target behavior, validation commands, and release maintenance expectations.
- Toolchain/package version advanced to `0.17.0`.

## [0.16.0] - 2026-02-16

### Changed
- Updated `prophet-lib` JavaScript runtime publishing to use npm trusted publishing (OIDC) instead of token-based auth.
- Updated runtime publish workflow JavaScript release environment to Node `24` for npm trusted publishing compatibility.
- Updated maintainer publishing docs/runbooks to remove `NPM_TOKEN` requirements and document npm trusted publisher setup for `@prophet-ontology/events-runtime`.
- Toolchain/package version advanced to `0.16.0`.

## [0.15.0] - 2026-02-16

### Added
- Added branded standalone READMEs for published packages with Prophet logo banners and links back to the main repository:
  - `prophet-cli/README.md`,
  - `prophet-lib/README.md`,
  - `prophet-lib/javascript/README.md`,
  - `prophet-lib/python/README.md`,
  - `prophet-lib/java/README.md`.
- Added package-level runtime usage guides for:
  - JavaScript runtime package (`@prophet-ontology/events-runtime`),
  - Java runtime package (`io.prophet:prophet-events-runtime`).

### Changed
- Renamed Node runtime package scope from `@prophet/events-runtime` to `@prophet-ontology/events-runtime` across:
  - Node generator sources,
  - generated manifests/artifacts for Node examples,
  - runtime/developer/reference documentation.
- Updated `prophet-lib` Python publish workflow to use OIDC trusted publishing for both TestPyPI and PyPI.
- Updated publishing runbooks/setup docs to remove Python API-token requirements and document trusted publisher configuration.
- Toolchain/package version advanced to `0.15.0`.

## [0.14.0] - 2026-02-16

### Added
- Added `prophet-lib/` shared runtime packages for generated event publishing:
  - JavaScript: `@prophet-ontology/events-runtime`,
  - Python: `prophet-events-runtime`,
  - Java: `io.prophet:prophet-events-runtime`.
- Added dedicated runtime publishing setup/runbooks:
  - `docs/developer/publishing-setup.md`,
  - `docs/developer/prophet-lib-release.md`.
- Added staged runtime publish workflow:
  - `.github/workflows/publish-prophet-lib.yml`.

### Changed
- Migrated Node, Python, and Java generation from legacy emitter contracts to async-first `EventPublisher` contracts and event wire envelopes.
- Updated generated action flows to support action-output shorthand and `ActionOutcome` with additional domain events.
- Updated examples and generated artifacts across Java/Node/Python to use runtime event publisher wiring.
- Extended CI to validate `prophet-lib` runtimes and to wire runtime dependencies in example validation jobs.
- Removed `Generated`-prefixed Java codegen concept names for publisher/config classes, relying on generated markers/annotations instead:
  - `GeneratedEventPublisherNoOp` -> `EventPublisherNoOp`,
  - `GeneratedPersistenceConfig` -> `PersistenceConfig`.
- Updated root/quickstart/reference/developer docs and contributor guides for `EventPublisher` terminology and runtime wiring paths.
- Toolchain/package version advanced to `0.14.0`.

## [0.13.0] - 2026-02-15

### Changed
- Refactored stack-neutral rendering utilities into `prophet_cli/codegen/rendering.py` and removed Java-target concerns from shared rendering.
- Introduced Java-wide shared rendering support in `prophet_cli/targets/java_common/render/support.py`.
- Reorganized Spring Java rendering into explicit modules:
  - orchestration in `prophet_cli/targets/java_spring_jpa/render/spring.py`,
  - stack-common Java artifacts in `prophet_cli/targets/java_spring_jpa/render/common/`,
  - JPA/ORM-specific artifacts in `prophet_cli/targets/java_spring_jpa/render/orm/`.
- Simplified Java generator dependency wiring to resolve renderer functions directly from Java target modules.
- Updated developer architecture docs with Python layout coverage and the revised Java renderer/module structure.
- Toolchain/package version advanced to `0.13.0`.

## [0.12.1] - 2026-02-15

### Changed
- Expanded the maintainer release skill allowed toolset to include repository-wide validation via `scripts/test-all.sh` and common read-only `git` inspection commands.
- Updated the maintainer release workflow to explicitly review commits since the previous release tag and derive changelog/release notes from that full range.
- Toolchain/package version advanced to `0.12.1`.

## [0.12.0] - 2026-02-15

### Changed
- Standardized Node/Python generated-file headers to industry-standard markers:
  - `// Code generated by prophet-cli. DO NOT EDIT.`
  - `# Code generated by prophet-cli. DO NOT EDIT.`
- Removed explicit `Generated*` prefixes from generated Node/Python runtime surfaces (types, classes, and helpers), relying on file-level generated markers instead.
- Updated Node/Python examples, docs, and target tests to match renamed generated symbols and marker format.
- Toolchain/package version advanced to `0.12.0`.

## [0.11.2] - 2026-02-15

### Changed
- Updated top-level README supported stack documentation to a single table including stack IDs and example links.
- Refreshed tracked example generated artifacts/manifests/IR snapshots to align with current release toolchain outputs.
- Toolchain/package version advanced to `0.11.2`.

## [0.11.1] - 2026-02-15

### Added
- Added execution-focused Prophet agent plugin suites:
  - `plugins/prophet-user-operator` with ontology change, integration update, and repair-loop skills.
  - `plugins/prophet-maintainer` with maintainer release workflow skill.
- Added `.agents/skills` symlink to maintainer skill set for local agent discovery.

### Changed
- Updated top-level README content for improved ontology and Prophet positioning.
- Toolchain/package version advanced to `0.11.1`.

## [0.11.0] - 2026-02-15

### Added
- Added Python example HTTP flow test suites for:
  - FastAPI + SQLAlchemy,
  - FastAPI + SQLModel,
  - Flask + SQLAlchemy,
  - Flask + SQLModel,
  - Django + Django ORM.
- Added Node example Mocha + Supertest HTTP flow suites for:
  - Express + Prisma,
  - Express + TypeORM,
  - Express + Mongoose.
- Added repository-wide `scripts/test-all.sh` orchestrator for CLI + Java + Node + Python validation.
- Added user quickstart pages split by ecosystem:
  - `docs/quickstart/java.md`,
  - `docs/quickstart/node.md`,
  - `docs/quickstart/python.md`.
- Added dedicated runnable examples reference at `docs/reference/examples.md`.

### Changed
- Hardened CI workflows for Python/Node example validation and PyPI release checks.
- Updated Python generated runtime rendering to align framework adapters and typed test coverage expectations.
- Updated top-level and contributor documentation (`README`, `AGENTS.md`, `CONTRIBUTING.md`, developer/reference docs) to reflect:
  - user-facing onboarding vs reference split,
  - pytest + framework test clients for Python examples,
  - Mocha + Supertest for Node examples.
- Toolchain/package version advanced to `0.11.0`.

## [0.10.0] - 2026-02-15

### Changed
- Refactored Node/Express generation into a modular renderer architecture:
  - shared support helpers under `targets/node_express/render/support.py`,
  - stack-agnostic renderers under `targets/node_express/render/common/`,
  - ORM-specific renderers under `targets/node_express/render/orm/{prisma,typeorm,mongoose}.py`.
- Reduced `targets/node_express/generator.py` to orchestration responsibilities (stack gating, target selection, manifest assembly).
- Updated developer architecture documentation to describe the new Node renderer layout.
- Toolchain/package version advanced to `0.10.0`.

## [0.9.0] - 2026-02-15

### Added
- Implemented Node Express + Mongoose stack (`node_express_mongoose`) with:
  - generated Mongoose models,
  - generated Mongoose repository adapters,
  - stack matrix/manifest registration and test coverage.
- Added a complete runnable example at `examples/node/prophet_example_express_mongoose` with generated integration wiring and concrete action handlers.
- Expanded CI Node matrix to validate Express + Mongoose generation/build/clean checks.

### Changed
- Node stack autodetection now includes Mongoose signals and explicit ambiguous-ORM diagnostics across Prisma/TypeORM/Mongoose.
- Node docs/quickstart/developer guides updated to cover Mongoose targets, stack ids, and validation flow.
- Top-level README updated to list the Express + Mongoose example.

### Fixed
- Mongoose code generation type emission now qualifies object-ref and struct document field types against generated domain types (`Domain.*`) so generated TypeScript compiles cleanly.
- Toolchain/package version advanced to `0.9.0`.

## [0.8.4] - 2026-02-15

### Changed
- CI/publish Node example dependency installs now use `npm ci` instead of `npm install` to keep lockfiles immutable in validation jobs.
- Toolchain/package version advanced to `0.8.4`.

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
