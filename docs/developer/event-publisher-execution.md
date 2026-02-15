# Event Publisher Migration Execution

Status tracking for the end-to-end implementation requested by the user.

## Objective

Replace legacy generated event-emitter contracts with async-first `EventPublisher` contracts and event wire envelopes across Node, Python, and Java. Add shared non-generated runtimes under `prophet-lib/`, update examples, docs, and CI/publish workflows, and ship via deliverable-by-deliverable commits.

## Full Plan

### Phase 1: Foundations

1. Create this execution tracker and maintain it after every deliverable.
2. Add `prophet-lib/` with 3 runtime packages:
   - JavaScript: `@prophet/events-runtime`
   - Python: `prophet-events-runtime`
   - Java: `io.prophet:prophet-events-runtime`
3. Standardize runtime API shape:
   - `EventWireEnvelope`
   - async `EventPublisher` with `publish` and `publishBatch`
   - helper utilities for `event_id` and timestamps
   - no-op publisher implementations

### Phase 2: Generator Migration

4. Node codegen migration:
   - Generate `DomainEvent` closed sum for action outputs + signals
   - Generate `ActionOutcome<T>` and ergonomic helpers
   - Replace event-emitter path with `EventPublisher` path
   - Emit envelopes and publish batched events in deterministic order
5. Python codegen migration:
   - Same conceptual migration as Node
   - Keep FastAPI async path native
   - Provide sync wrappers for Flask/Django while retaining async publisher default
6. Java codegen migration:
   - Generate async event publishing path via `CompletionStage`
   - Generate action outcome contracts and envelope mapping utilities
   - Remove generated per-event emitter interfaces

### Phase 3: Consumer Integration

7. Update all examples to use new contracts:
   - Node: inject `EventPublisher`
   - Python: inject `EventPublisher` in runtime wiring
   - Java: wire async publisher bean
8. Update extension hooks manifest to include event publisher seam metadata.

### Phase 4: CI, Publish, Docs

9. Extend CI with `prophet-lib` validation jobs.
10. Add staged publish workflow for `prophet-lib`:
    - Phase 1 internal/test registries
    - Phase 2 public registries
11. Add runbooks:
    - local testing for `prophet-lib`
    - staged publish and promotion flow

### Phase 5: Validation and Finalization

12. Regenerate example artifacts/snapshots and commit updated generated outputs.
13. Run test matrix and fix regressions.
14. Final release prep notes and changelog updates.

## Deliverables

- [x] D1: Create implementation plan and progress tracker (this file)
- [x] D2: Add `prophet-lib` runtime packages for JavaScript, Python, Java
- [x] D3: Migrate Node generator to `EventPublisher` + `ActionOutcome` + event wire envelopes
- [x] D4: Migrate Python generator to `EventPublisher` + `ActionOutcome` + event wire envelopes
- [x] D5: Migrate Java generator to async `EventPublisher` + `ActionOutcome` + event wire envelopes
- [x] D6: Update examples to compile and run with new generated contracts
- [ ] D7: Add CI workflows/jobs for `prophet-lib` validation and staged publish
- [ ] D8: Add local testing + release runbooks for `prophet-lib`
- [ ] D9: Regenerate snapshots/artifacts and run validation suites

## Commit Strategy

- One commit per deliverable (D1..D9).
- If a deliverable is too large, split into sub-commits with a `Dx.y` prefix but keep changes scoped to that deliverable.

## Acceptance Criteria

- No generated stack uses legacy per-event emitter interfaces.
- Node/Python/Java generated action flows support:
  - raw output return shorthand
  - `ActionOutcome` return with additional events
  - deterministic publish order: primary action output event first, then additional events
- All published envelopes follow event wire contract fields:
  - `event_id`, `trace_id`, `event_type`, `schema_version`, `occurred_at`, `source`, `payload`, optional `attributes`
- Runtime packages build and test locally.
- Examples compile/run with new generated contracts.
- CI includes runtime validation and staged publish workflow.

## Progress Log

- 2026-02-15: D1 completed and committed.
- 2026-02-15: D2 completed and committed (JS/Python/Java runtime scaffolds added).
- 2026-02-15: D3 completed and committed (Node generator now publishes via async EventPublisher and event wire envelopes).
- 2026-02-15: D4 completed and committed (Python generator now uses async EventPublisher contracts with ActionOutcome shorthands).
- 2026-02-15: D5 completed and committed (Java Spring generator migrated to async EventPublisher with ActionOutcome + domain event wrappers).
- 2026-02-15: D6 completed (examples rewired to EventPublisher contracts; generated outputs regenerated and validated for compile/smoke paths).

## Notes

- `EventPublisher` is async by default in all language runtimes.
- Naming: use "event publisher" APIs and "event wire contract" terminology for envelope spec.
- No backward compatibility constraints are applied for legacy emitter contracts.
