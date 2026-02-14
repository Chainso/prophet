# Prophet Generator Modularization Strategy and Roadmap v0.1

## Status Snapshot (2026-02-14)

Completed so far:

1. Introduced `prophet_cli.core` package boundaries for:
   - parser
   - validation
   - IR construction
   - compatibility logic
2. Wired CLI delegation to core modules while preserving existing command behavior.
3. Added delegation regression tests to lock the modularization seam.
4. Added explicit stack matrix and capability metadata with CLI validation.
5. Added `prophet stacks` command for contributor/operator visibility.
6. Added generated artifact ownership manifest (`gen/manifest/generated-files.json`) and integrated manifest-aware managed file detection.
7. Added explicit code generation pipeline contract layer (`GenerationContext` + stack generator routing).
8. Added first dedicated target module boundary at `prophet_cli.targets.java_spring_jpa`.
9. Added structured `prophet plan --json` diagnostics for CI and automation workflows.
10. Added explicit stack status metadata (`implemented` vs `planned`) for transparent contributor planning.

In progress:

1. Reducing duplicated legacy logic in `cli.py` now that core delegation is active.
2. Advancing Milestone 2 and Milestone 3 work packages with no behavior drift.
3. Expanding Milestone 4 stack validation into full target manifest schema.

## 1. Purpose

This document defines the strategy, execution plan, and roadmap for modularizing Prophet's generator so it can support multiple language/framework stacks while preserving a single canonical semantics model.

This roadmap intentionally excludes:

- external plugin loading/discovery
- migration generation/runtime migration work

## 2. Strategic Intent

Prophet should compile one ontology semantics model and project it consistently across multiple runtime stacks. The long-term value is not "more templates," but a stable contract system where each generated stack reflects the same domain, action, and query behavior.

The near-term priority is to modularize the existing generator so future target expansion does not create regressions or semantic drift.

## 3. Guiding Principles

1. Canonical semantics first: one source of truth, many projections.
2. Deterministic outputs: same input produces same artifacts every time.
3. Explicit compatibility contracts: no hidden behavior changes across targets.
4. Fail fast on invalid target combinations.
5. Preserve current user workflow while internals evolve.
6. Defer complexity that is not needed yet.

## 4. Scope and Boundaries

### In Scope

1. Generator modularization.
2. Standardized IR reader layer for all generation targets.
3. Target manifest model and stack validation.
4. Artifact ownership tracking for reliable clean behavior.
5. Extension hooks for safe user customization.
6. Cross-target semantic conformance strategy.
7. Performance/caching improvements for generation pipeline.

### Explicitly Out of Scope (Current Phase)

1. External plugin loading/discovery system.
2. Migration generation strategy and migration runtime wiring strategy changes.

## 5. Target Expansion Direction

### Planned Stack Matrix

1. `java_spring_jpa` (baseline and reference implementation)
2. `node_express_typeorm`
3. `node_express_prisma`
4. `node_express_mongoose`
5. `python_fastapi_sqlalchemy`
6. `python_flask_sqlalchemy`
7. `python_django_orm`

### Stack Policy

1. Not every framework can pair with every ORM; supported combinations are explicit.
2. Each stack declares capabilities and constraints up front.
3. Unsupported combinations fail during validation, before generation.

## 6. Operating Model

### Compiler Lifecycle

1. Parse ontology DSL.
2. Validate ontology semantics.
3. Build canonical IR.
4. Read canonical IR through a standardized IR reader and typed views.
5. Select valid target stack(s).
6. Generate artifacts per target.
7. Produce ownership manifest and diagnostics.

### Separation of Concerns

1. Core compiler logic: parsing, validation, IR, compatibility.
2. Target contract layer: shared generation interfaces and capability definitions.
3. Target implementations: language/framework-specific projection.
4. Integration layer: host-project synchronization and lifecycle actions.
5. CLI layer: command surface and orchestration only.

## 7. IR Reader Standardization

The IR reader is a first-class platform boundary and should be introduced before adding new targets.

### Goals

