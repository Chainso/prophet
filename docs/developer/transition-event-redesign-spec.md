# Transition/Event Redesign Implementation Spec

## 1. Purpose

This document defines a **hard-cut redesign** of Prophet action outputs, transitions, and state transition execution.

It is written for implementers with no prior context. It specifies:

- required behavior changes
- required compiler/runtime/codegen changes
- storage model decisions
- milestones and execution order
- success criteria and acceptance gates

There is no backward-compatibility requirement for this change.

## 1.1 Living Document Policy (Mandatory)

This file is a living implementation plan and must be updated continuously.

Required updates after every deliverable/milestone increment:

1. Update this file with:
- status (`not_started`, `in_progress`, `completed`, `blocked`)
- date updated
- what changed
- any deviations from spec
- follow-up work
2. Update all affected project documentation before commit, including at minimum:
- `AGENTS.md`
- `README.md`
- `CONTRIBUTING.md`
- `docs/reference/*` (relevant pages)
- `docs/quickstart/*` (relevant pages)
- `docs/developer/*` (relevant pages)
3. Do not commit a deliverable until both code and docs are synchronized.

## 1.2 Documentation Update Gate (Mandatory Before Commit)

A deliverable is not complete until:

1. The implementation behavior is present in code/tests.
2. The living status in this spec is updated.
3. User-facing and contributor-facing docs are updated to match behavior.
4. Example snippets and generated-output references in docs are regenerated if affected.

## 2. Problem Statement

Current Prophet behavior has a modeling mismatch:

- `Transition` is already an event-like concept in the metamodel.
- `ActionOutput` is a separate event category and action outputs are treated specially.
- Transition handling is not fully first-class across generated stacks.

We need a single coherent event model where action outputs are events (`Signal` or `Transition`) and transition execution is generated as a first-class service/handler pattern.

## 3. Goals

1. Remove `ActionOutput` from the metamodel and toolchain.
2. Make action outputs reference an `Event` directly.
3. Support new DSL output forms:
- `output { ... }` (inline, derives a signal event)
- `output signal <SignalName>`
- `output transition <ObjectName>.<TransitionName>`
4. Make transition events richer and easier to use:
- automatically include object primary key fields
- automatically include `fromState` and `toState`
5. Generate per-object transition handlers with default implementations that:
- validate current state against transition `from`
- run transition validator hooks
- persist new state
- persist transition history
- return a transition event **Draft**
6. Represent object lifecycle state as generated domain field `state`.
7. Reserve user field name `state` globally (cannot be user-defined).
8. Preserve deterministic generation behavior.
9. Generate transition validator extension points with shared validation result contract.

## 4. Non-Goals

1. No migration support for legacy DSL/output semantics.
2. No compatibility shim for old IR shape.
3. No partial opt-in flags; this is a hard behavior switch.

## 5. Target Terminology

1. **Event**: one of `Signal` or `Transition`.
2. **Action produced event**: the event an action publishes as its primary output.
3. **Transition Draft**: a not-yet-final transition payload object returned by transition handlers; contains implicit fields and supports adding optional transition fields before final build.
4. **Object state field**: generated logical field name `state` on stateful domain objects.
5. **Internal storage state key**: `__prophet_state` in persistence layers (not a user-facing field).

## 6. Functional Requirements

### 6.1 Metamodel Changes (`prophet.ttl`)

1. Remove `prophet:ActionOutput` class and all references.
2. Replace action relation:
- remove `prophet:producesOutput`
- add `prophet:producesEvent` with range `prophet:Event`
3. Update event partition:
- `prophet:Event` is exactly one of `prophet:Signal` or `prophet:Transition`
4. Keep `prophet:Transition` as:
- subclass of `prophet:Event`
- subclass of `prophet:PropertyContainer`
5. Update all SHACL shapes accordingly:
- abstract event xone list
- action shape output property validation
- closed shapes for affected classes
- any constraints referencing `ActionOutput`

### 6.2 DSL Changes

Action output syntax:

