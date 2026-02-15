---
name: prophet-execute-integration-update
description: Execute Prophet integration updates directly by regenerating artifacts and implementing required user-owned extension points in Java, Node, or Python applications. Use when users ask to wire generated code, implement handlers, integrate emitters, or make generated APIs runnable end-to-end.
license: See LICENSE for complete terms
allowed-tools: Bash(prophet:validate:*) Bash(prophet:plan:*) Bash(prophet:check:*) Bash(prophet:stacks:*) Bash(prophet:hooks:*) Bash(prophet:version:check:*) Bash(prophet:generate:--verify-clean:*) Bash(prophet:gen:--verify-clean:*)
---

# Prophet Execute Integration Update

## Operator Contract

- Execute integration work directly in the repository.
- Do not only provide instructions unless blocked by permissions or missing required decisions.
- Never treat generated files as the only integration layer; implement user-owned glue and handlers.

## Integration Boundary Rules

- Generated files in `gen/**` are tool-owned.
- Application files outside generated output are user-owned and should contain business logic.
- Default generated action handlers are placeholders; replace or wire concrete implementations.
- Event emitter integration is optional but should be wired when requested.

## Execution Workflow

1. Detect project stack from `prophet.yaml` or manifest outputs.
2. Regenerate artifacts:
   - `prophet gen`
   - Java stack: include `--wire-gradle` when needed.
3. Implement required application code changes in user-owned files:
   - action handlers/services,
   - repository/data-source/session wiring,
   - optional custom event emitter implementation.
4. Verify stack-specific runtime expectations:
   - Java Spring + JPA:
     - generated module compiles,
     - app module compiles/tests pass.
   - Node Express:
     - TypeScript build passes,
     - integration tests pass,
     - ORM bootstrap uses app-owned DB configuration.
   - Python frameworks:
     - generated routes wired into app,
     - test-client based tests pass.
5. If runtime errors appear, fix the integration code and re-run tests.

## Verification Commands (Preferred)

- `prophet check --show-reasons`
- Java: `./gradlew test`
- Node: `npm run build` then `npm run test:integration`
- Python: run project test command (prefer `pytest` where configured)

## Completion Criteria

- Requested integration behavior works end-to-end.
- Build/tests pass for relevant stack.
- Generated-to-user-owned boundary remains clean and maintainable.

## Response Requirements

- List user-owned files modified.
- List generated outputs refreshed.
- Report verification commands run and outcomes.