1. Present a stable, typed interface for target generators.
2. Centralize lookup/index/normalization logic.
3. Isolate IR version evolution from target-specific code.
4. Eliminate direct raw-JSON access patterns in target generators.

### Responsibilities

1. Load and validate canonical IR structure.
2. Provide indexed access to common entities.
3. Expose stable "views" for domain, action contracts, and query contracts.
4. Normalize supported IR versions into one target-facing shape.

## 8. Capability and Contract Governance

### Capability Matrix

Each stack must explicitly declare support level for:

1. action endpoint generation
2. action input/output contracts
3. object query contracts and typed filters
4. pagination envelope conventions
5. object reference handling
6. nested list handling
7. struct handling
8. extension/customization hooks

### Compatibility Contract

Compatibility decisions remain centralized and independent from individual targets. Targets consume compatibility outcomes; they do not define compatibility semantics locally.

## 9. Roadmap and Milestones

## Milestone 1: Baseline Freeze and Guardrails

### Objectives

1. Lock current generator behavior as baseline.
2. Strengthen semantic contract tests beyond file snapshots.

### Deliverables

1. Stable golden snapshots for current reference stack.
2. Semantic conformance tests for action and query contracts.

### Exit Criteria

1. No behavior changes introduced.
2. Existing tests pass with no result deltas.

## Milestone 2: Core Compiler Extraction

### Objectives

1. Split monolithic generator internals into core modules.
2. Keep CLI behavior and command interface stable.

### Deliverables

1. Clear module boundaries for parser, validation, IR, and compatibility.
2. Reduced coupling between CLI and generation internals.

### Exit Criteria

1. No output regressions.
2. Operational parity with baseline workflow.

## Milestone 3: Standardized IR Reader and Views

### Objectives

1. Introduce canonical IR reader as a mandatory boundary.
2. Migrate existing target generation to consume IR views.

### Deliverables

1. Typed IR reader and view model.
2. Existing target fully migrated to reader/view APIs.

### Exit Criteria

1. Target code no longer depends on raw IR dictionaries.
2. Existing generated outputs remain unchanged.

## Milestone 4: Target Manifest and Stack Validation

### Objectives

1. Formalize stack selection and capability declarations.
2. Validate supported combinations at configuration time.

### Deliverables

1. Target manifest schema.
2. Stack matrix and constraint validator.
3. Clear diagnostics for invalid target combinations.

### Exit Criteria

1. Invalid combinations fail fast before generation.
2. Supported stacks resolve predictably and consistently.

## Milestone 5: Modularize Reference Target

### Objectives

1. Move current reference stack into isolated target module.
2. Keep existing behavior as compatibility anchor.

### Deliverables

1. Reference target as independent generator package.
2. Shared target contracts used by reference stack.

### Exit Criteria

1. Byte-for-byte stable outputs for reference example.
2. No CLI contract changes required for existing users.

## Milestone 6: Artifact Ownership and Lifecycle Reliability

### Objectives

1. Make generated artifact ownership explicit.
2. Ensure clean/unwire operations are deterministic and safe.

### Deliverables

1. Generated artifact ownership manifest.
2. Manifest-driven cleanup behavior.

### Exit Criteria

1. Clean behavior is deterministic across targets.
2. No accidental deletion of user-authored files.

## Milestone 7: Safe Extension Hooks

### Objectives

1. Allow user customization without regeneration conflicts.
2. Define clear supported extension surfaces.

### Deliverables

1. Documented extension hook model.
2. Regeneration-safe extension behavior tests.

### Exit Criteria

1. Regeneration does not overwrite user extension code.
2. Extension model is consistent across supported stacks.

## Milestone 8: Performance and Caching

### Objectives

1. Reduce no-op generation cost.
2. Improve iterative developer workflow speed.

### Deliverables

1. Deterministic cache keys based on IR and target config.
2. Generation skip behavior when no relevant changes are detected.

### Exit Criteria

1. Repeated no-change generation is measurably faster.
2. Deterministic outputs remain intact.

## 10. Release Roadmap

### 0.3.x Track

Focus: Milestones 1 through 5.

Expected outcome: fully modular internal architecture with reference target preserved.

### 0.4.x Track