1. Inline signal form:
```prophet
output {
  field ...
}
```
Compiles to a derived signal event named `<ActionName>Result`.

2. Referenced signal form:
```prophet
output signal PaymentCaptured
```

3. Referenced transition form:
```prophet
output transition Order.approve
```

Validation:

1. Exactly one output declaration form is allowed per action.
2. Referenced signal must exist.
3. Referenced transition target must exist (`object + transition`).
4. Legacy action-output-only assumptions are removed.

### 6.3 Transition Event Payload Semantics

Each transition event includes implicit fields:

1. Object primary key fields (required).
2. `fromState` (required).
3. `toState` (required).

Rules:

1. User-defined transition fields must not collide with implicit field names.
2. User-defined transition fields must not collide with implicit PK field names.
3. Implicit fields are always present in generated contracts.

### 6.4 Object State Field Semantics

1. Stateful objects generate a domain-level `state` field.
2. User-defined field name `state` is globally forbidden.
3. Persistence stores state in internal key/column `__prophet_state`.
4. Query/filter APIs expose logical `state` and map internally to `__prophet_state`.

### 6.5 Transition Handler Generation

Generate one transition handler interface per object that has transitions.

Method naming:

1. Use `transitionName + objectName` order (for example `approveOrder`).

Method behavior:

1. Accept object ref-or-object type.
2. Resolve primary key.
3. Load object.
4. Verify current state equals transition `from`.
5. Update state to transition `to`.
6. Persist transition history record.
7. Return transition event `Draft` seeded with implicit fields.

Default implementation behavior:

1. Implement steps above out of the box.
2. Enforce state mismatch errors with explicit message.
3. Ensure atomicity where backend supports transactions.

### 6.6 Transition Validator Extension Points

Generate one transition validator interface per object that has transitions.

Validator interface naming:

1. `<ObjectName>TransitionValidator`

Method naming:

1. `validate<TransitionName><ObjectName>` (for example `validateApproveOrder`).

Method behavior:

1. Accept the fully loaded domain object for validation.
2. Return `TransitionValidationResult`.

Default behavior:

1. Generate a default validator implementation that always passes.
2. Generated transition handlers must invoke validators before state mutation.
3. Failed validation must stop transition execution and expose `failureReason`.

`TransitionValidationResult` contract:

1. Add a new runtime-library class/type named `TransitionValidationResult`.
2. Fields:
- `passesValidation` (boolean)
- `failureReason` (string, optional/nullable; unset when `passesValidation` is true)

### 6.7 Action Codegen Behavior

1. Action codegen remains structurally similar.
2. Replace old action-output type usage with produced event payload type.
3. Action default service must auto-publish the produced event.
4. If produced event is transition:
- action implementation can call transition handler
- receive Draft
- finalize Draft
- return/publish resulting transition event payload

### 6.8 Persistence Model Requirements

#### SQL-based stacks

1. Keep state on object row in `__prophet_state`.
2. Keep history table `<object>_state_history` with:
- object PK columns
- transition id
- from state
- to state
- timestamp
- optional actor metadata if already supported
3. Transition update must be compare-and-set style:
- update only when current `__prophet_state` equals expected `from`

#### Document stacks (Mongoose)

1. Keep state on object document field `__prophet_state`.
2. Add history collection per stateful object (for example `OrderStateHistory`).
3. Transition update uses conditional query on `__prophet_state`.
4. Persist history record after successful state update.

## 7. IR Contract Changes

Required IR shape shifts:

1. Remove `action_outputs` top-level section.
2. Remove event kind `action_output`.
3. Action entries contain `output_event_id`.
4. Event kinds are only `signal` and `transition`.
5. Transition event entries include implicit fields and transition metadata.
6. Object fields include logical `state` for stateful objects.

All generators and compatibility logic must consume the new IR schema.

## 8. Validation Rules

Compiler validation must enforce:

1. Reserved name `state` cannot be declared by users.
2. Reserved prefix `__prophet_` cannot be used by users.
3. Action output references must resolve to existing event definitions.
4. Transition implicit field collisions are compile errors.
5. Transition state references (`from`/`to`) remain required and valid.
6. Transition `from != to`.
7. Deterministic ordering of generated event/transition fields.

