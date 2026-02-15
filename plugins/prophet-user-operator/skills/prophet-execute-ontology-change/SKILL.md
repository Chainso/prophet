---
name: prophet-execute-ontology-change
description: Execute Prophet ontology changes directly by editing DSL source files, validating, planning, regenerating artifacts, and verifying integration outcomes. Use when users ask to add, change, or refactor domain models, actions, signals, triggers, refs, structs, keys, or query behavior.
---

# Prophet Execute Ontology Change

## Operator Contract

- Perform the work directly. Do not stop at recommendations.
- Only pause for: missing required business decisions, permission blocks, or destructive ambiguity.
- Edit source-of-truth files (`.prophet`, `prophet.yaml`, user-owned code), not generated `gen/**` as the primary fix path.

## Inputs to Resolve

1. Locate Prophet project root (`prophet.yaml`).
2. Resolve ontology DSL path from `project.ontology_file`.
3. Infer active stack and targets from `generation.stack` and `generation.targets`.

## Execution Workflow

1. Read current ontology and identify impacted concepts.
2. Apply DSL edits to satisfy user intent.
3. Preserve current Prophet modeling rules:
   - fields are required by default; use `optional` when needed,
   - actions use inline `input {}` and `output {}`,
   - use `ref(ObjectName)` for object references,
   - use `struct` for embedded value objects,
   - signals are top-level explicit events; action outputs and transitions are derived.
4. Run validation:
   - `prophet validate`
5. Run compatibility/impact plan:
   - `prophet plan --show-reasons`
6. Regenerate:
   - `prophet gen`
   - use `prophet gen --wire-gradle` when Java Spring module wiring is expected.
7. Run project verification gates when available:
   - Java: `./gradlew test`
   - Node: `npm run build` and `npm run test:integration` if present
   - Python: framework test suite (`pytest` if configured)
8. If failures occur, fix root causes and repeat validate/plan/gen/test loop.

## Completion Criteria

- Ontology intent is implemented in DSL.
- `prophet validate` passes.
- Regeneration completed without unresolved errors.
- Relevant project tests/build checks pass or clearly documented if blocked.

## Response Requirements

- Summarize exact files changed.
- Include key command outcomes.
- Call out any follow-up required from the user only if truly necessary.