Focus: Milestones 6 through 8.

Expected outcome: robust lifecycle behavior, extension safety, and performance readiness.

### 0.5.x Track

Focus: first non-Java stack implementations on top of modular architecture.

Expected outcome: multi-language generation starts from a stable foundation, not ad hoc templates.

## 11. Testing and Quality Strategy

### Test Categories

1. Parser/validation correctness tests.
2. IR and compatibility semantic tests.
3. Target contract tests (language-agnostic).
4. Target snapshot tests (stack-specific outputs).
5. End-to-end stack tests (runtime behavior).

### Quality Gates

1. No milestone merge without passing baseline and semantic tests.
2. No milestone merge without deterministic output checks.
3. No milestone merge without documentation updates for new behavior.

## 12. Risk Register and Mitigations

### Risk: Semantic Drift Across Targets

Mitigation:

1. Centralized compatibility engine.
2. IR view conformance tests shared across targets.

### Risk: Combinatorial Stack Explosion

Mitigation:

1. Explicit supported stack matrix.
2. Capability-driven validation and constraints.

### Risk: Refactor-Induced Regressions

Mitigation:

1. Freeze baseline outputs.
2. Milestone-level regression gates.

### Risk: User Workflow Disruption

Mitigation:

1. Keep CLI behavior stable during modularization.
2. Introduce changes behind compatible defaults first.

## 13. Execution Cadence

1. Work in milestone-scoped branches.
2. Keep commits aligned to milestone sub-goals.
3. Publish milestone notes with:
   - completed deliverables
   - behavior deltas
   - validation evidence
   - remaining risks

## 14. Immediate Next Actions

1. Start Milestone 1 baseline freeze and semantic guardrails.
2. Produce milestone task breakdown with clear acceptance criteria per task.
3. Begin Milestone 2 extraction once Milestone 1 gates are green.

## 15. Open Source Contributor Onboarding

This section is intentionally operational so contributors can start work without additional handholding.

### Who This Is For

1. Contributors who want to work on architecture and compiler boundaries.
2. Contributors who want to add tests and quality gates.
3. Contributors who want to improve docs and contributor experience for generator modularization.

### First Read Sequence

1. `README.md`
2. `CONTRIBUTING.md`
3. `docs/prophet-spec-v0.1.md`
4. `docs/prophet-compatibility-policy-v0.2.md`
5. This roadmap document.

### Working Agreement

1. No milestone implementation should change public semantics unless explicitly called out.
2. Any behavior-affecting change must include updated compatibility reasoning.
3. Every merged milestone must include validation evidence in the PR description.

## 16. Work Package Backlog (Pick-Up Ready)

Each work package is scoped so contributors can deliver independently.

### Milestone 1 Work Packages

1. `M1-W1` Baseline snapshot hardening.
   - Outcome: reference stack snapshots are complete and reliable.
   - Acceptance: no snapshot drift on clean regeneration.
2. `M1-W2` Semantic conformance tests.
   - Outcome: action and query contracts validated independently of file snapshots.
   - Acceptance: tests fail on semantic drift and pass on current baseline.
3. `M1-W3` Regression gate docs.
   - Outcome: clear gate criteria documented for future milestones.
   - Acceptance: PR template references these gates.

### Milestone 2 Work Packages

1. `M2-W1` Parser boundary extraction.
   - Outcome: parsing responsibilities isolated from CLI command flow.
   - Acceptance: no CLI behavior changes.
2. `M2-W2` Validation boundary extraction.
   - Outcome: validation concerns moved behind explicit module boundary.
   - Acceptance: existing validation outputs unchanged.
3. `M2-W3` Compatibility boundary extraction.
   - Outcome: compatibility logic isolated with stable call contract.
   - Acceptance: compatibility classification outputs remain stable.

### Milestone 3 Work Packages

1. `M3-W1` Canonical IR reader contract.
   - Outcome: typed reader boundary documented and introduced.
   - Acceptance: reader supports all currently generated artifacts.
2. `M3-W2` IR index and lookup model.
   - Outcome: normalized lookup patterns centralized.
   - Acceptance: target code can remove local ad hoc lookup logic.