## 9. Generated API Expectations by Language

### Java

1. Transition handlers return typed Draft/builder objects.
2. Draft supports fluent field assignment and final `build()`.
3. Existing action handler/service pattern remains, with produced-event type substitution.
4. Generate `<ObjectName>TransitionValidator` interface + default implementation.
5. Transition handlers call validators and fail with reason when validation fails.
6. Include `TransitionValidationResult` in Java runtime library.

### Node/TypeScript

1. Generate typed Draft classes/interfaces for transitions.
2. Draft expresses "incomplete until finalized" semantics.
3. Preserve existing action execution service pattern.
4. Generate `<ObjectName>TransitionValidator` interfaces + default implementations.
5. Include `TransitionValidationResult` in Node runtime contract and generated code.

### Python

1. Generate typed Draft dataclasses/helpers for transitions.
2. Draft has explicit finalize/build method.
3. Preserve existing action execution service pattern.
4. Generate `<ObjectName>TransitionValidator` protocols/interfaces + default implementations.
5. Include `TransitionValidationResult` in Python runtime contract and generated code.

## 10. Milestones

### 10.0 Milestone Status Tracker (Update Each Deliverable)

| Milestone | Status | Last Updated | Owner | Notes |
|---|---|---|---|---|
| 0. Design Freeze | completed | 2026-02-17 | codex | Naming and architecture decisions locked in this spec. |
| 1. Metamodel + DSL + Parser + Core Models | completed | 2026-02-17 | codex | `ActionOutput` removed, `producesEvent` model, new action output DSL forms, reserved `state` validation added. |
| 2. IR + Validation + Compatibility Engine | completed | 2026-02-17 | codex | IR now uses `output_event_id`; event kinds reduced to signal/transition; validation enforces reserved `state` and output event resolution. |
| 3. Event/Action Codegen Refactor | completed | 2026-02-17 | codex | Action codegen now publishes produced events (`signal` or `transition`) and removed legacy action-output code paths. |
| 4. Transition Handler Generation + Persistence Wiring | completed | 2026-02-17 | codex | Per-object transition handlers, draft returns, validator hooks, history writes, and runtime `TransitionValidationResult` integrated across Java/Node/Python. |
| 5. Examples + Docs + Full Validation | in_progress | 2026-02-17 | codex | Examples/docs regenerated and updated; stack verification complete except FastAPI `TestClient` instability under Python 3.14 in this environment. |

### 10.1 Deliverable Log

#### Deliverable 1 (2026-02-17): Core Model + DSL + Metamodel Foundation

Status: completed

Implemented:
1. Removed core `action_outputs` ontology model support.
2. Replaced action output contract pointer with `produces_event`.
3. Added DSL support for:
- `output { ... }` (inline signal)
- `output signal <SignalName>`
- `output transition <Object>.<Transition>`
4. Updated parser materialization and validation to the new event-output model.
5. Added reserved DSL field-name validation for `state`.
6. Updated IR schema/action contract wiring to use `output_event_id`.
7. Transition IR events now include implicit fields:
- object primary-key fields
- `fromState`
- `toState`
8. Updated compatibility/query-contract state filter naming from `currentState`/`__current_state__` to `state`/`__prophet_state`.
9. Updated `prophet.ttl` to remove `ActionOutput` and move action output relation to `producesEvent`.

Known remaining work:
1. Completed in Deliverable 2.

#### Deliverable 2 (2026-02-17): Generator + Runtime Transition Validation Integration

Status: completed

