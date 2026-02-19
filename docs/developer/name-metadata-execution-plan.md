# Name Metadata Execution Plan

## Objective

Introduce explicit DSL `name "..."` metadata as the canonical human-facing display label across Prophet surfaces (IR, Turtle, OpenAPI hints, and generated code documentation), while preserving technical identifiers for stability in generated contracts and persistence.

## Change Policy

This initiative is intentionally **breaking**.

- Backward compatibility is **not required**.
- We may change IR shape, parser behavior, and generator expectations in one coordinated rollout.
- Existing ontologies without explicit `name "..."` should still parse, but generated semantics can change.

## Target Outcome

After this rollout:

- DSL supports `name "..."` on ontology concepts and fields.
- Every concept has:
  - a technical symbol/identifier used for wiring and code generation keys
  - a display name used for human-facing metadata
- Turtle `prophet:name` is sourced from DSL `name` metadata (fallback to technical symbol when omitted).
- OpenAPI and generated code docs can expose display names as hints without changing wire keys.

## Scope

In scope:

- Parser and core model updates for explicit `name` metadata
- IR contract updates for explicit display-name carrying
- Generator updates:
  - Turtle
  - OpenAPI
  - Java docs/comments
  - Node docs/comments
  - Python docs/comments
- Tests and snapshots
- User and developer documentation
- Example ontology updates to demonstrate best practices

Out of scope:

- UI framework implementation
- Localization/i18n pipeline
- Per-consumer custom label transformation rules

## Semantic Contract

### DSL

Add optional metadata line:

```prophet
name "Human Readable Label"
```

Supported on:

- `ontology`
- `type`
- `object`
- `struct`
- `field`
- `state`
- `transition`
- `action` + inline input/output shapes
- `signal`
- `trigger`

### Technical vs Display Naming

- Technical symbol:
  - current block identifier (`object Order`, `field order_id`, etc.)
  - used for wiring, references, generated API/property keys, and compatibility anchors
- Display name:
  - value from `name "..."` metadata
  - used for docs/display metadata surfaces

Fallback rule:

- If `name "..."` is omitted, display name defaults to technical symbol.

## IR Contract Changes

Use explicit display naming in IR entities:

- `name`: technical symbol (stable for generator keys and references)
- `display_name`: resolved display label from DSL `name "..."` (fallback to technical symbol)

IR updates required:

- Update IR builder and typed readers to carry `display_name`
- Update generator consumers to read display hints from `display_name`
- Update IR contract docs and tests

## Execution Plan

## Phase 1: Core Compiler

Deliverables:

- Parser accepts `name "..."` metadata everywhere metadata is allowed.
- Core models carry both technical symbol and optional display name metadata.
- Validation includes:
  - duplicate `name` line handling per block
  - empty-string rejection for metadata `name` values

Acceptance:

- Unit tests confirm parsing, fallback behavior, and invalid forms.

## Phase 2: IR + Reader

Deliverables:

- IR schema includes explicit technical and display naming fields.
- IR hash determinism remains stable for identical input.
- `IRReader` updated for new naming fields.

Acceptance:

- IR-focused tests pass with updated expectations.

## Phase 3: Generators

Deliverables:

- Turtle:
  - `prophet:name` sourced from display name
  - `prophet:fieldKey` remains technical field symbol
- OpenAPI:
  - preserve wire keys
  - add display-name hints (`title` and/or vendor extension)
- Java/Node/Python renderers:
  - use display names in generated comments/docs where available
  - do not mutate generated contract property names

Acceptance:

- Snapshot and target tests pass for all stacks.

## Phase 4: Examples + Docs

Deliverables:

- Update **all maintained examples** to include `name "..."` metadata usage.
  - Java, Node, Python, and Turtle example ontologies
  - include field-level `name` metadata in each example (representative or comprehensive per file)
- Update docs:
  - `docs/reference/dsl.md`
  - `docs/quickstart/quickstart.md`
  - `docs/reference/turtle.md`
  - `docs/reference/generation.md`
  - `docs/reference/concepts.md`
  - `README.md`
  - `prophet-cli/README.md`
  - `docs/developer/ir-contract.md`
  - any other user-facing page that describes DSL metadata behavior
- Include guidance on when to use technical symbols vs display names.

Acceptance:

- Docs are internally consistent and include at least one full DSL example with metadata `name`.

## Phase 5: Validation Matrix

Deliverables:

- CLI/unit test suite passes.
- Turtle SHACL tests pass.
- Java/Node/Python example generation and tests pass.
- `./scripts/test-all.sh` passes.

Acceptance:

- Clean CI run with no generator drift.

## Deliverable Checklist

- DSL grammar support for metadata `name`
- Parser/model support for display naming
- IR contract + reader updates
- Turtle naming semantics update
- OpenAPI display hint support
- Java/Node/Python generated doc hint support
- Updated tests and snapshots
- Updated examples with explicit names
- Updated user and developer docs
- Full regression validation across stacks

## Risks and Mitigations

- Risk: generators accidentally use display names for wire keys.
  - Mitigation: explicit tests asserting unchanged wire key names.
- Risk: broad snapshot churn hides regressions.
  - Mitigation: phase-by-phase updates and focused assertions before bulk snapshot updates.
- Risk: inconsistent docs after breaking IR changes.
  - Mitigation: docs update is a required phase-gate before completion.

## Completion Criteria

- All checklist deliverables completed.
- All validation gates pass.
- No remaining references to old naming semantics in docs.
- Team can author UI-friendly labels in DSL without affecting technical contract keys.
