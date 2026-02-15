---
name: prophet-execute-release-maintenance
description: Execute Prophet maintainer release and repository maintenance tasks directly, including version bumps, regeneration consistency, validation gates, changelog updates, tagging, and push readiness. Use for maintainer-only work in the Prophet repository.
license: See LICENSE for complete terms
allowed-tools: Bash(prophet:validate:*) Bash(prophet:plan:*) Bash(prophet:check:*) Bash(prophet:stacks:*) Bash(prophet:hooks:*) Bash(prophet:version:check:*) Bash(prophet:generate:--verify-clean:*) Bash(prophet:gen:--verify-clean:*)
---

# Prophet Execute Release Maintenance

## Operator Contract

- This skill is for Prophet maintainers working in the Prophet repository.
- Perform release work end-to-end; do not only provide guidance.
- Do not skip verification gates unless explicitly instructed.

## Release Workflow

1. Assess current state:
   - inspect working tree and branch,
   - identify intended release scope.
2. Update versioned artifacts:
   - `prophet-cli/pyproject.toml`,
   - `prophet-cli/src/prophet_cli/cli.py` (`TOOLCHAIN_VERSION`),
   - changelog entry in `prophet-cli/CHANGELOG.md`.
3. Regenerate impacted example outputs with current CLI version:
   - Java example,
   - Node examples,
   - Python examples.
4. Run validation gates:
   - version sync tests,
   - CLI tests,
   - repository-wide verification script (`scripts/test-all.sh`) when feasible.
5. Verify release cleanliness:
   - manifests and generated artifacts reflect new toolchain version,
   - no unintentional drift remains.
6. Prepare release VCS actions:
   - commit with comprehensive bullet-point message,
   - create annotated semver tag (`vX.Y.Z`),
   - push branch and tag when requested.

## Maintenance Workflow (Non-release)

1. Reproduce reported maintainer issue.
2. Fix source modules (parser/core/codegen/targets/docs/tests).
3. Regenerate fixtures/examples as required.
4. Run focused tests and affected integration suites.
5. Commit with clear scope and validation evidence.

## Safety Rules

- Never rely on edits to generated files without corresponding source changes.
- Keep docs, tests, and generated artifacts synchronized with behavior changes.
- Flag blockers explicitly (network, permissions, missing credentials).

## Completion Criteria

- Release or maintenance objective is fully implemented.
- Verification evidence is captured.
- Repository state is ready for maintainers to publish confidently.
