# Node/Express Generator Roadmap (Prisma + TypeORM)

## Purpose

Define a contributor-ready roadmap for adding first-class Node.js generation targets for:

- Express + Prisma
- Express + TypeORM

This document is the implementation contract for open source contributors.

## Current Status

Implemented in current tree:
- Shared Node/Express generation surface (contracts, validation, routes, events)
- Prisma repository generation (list/query/getById/save), schema generation, composite key handling
- TypeORM entity + repository generation with query translation parity surface
- Node autodetect with fail-closed ambiguity handling and diagnostics report
- Node example projects + CI validation coverage

## Product Goal

A TypeScript developer should be able to:

1. Write ontology/business contracts in Prophet DSL.
2. Run `prophet gen`.
3. Start an Express app with generated routes, validation, typed contracts, persistence wiring, and extension hooks.
4. Implement only user-owned business handlers.
5. Regenerate safely without losing custom code.

## Scope

In scope:

- Node 20+, TypeScript-only generation
- Express integration
- Prisma adapter
- TypeORM adapter
- Generated OpenAPI
- Generated event emitter interfaces and default NoOp implementation
- Typed action + query/filter contracts
- Autodetection and safe auto-wiring

Out of scope (for this roadmap):

- Backward compatibility with older Prophet versions
- Tool-version migration layers, migration shims, and upgrade helpers
- Plugin loading architecture
- Multi-framework Node targets beyond Express
- Runtime leasing/event-ingest platform concerns
- Advanced migration orchestration

## Compatibility Stance

Prophet is currently pre-adoption for this target stream. For this roadmap:

1. We explicitly do **not** preserve behavior for previous tool versions.
2. We may introduce breaking changes at any layer (DSL handling, IR mapping, generation layout, CLI internals) when it improves target quality.
3. We do **not** build version migration codepaths, compatibility shims, or legacy fallback behavior for old generator outputs.

## Non-Negotiable Requirements

1. **Autodetection is mandatory** for Node project shape, ORM choice, and key integration files.
2. **Deterministic generation** with stable outputs for identical inputs.
3. **Regeneration safety**: generated/user-owned boundaries must prevent overwrites of user logic.
4. **Type fidelity** across DSL, runtime validation, OpenAPI, and ORM layers.
5. **Cross-ORM behavior parity** for supported features.

## Target Developer Experience

## Initial Setup

1. `prophet init`
2. `prophet gen`
3. Add generated router mounting line in app bootstrap only if not auto-wired.
4. Implement action handlers in generated extension points.

## Ongoing Iteration

1. Update ontology DSL.
2. Run `prophet gen`.
3. Validate with `prophet check`.
4. Run project tests.

## Design Principles

1. TS-first, ESM-first defaults.
2. Shared Node core generator for contracts/http/validation/events.
3. Thin ORM adapters behind common repository/query interfaces.
4. Fail-closed on ambiguous autodetection.
5. No hidden destructive edits to host project files.

## Architecture Plan

## Shared Node Core

Generate:

- `generated/contracts/*` action input/output and event payload types
- `generated/domain/*` object/struct/ref/state models
- `generated/validation/*` runtime schemas (single source for request validation + OpenAPI)
- `generated/http/*` Express routers/controllers
- `generated/actions/*` handler interfaces + default unsupported implementations
- `generated/events/*` emitter interface + noop implementation
- `generated/query/*` typed query/filter contracts and parser helpers
- `generated/manifest/*` managed files + extension hooks metadata

## ORM Adapter Layer

Prisma adapter:

- `prisma/schema.prisma` generation
- relation and key mapping
- generated repository/query adapters targeting Prisma client

TypeORM adapter:

- entity generation with decorators
- relation and key mapping
- generated repository/query adapters using QueryBuilder

## Delivery Roadmap

## Milestone 0: Foundation and Contracts

Goals:

- Lock shared Node target contracts.
- Define generation boundaries and managed file policy.

Deliverables:

- Node target entry in stack matrix and capability map.
- Node generator interfaces and target registry stubs.
- Initial contributor guide for Node target architecture.

Acceptance criteria:

- Deterministic snapshot tests for empty/minimal target output.
- `prophet stacks` includes planned Node target metadata.

## Milestone 1: Express Core (No ORM)

Goals:

- Deliver runnable Express generation without DB adapters.

Deliverables:

- Generated action routes and handler interfaces.
- Generated request validation and response typing.
- Generated OpenAPI from shared schemas.
- Event emitter interface and default noop implementation.

Acceptance criteria:

- Generated Express app compiles and starts.
- Action endpoints execute through user-owned handlers.
- OpenAPI and runtime validation remain aligned in tests.

## Milestone 2: Prisma Adapter

Goals:

- Add production-grade Prisma persistence integration.

Deliverables:

- Generated `schema.prisma` from ontology objects/refs/keys.
- Prisma repository adapters for generated contracts.
- Typed query/filter translation to Prisma `where`.
- Composite key support in generated query and repository paths.

Acceptance criteria:

- End-to-end tests pass on SQLite and PostgreSQL.
- Composite keys and refs behave as specified.
- Query/filter contract behavior matches generated OpenAPI and runtime.

## Milestone 3: TypeORM Adapter

Goals:

- Add TypeORM integration with parity to Prisma feature set.

Deliverables:

- Generated entities, relations, and repository adapters.
- QueryBuilder translation for typed filter DSL.
- Equivalent action/query endpoint behavior vs Prisma target.

Acceptance criteria:

- Parity suite passing against both ORM targets.
- No unsupported behavior silently accepted in one ORM and rejected in the other.