3. `M3-W3` IR view adoption for reference target.
   - Outcome: reference target consumes IR views only.
   - Acceptance: no raw IR dictionary access in target layer.

### Milestone 4 Work Packages

1. `M4-W1` Target manifest schema.
   - Outcome: consistent way to declare stack and capabilities.
   - Acceptance: schema docs and validation behavior are complete.
2. `M4-W2` Stack matrix and constraints.
   - Outcome: supported combinations and invalid combinations are explicit.
   - Acceptance: invalid combinations fail fast with actionable diagnostics.
3. `M4-W3` Capability reporting in diagnostics.
   - Outcome: users can see enabled/unsupported capabilities per target stack.
   - Acceptance: checks and plan outputs include capability context.

### Milestone 5 Work Packages

1. `M5-W1` Reference target packaging.
   - Outcome: baseline stack is modularized as a dedicated target package.
   - Acceptance: generated outputs remain byte-for-byte stable.
2. `M5-W2` Target contract compliance checks.
   - Outcome: reference target formally validated against target contracts.
   - Acceptance: dedicated contract tests pass.
3. `M5-W3` Documentation transition.
   - Outcome: docs updated to reflect modular architecture.
   - Acceptance: contributor docs align with implemented boundaries.

### Milestone 6 Work Packages

1. `M6-W1` Artifact ownership model definition.
2. `M6-W2` Manifest-driven clean semantics.
3. `M6-W3` Lifecycle safety tests for clean/unwire behavior.

### Milestone 7 Work Packages

1. `M7-W1` Extension surface definition.
2. `M7-W2` Regeneration safety policy.
3. `M7-W3` Extension workflow docs and examples.

### Milestone 8 Work Packages

1. `M8-W1` Deterministic cache key strategy.
2. `M8-W2` No-op generation bypass behavior.
3. `M8-W3` Performance baseline and benchmarking report.

## 17. PR and Review Protocol

### PR Requirements

1. State milestone and work package ID in PR title or description.
2. Provide before/after behavior summary.
3. Include validation output relevant to changed scope.
4. Highlight compatibility or contract implications.
5. Update documentation when behavior or workflow changes.

### Review Checklist

1. Does this change preserve canonical semantics?
2. Does this increase or reduce coupling?
3. Are compatibility consequences explicitly described?
4. Are tests aligned to changed behavior?
5. Is contributor onboarding clarity improved or degraded?

## 18. Milestone Exit Artifacts

Each milestone is complete only when these artifacts exist:

1. Milestone summary note.
2. Updated roadmap status with completed work package IDs.
3. Validation evidence summary.
4. Known risk carry-over list to next milestone.
5. Documentation updates merged.

## 19. Decision Log and Governance

### Decision Logging

1. Record major architecture decisions in a concise decision log section in milestone notes.
2. Include decision context, tradeoffs considered, and chosen direction.
3. Link each decision to relevant work package IDs.

### Governance Rules

1. No new stack implementation starts until Milestones 1 through 5 exit criteria are met.
2. Unsupported stack combinations cannot be merged as "experimental defaults."
3. Compatibility semantics remain centralized and cannot fork per target.

## 20. Communication Rhythm

1. Weekly roadmap status update.
2. Milestone kickoff note.
3. Milestone closeout note.
4. Cross-milestone risk review at milestone boundaries.

## 21. Definition of Done for This Roadmap Phase

This modularization phase is complete when:

1. Reference generator is modularized and behavior-preserving.
2. IR reader boundary is mandatory for target generation.
3. Target manifest validation and stack constraints are enforced.
4. Artifact ownership model is in place for lifecycle commands.
5. Extension hooks and no-op performance path are operational.
6. Documentation enables new contributors to start work without private context.

## 22. Open Questions (Tracked)

1. Should target capabilities be versioned independently from toolchain version?
2. Should capability validation support strict and permissive modes?
3. What is the default behavior when multiple target stacks are requested at once?
4. How should extension hooks be represented consistently across language ecosystems?
5. What benchmark threshold is required to consider no-op caching successful?