Implemented:
1. Added generated transition runtime surfaces for Java/Node/Python:
- per-object transition handler interfaces
- per-object transition service defaults
- transition draft return types seeded with PK + `fromState` + `toState`
2. Added per-object transition validator interfaces/defaults:
- `<ObjectName>TransitionValidator`
- method shape `validate<TransitionName><ObjectName>(...)`
3. Handler defaults now invoke validators on full loaded objects before state mutation.
4. Added shared `TransitionValidationResult` runtime type in:
- Java runtime (`io.prophet.events.runtime`)
- Python runtime (`prophet_events_runtime`)
- JavaScript runtime (`@prophet-ontology/events-runtime`)
5. Java transition default handlers are generated as `@Component` with `@ConditionalOnMissingBean` directly on the default handler class (no dedicated transition config class).
6. Stateful persistence mappings standardized on internal `__prophet_state` while preserving logical `state` in domain/query contracts.

Known remaining work:
1. Final all-suite execution in one clean environment (current local blocker: FastAPI `TestClient` hangs under Python 3.14).

### Milestone 0: Design Freeze

Deliverables:

1. This document approved.
2. Final naming locked:
- `producesEvent`
- output DSL forms
- `state` logical field
- `__prophet_state` physical key
- Draft terminology

Exit criteria:

1. No unresolved design questions.
2. Living document tracker updated.
3. Documentation update gate completed before commit.

### Milestone 1: Metamodel + DSL + Parser + Core Models

Deliverables:

1. `prophet.ttl` updated (OWL + SHACL).
2. Parser supports new output syntax forms.
3. Core data models updated to remove legacy action-output assumptions.

Exit criteria:

1. Parser tests for all output forms pass.
2. SHACL conformance tests pass with generated turtle.
3. Living document tracker updated.
4. Documentation update gate completed before commit.

### Milestone 2: IR + Validation + Compatibility Engine

Deliverables:

1. New IR schema implemented.
2. Validation rules for reserved names and transition implicit field collisions.
3. Compatibility analyzer updated to new model (even if hard-cut, internal checks must be coherent).

Exit criteria:

1. Core unit tests pass.
2. IR snapshots/examples updated and deterministic.
3. Living document tracker updated.
4. Documentation update gate completed before commit.

### Milestone 3: Event/Action Codegen Refactor

Deliverables:

1. Remove action-output event generation path.
2. Generated action services publish produced event (`Signal` or `Transition`).
3. Event contracts generated from new event model.

Exit criteria:

1. Java/Node/Python generated projects compile/build.
2. Living document tracker updated.
3. Documentation update gate completed before commit.

### Milestone 4: Transition Handler Generation + Persistence Wiring

Deliverables:

1. Per-object transition handler interfaces generated.
2. Default implementations generated across stacks.
3. State compare-and-set logic implemented.
4. Transition history persistence wired.
5. Per-object transition validator interfaces/defaults generated.
6. `TransitionValidationResult` added to runtime libraries and wired into handlers.

Exit criteria:

1. Generated transition handler tests pass for all stacks.
2. Invalid transition attempts fail as expected.
3. Successful transitions produce Draft and final event payload correctly.
4. Validator failures block transitions with clear failure reason.
5. Living document tracker updated.
6. Documentation update gate completed before commit.

### Milestone 5: Examples + Docs + Full Validation

Deliverables:

1. All example ontologies migrated to new DSL.
2. Regenerated outputs committed.
3. User docs and developer docs updated.

Exit criteria:

1. Full suite passes (`./scripts/test-all.sh`).
2. Determinism checks pass.
3. Turtle target SHACL conformance passes.
4. Living document tracker updated.
5. Documentation update gate completed before commit.

## 11. Execution Plan (Step-by-Step)

1. Update metamodel (`prophet.ttl`) first, then lock failing tests.
2. Implement parser/model changes for new output syntax.
3. Refactor IR builder and validation to eliminate action-output branch.
4. Update event contract renderers for all targets.
5. Update action service renderers to consume produced event types.
6. Implement transition Draft contract generation.
7. Implement transition handler interfaces/defaults per target.
8. Implement transition validator interfaces/defaults + `TransitionValidationResult` runtime support per target.
9. Implement persistence updates for `__prophet_state` and history writes.
10. After each deliverable, update this living spec status tracker and notes.
11. After each deliverable, update required docs (`AGENTS.md`, `README.md`, `CONTRIBUTING.md`, and relevant `docs/*`) before commit.
12. Migrate examples and regenerate.
13. Update docs/reference and docs/developer pages.
14. Run all required tests and fix regressions.

