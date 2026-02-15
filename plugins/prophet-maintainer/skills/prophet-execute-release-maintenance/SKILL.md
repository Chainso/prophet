---
name: prophet-execute-release-maintenance
description: Execute Prophet maintainer release and repository maintenance tasks directly, including version bumps, regeneration consistency, validation gates, changelog updates, tagging, and push readiness. Use for maintainer-only work in the Prophet repository.
license: See LICENSE for complete terms
allowed-tools: Bash(prophet:validate:*) Bash(prophet:plan:*) Bash(prophet:check:*) Bash(prophet:stacks:*) Bash(prophet:hooks:*) Bash(prophet:version:check:*) Bash(prophet:generate:--verify-clean:*) Bash(prophet:gen:--verify-clean:*) Bash(scripts/test-all.sh:*) Bash(git:status:*) Bash(git:log:*) Bash(git:show:*) Bash(git:diff:*) Bash(git:branch:*) Bash(git:tag:*) Bash(git:rev-parse:*) Bash(git:describe:*) Bash(git:shortlog:*) Bash(git:remote:*) Bash(git:ls-files:*) Bash(git:cat-file:*) Bash(git:blame:*) Bash(git:grep:*) Bash(git:name-rev:*)
---

# Prophet Execute Release Maintenance

## Operator Contract

- This skill is for Prophet maintainers working in the Prophet repository.
- Perform release work end-to-end; do not only provide guidance.
- Do not skip verification gates unless explicitly instructed.

## Release Workflow

1. Assess current state:
   - inspect working tree and branch,
   - identify intended release scope,
   - identify the previous released semver tag and review the full commit range from that tag to `HEAD` (for example: `git log --oneline <previous_tag>..HEAD`).
2. Update versioned artifacts:
   - `prophet-cli/pyproject.toml`,
   - `prophet-cli/src/prophet_cli/cli.py` (`TOOLCHAIN_VERSION`),
   - changelog entry in `prophet-cli/CHANGELOG.md`,
   - release notes draft/body derived from the reviewed commit range since the previous release tag.
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
- Release changelog and release notes account for all commits since the previous released version tag.
- Repository state is ready for maintainers to publish confidently.
