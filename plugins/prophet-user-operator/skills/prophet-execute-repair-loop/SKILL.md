---
name: prophet-execute-repair-loop
description: Execute a full Prophet repair loop by diagnosing failures, fixing root causes in source-of-truth files, regenerating outputs, and re-verifying until green. Use when users report validation errors, compatibility drift, generation issues, compile failures, or runtime faults in generated integrations.
license: See LICENSE for complete terms
allowed-tools: Bash(prophet:validate:*) Bash(prophet:plan:*) Bash(prophet:check:*) Bash(prophet:stacks:*) Bash(prophet:hooks:*) Bash(prophet:version:check:*) Bash(prophet:generate:--verify-clean:*) Bash(prophet:gen:--verify-clean:*)
---

# Prophet Execute Repair Loop

## Operator Contract

- Run the repair loop yourself. Do not stop at diagnosis.
- Fix root causes in ontology/config/generator/application code, then regenerate and verify.
- Avoid one-off edits to generated artifacts that will be overwritten.

## Failure Classification

1. DSL parse or validation failure (`prophet validate`).
2. Compatibility/policy failure (`prophet plan` / `prophet check`).
3. Generation drift or target misconfiguration (`prophet gen`, manifest mismatch).
4. Stack compile/build failure (Gradle/TypeScript/Python import/type errors).
5. Runtime behavior failure (HTTP flow, DI wiring, DB wiring, handler logic).

## Repair Loop

1. Reproduce with the narrowest failing command.
2. Classify failure category.
3. Patch root cause in source files:
   - ontology DSL,
   - `prophet.yaml`,
   - generator source (for Prophet repo work),
   - user-owned app code.
4. Regenerate:
   - `prophet gen` (plus `--wire-gradle` where applicable)
5. Re-run verification:
   - `prophet validate`
   - `prophet check --show-reasons`
   - stack build/tests
6. Repeat until pass.

## Stack Verification Defaults

- Java: `./gradlew test`
- Node: `npm run build` and `npm run test:integration`
- Python: project tests (prefer `pytest` when configured)

## Completion Criteria

- Original failure is resolved and reproducible as fixed.
- Validation/check/build/tests pass for impacted scope.
- Changes are minimal, source-of-truth aligned, and regeneration-safe.

## Response Requirements

- State root cause.
- State exact fix files.
- State verification evidence.