## 12. Acceptance Criteria (Success Criteria)

Implementation is complete only when all conditions below are true.

### 12.1 Language/Compiler

1. DSL accepts:
- `output {}`
- `output signal X`
- `output transition Obj.trans`
2. Legacy action-output assumptions removed from parser/IR.
3. Compiler rejects user field `state`.

### 12.2 Metamodel/SHACL

1. `ActionOutput` is absent from metamodel.
2. `Action` points to `Event` via `producesEvent`.
3. Event partition is exactly signal/transition.
4. Generated turtle conforms to updated SHACL.

### 12.3 Generated Contracts

1. Transition events include implicit PK + `fromState` + `toState`.
2. Transition handler defaults return Draft objects.
3. Action generated output typing uses produced event payload type.

### 12.4 Persistence/Runtime

1. Stateful objects persist lifecycle state under internal key `__prophet_state`.
2. Logical domain/API field is `state`.
3. Transition compare-and-set state check is enforced.
4. Transition history persistence exists in all supported storage targets.

### 12.5 End-to-End Behavior

1. Action that outputs signal publishes signal event.
2. Action that outputs transition can invoke transition handler, finalize Draft, and publish transition event.
3. Manual transition invocation outside action flow is supported via generated transition handlers.

### 12.6 Quality Gates

1. Unit tests pass.
2. Example integration tests pass.
3. Deterministic generation checks pass.
4. SHACL validation tests pass.
5. Living document status/notes updated for the completed deliverable.
6. Documentation update gate satisfied before commit.

## 13. Test Plan

Required test additions/updates:

1. DSL parsing tests:
- all new output forms
- invalid references
- reserved field name checks
2. IR tests:
- no `action_output` kind
- action `output_event_id` wiring
- transition implicit fields materialization
3. Codegen tests:
- event contracts per target
- action services with new output event flow
- transition Draft API generation
4. Persistence tests:
- valid transition state change and history append
- invalid transition state mismatch
5. Example stack integration tests:
- Java spring
- Node prisma/typeorm/mongoose
- Python sqlalchemy/sqlmodel/django

## 14. File/Module Impact Map

Likely primary edit zones:

1. `prophet.ttl`
2. `prophet-cli/src/prophet_cli/core/models.py`
3. `prophet-cli/src/prophet_cli/core/parser.py`
4. `prophet-cli/src/prophet_cli/core/validation.py`
5. `prophet-cli/src/prophet_cli/core/ir.py`
6. `prophet-cli/src/prophet_cli/core/compatibility.py`
7. `prophet-cli/src/prophet_cli/codegen/rendering.py`
8. `prophet-cli/src/prophet_cli/targets/java_spring_jpa/...`
9. `prophet-cli/src/prophet_cli/targets/node_express/...`
10. `prophet-cli/src/prophet_cli/targets/python/...`
11. `docs/reference/*.md` (DSL, concepts, compatibility, target refs)
12. examples under `examples/*/prophet_example_*`

## 15. Risks and Mitigations

1. Risk: broad refactor touches many generators.
- Mitigation: milestone-gated implementation and per-target smoke tests.

2. Risk: state field naming conflicts in persistence.
- Mitigation: strict reserved naming and explicit internal field mapping.

3. Risk: inconsistent Draft semantics across languages.
- Mitigation: define Draft contract behavior first, then map idiomatically per language.

4. Risk: hidden action-output assumptions in codegen paths.
- Mitigation: search-and-eliminate all `action_output` branches before finalizing.

## 16. Done Definition

This redesign is done when:

1. The codebase no longer models `ActionOutput`.
2. All outputs are modeled as `Event` references.
3. Transition handlers and Draft flows are generated and tested across all stacks.
4. State persistence and transition history behavior are consistent and validated.
5. All required tests and example suites pass.
6. Living document tracker reflects final delivered state.
7. All required documentation is synchronized with final behavior.