## Milestone 4: Autodetection and Auto-Wiring Hardening

Goals:

- Make setup seamless and safe in real Node repos.

Deliverables:

- Detection engine for:
  - package manager (`npm`, `pnpm`, `yarn`, `bun`)
  - module mode (ESM/CJS)
  - TS config and rootDir/outDir
  - Express entrypoints
  - ORM presence/config/version
  - monorepo workspace boundaries
- Deterministic precedence rules:
  - CLI flag > `prophet.yaml` > autodetect
- Idempotent host project edits for scripts/wiring when confidence is high.
- Structured diagnostics for ambiguous detection.

Acceptance criteria:

- Re-running generation produces zero additional host-file churn.
- Ambiguous projects fail with actionable diagnostics.
- Detection report available in machine-readable form for CI and tooling.

## Milestone 5: OSS Readiness and Release Quality

Goals:

- Ensure contributors and adopters can use/extend the target safely.

Deliverables:

- User quickstart for Node+Express targets.
- Reference docs for generated surfaces and extension points.
- Troubleshooting for common Node ecosystem pitfalls.
- CI matrix with Node version and ORM profile coverage.

Acceptance criteria:

- New contributor can implement a scoped roadmap task from docs alone.
- Release checklist includes Node-specific quality gates.

## Detailed Requirements

## Autodetection Requirements (Must)

1. Detect and validate host project root correctly in monorepos.
2. Detect TypeScript compiler config and resolve path aliases used by generated code.
3. Detect Express bootstrap candidates and avoid unsafe edits when multiple exist.
4. Detect installed ORM and reject conflicting dual-ORM setup unless explicitly configured.
5. Detect DB provider from configuration/env where possible.
6. Emit explicit confidence and rationale per detection decision.
7. Provide remediation hints when detection fails or is ambiguous.

## Regeneration Safety Requirements

1. Generated files are clearly marked and listed in manifest.
2. User-owned extension files are never overwritten.
3. Stale generated files are removed only when covered by manifest policy.
4. Auto-wiring edits are reversible and idempotent.

## Type and Contract Fidelity Requirements

1. `decimal`, `bigint`, temporal types, lists, nested lists, structs, refs retain semantics end-to-end.
2. Nullability semantics are consistent across:
  - DSL required/optional
  - runtime validation
  - TS types
  - OpenAPI required arrays
  - ORM nullability
3. Composite keys are fully supported in API paths, repositories, and persistence mapping.

## Query/Filter Requirements

1. Typed query endpoints are canonical for filtering.
2. Supported operators must be explicitly documented and parity-tested across ORMs.
3. Generated operator behavior must be deterministic and stable for compatibility checks.

## Compatibility and Versioning Requirements

1. IR compatibility checks continue to classify breaking/additive/non-functional changes.
2. Node target generation changes must include compatibility notes in release docs.
3. Field order-only changes must remain non-functional in compatibility classification.
4. No roadmap deliverable should include support for older tool-version output migration.

## Testing Strategy Requirements

Test categories required per milestone:

1. Unit tests for parser/IR/target mapping logic.
2. Snapshot tests for deterministic generated outputs.
3. Integration tests for CLI flow (`init`, `gen`, `check`).
4. End-to-end HTTP tests for action and query flows.
5. Cross-ORM parity tests for shared contract behavior.
6. Regeneration safety tests for user-owned extension files.

## Contributor Workstreams

## Workstream A: Shared Node Core

Tasks:

- Generator scaffolding and target registry integration.
- Type contracts, validation schemas, Express routers, OpenAPI exporter.

Definition of done:

- Express core app boots and passes contract tests without ORM dependency.

## Workstream B: Prisma Adapter

Tasks:

- Prisma schema generator and mapping logic.
- Repository/query adapter generation.

Definition of done:

- End-to-end actions and query flow pass on Prisma profile.

## Workstream C: TypeORM Adapter

Tasks:

- Entity generator and relation/key mapping.
- QueryBuilder adapter generation.

Definition of done:

- Parity test suite vs Prisma passes.

## Workstream D: Autodetection Engine

Tasks:

- Detection graph, confidence scoring, diagnostics.
- Idempotent auto-wiring integration.

Definition of done:

- Ambiguity and conflict cases produce deterministic actionable errors.

## Workstream E: Docs and DX

Tasks:

- User quickstart, reference pages, troubleshooting updates.
- Example projects and migration guides.

Definition of done:

- New users can complete first run without maintainer intervention.

## Suggested Issue Labels

- `target:node`
- `target:express`
- `target:prisma`
- `target:typeorm`
- `area:autodetect`
- `area:contracts`
- `area:query`
- `area:docs`
- `good-first-issue`
- `help-wanted`

## Risk Register

1. ORM behavior divergence on composite keys and relation loading.
2. Ambiguous host project structure causing unsafe wiring edits.
3. Type drift between runtime validation and OpenAPI.
4. Non-deterministic output ordering in generated artifacts.
5. Ecosystem version churn (Express/TypeScript/ORM major updates).

Mitigations:

1. Cross-ORM parity suite.
2. Fail-closed autodetection with explicit overrides.
3. Shared schema source for validation and OpenAPI.
4. Snapshot + deterministic sort enforcement.
5. Version matrix CI and documented supported ranges.

## Completion Criteria

Roadmap is complete when:

1. Express + Prisma and Express + TypeORM are both implemented and parity-tested.
2. Autodetection and safe auto-wiring are reliable in mono- and poly-repo setups.
3. Contributor and user docs are complete and self-serve.
4. Release process includes Node target quality gates.
