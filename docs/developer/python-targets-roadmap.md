# Python Targets Roadmap

This roadmap defines how to add Python generation targets to Prophet with a modular architecture that can scale across frameworks and ORMs.

This document is intentionally implementation-oriented so open source contributors can pick a workstream and ship independently.

## Context

Target stacks:

- `python_django_django_orm`
- `python_flask_sqlalchemy`
- `python_flask_sqlmodel`
- `python_fastapi_sqlalchemy`
- `python_fastapi_sqlmodel`

Design intent:

- Use one shared Python domain/action/query/event contract surface.
- Compose framework renderers with ORM renderers.
- Keep stack-specific behavior isolated to dedicated modules.
- Preserve deterministic generation and managed-file ownership.

Backward compatibility policy for this roadmap:

- We do not optimize for compatibility with old Prophet tool versions.
- We may break internal generator structure if it yields a cleaner long-term architecture.
- We still require deterministic output and passing test gates.

## Goals

- Add first-class Python stack entries to stack manifest and generator registry.
- Implement modular Python codegen architecture using framework and ORM composition.
- Generate runnable examples for each Python stack.
- Add CI validation for Python examples.
- Ship reference documentation for Python targets.
- Maintain product-level feature parity with existing Java and Node generated experiences.

## Non-Goals

- Plugin loading system.
- Full migration engines for Python stacks.
- Runtime orchestration concerns outside generated app integration boundaries.

## Architectural Requirements

## 1. Composition Model

Generation must be split into:

- Common renderers: framework and ORM agnostic files.
- Framework renderers: HTTP/web wiring and framework lifecycle integration.
- ORM renderers: persistence models, repository adapters, and query translation.
- Orchestrator: target selection, stack gating, manifest assembly, post-processing.

## 2. Module Layout

Recommended structure:

- `prophet_cli/targets/python/generator.py`
- `prophet_cli/targets/python/render/support.py`
- `prophet_cli/targets/python/render/common/*`
- `prophet_cli/targets/python/render/framework/django.py`
- `prophet_cli/targets/python/render/framework/flask.py`
- `prophet_cli/targets/python/render/framework/fastapi.py`
- `prophet_cli/targets/python/render/orm/django_orm.py`
- `prophet_cli/targets/python/render/orm/sqlalchemy.py`
- `prophet_cli/targets/python/render/orm/sqlmodel.py`

## 3. Contract Stability

Common-generated interfaces must stay stable across Python stacks:

- domain model contracts
- action input/output contracts
- event contracts and event emitter interface
- query filter contracts
- repository interface contracts

Framework and ORM modules must consume those common contracts, not redefine them.

## 4. Capability Separation

Framework responsibilities:

- route registration
- request/response validation hooks
- handler injection/wiring
- error mapping conventions

ORM responsibilities:

- object model persistence definitions
- query operator translation
- get/list/query/save repository operations
- object-ref and key handling

Orchestrator responsibilities:

- stack/target routing
- output tree assembly
- generated-file manifest and extension hooks
- deterministic ordering and content post-processing

## Milestones

## Milestone 0: Foundations

Deliverables:

- stack manifest entries for all Python target stacks (`planned` or `implemented` as work progresses)
- Python target orchestrator scaffold
- Python render package scaffold (`common`, `framework`, `orm`, `support`)
- baseline tests proving registry and stack resolution behavior

Acceptance criteria:

- `stacks` CLI output includes new Python stacks with correct tuple metadata
- generator registry tests pass

## Milestone 1: Common Python Contracts

Deliverables:

- common renderers for domain/actions/event-contracts/events/query/persistence/action-handlers/action-service
- shared naming/type mapping utilities in `render/support.py`
- deterministic output tests for common artifacts

Acceptance criteria:

- common artifact snapshots are deterministic
- no framework or ORM imports in common contracts

## Milestone 2: SQLAlchemy ORM Renderer

Deliverables:

- ORM renderer for SQLAlchemy persistence models and repository adapters
- typed query translation from generated filter contracts to SQLAlchemy query expressions
- support for object refs, composite keys, state field, pagination, and filter ops

Acceptance criteria:

- generated ORM artifacts compile/import in both Flask and FastAPI example apps
- repository contract tests pass against SQLAlchemy-generated adapters

## Milestone 3: Flask + SQLAlchemy Stack

Deliverables:

- Flask framework renderer (action routes, query routes, wiring helpers)
- stack config + examples:
  - `examples/python/prophet_example_flask_sqlalchemy`
- docs for setup/run/validation

Acceptance criteria:

- example app boots and actions/query endpoints function
- CI job validates generation + tests/import checks

## Milestone 4: FastAPI + SQLAlchemy Stack

Deliverables:

- FastAPI framework renderer that reuses SQLAlchemy ORM renderer
- stack config + example:
  - `examples/python/prophet_example_fastapi_sqlalchemy`
- docs updates

Acceptance criteria:

- example app boots with generated routes and typed contracts
- CI coverage added

## Milestone 5: SQLModel ORM Renderer

Deliverables:

- SQLModel ORM renderer for persistence models and repository adapters
- support both Flask and FastAPI SQLModel stacks:
  - `python_flask_sqlmodel`
  - `python_fastapi_sqlmodel`
- two runnable examples

Acceptance criteria:

- SQLModel examples generate and run
- query and persistence semantics match common repository contracts

## Milestone 6: Django + Django ORM Stack

Deliverables:

- Django framework renderer
- Django ORM renderer
- stack config + example:
  - `examples/python/prophet_example_django`

Acceptance criteria:

- generated Django app wiring functions with action/query endpoints
- repository contract parity with other Python stacks

## Milestone 7: Autodetect + Docs + CI Hardening

Deliverables:

- Python stack autodetection strategy for framework/ORM signals
- fail-closed diagnostics for ambiguous detection
- reference docs:
  - `docs/reference/python-*.md` (or equivalent split)
- CI matrix entries for each implemented Python stack

Acceptance criteria:

- clear autodetect diagnostics
- end-to-end CI checks for all implemented Python stacks

## Cross-Cutting Engineering Rules

- Determinism: outputs must be stable for identical IR/config.
- Generated file ownership: all Python target outputs tracked in manifest.
- No user file clobbering: generation cannot overwrite user-owned extension implementations.
- Error quality: invalid config, ambiguous stack, and unsupported features must provide actionable diagnostics.
- Test-first for shared contracts and stack registry behavior.

## Strong Emphasis (Non-Negotiables)

- Contract-first implementation:
  - common contracts are the source of truth; framework/ORM renderers must conform to them.
- Parity over framework preference:
  - users should get equivalent value regardless of Java, Node, or Python target.
  - framework idioms are respected, but capability gaps must be explicit and temporary.
- Small, composable modules:
  - no monolithic renderer files; shared logic goes into support/common modules.
  - avoid duplicating query/type/key logic in multiple stacks.
- Deterministic + reviewable outputs:
  - generated artifacts must remain stable and diff-friendly for PR review.
- Clear ownership boundaries:
  - generated code handles inferred wiring, not app-specific business logic.
  - host apps own runtime concerns (auth, policy, deployment, infra config).
- CI-backed examples as product surface:
  - every implemented stack must have a runnable example validated in CI.
  - examples are not optional docs; they are compatibility tests.

## Key Design Decisions To Lock Early

Decisions for this roadmap:

- sync/async is framework-dependent (not globally enforced):
  - Django and Flask stacks are sync-first.
  - FastAPI stacks are async-first and generated interfaces should be `async` where framework flow expects it.
- contract semantics must remain stack-equivalent:
  - action input/output, query filters, event contracts, and repository semantics are equivalent across sync and async stacks.
- Python targets must deliver feature parity with Java/Node capabilities that are already in-product:
  - action endpoints
  - query/list/get-by-id endpoints
  - typed filters with operator support
  - generated event emitter interfaces + noop
  - object refs/composite keys/state handling
  - extension hooks and generated-file manifests
- Python package layout should follow ontology-scoped namespacing to support multi-ontology generation safely.

## Additional Concerns To Decide Early

- Python support matrix:
  - define supported runtime versions (for example 3.10/3.11/3.12) and CI coverage policy.
- Dependency baselines:
  - pin major lines for core libraries (Django, Flask, FastAPI, SQLAlchemy, SQLModel, Pydantic).
- Sync/async contract shape:
  - common semantic contract is shared, but generated method signatures follow framework mode (sync for Django/Flask, async for FastAPI).
- Validation engine policy:
  - choose canonical validation model surface for generated contracts to avoid framework drift.
- Packaging and import layout:
  - define generated package structure, namespace conventions, and collision policy for multi-ontology generation.
- Session/connection lifecycle:
  - document how generated code obtains database sessions/connections from host apps.
- Observability hooks:
  - define minimal structured logging/error hook extension points generated by default.
- Security baseline:
  - clarify what generated APIs do not include by default (authn/authz/rate limiting) and how users integrate them.

## Risk Register

- Async/sync mismatch can leak complexity into common contracts.
- SQLAlchemy vs SQLModel feature parity can diverge query behavior.
- Django conventions can resist direct parity with Flask/FastAPI route patterns.
- Composite keys and object refs can become inconsistent without strict contract tests.
- Example project drift can hide generation regressions unless CI gates run all examples.

## Parity Gate (Java/Node -> Python)

Each Python stack milestone must include a parity checklist against existing Java/Node behavior.

Minimum parity checklist:

- generated domain/action/event/query contract coverage
- generated persistence adapter contract coverage
- generated action endpoints and query endpoints
- typed filter behavior parity (operator semantics)
- state + transition/event semantics parity
- manifest + extension hook generation parity

Any intentional gap must be documented explicitly in release notes and roadmap status.

## Test Plan

## Unit Tests

- naming/type mapping helpers
- ORM query-operator translation
- stack resolution and generator routing
- deterministic output hashing

## Contract Tests

- repository interface contract compliance for each ORM renderer
- action/service contract parity across frameworks

## Snapshot Tests

- generated outputs for each stack
- no-op generation determinism

## Example Validation

Each implemented stack example should verify:

- `prophet gen`
- framework-specific build/import checks
- basic endpoint smoke behavior (action + query)

## CI Plan

Add Python examples to CI matrix as each stack is implemented:

- generate artifacts
- install runtime dependencies
- run compile/import tests
- run example-level checks
- verify clean generated outputs

## Contributor Workstreams

Parallelizable workstreams:

- Stack manifest and registry updates
- Common Python renderer package
- SQLAlchemy ORM renderer
- SQLModel ORM renderer
- Flask framework renderer
- FastAPI framework renderer
- Django framework + ORM renderer
- Autodetect and diagnostics
- Documentation and examples

Each PR should:

- scope to one workstream or one milestone slice
- include tests
- update docs for user-visible behavior changes

## Definition of Done

A Python stack is considered done when:

- stack manifest entry is `implemented`
- generator outputs are deterministic
- stack tests and example CI checks pass
- reference docs and troubleshooting guidance exist
- generated outputs are manifest-owned and verify-clean passes
