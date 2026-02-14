# Contributing to Prophet

Thanks for contributing.

## Development Setup

```bash
python3 -m venv .venv --system-site-packages
.venv/bin/pip install --no-build-isolation -e ./prophet-cli
.venv/bin/pip install build twine
```

## Core Validation Commands

From repo root:

```bash
python3 -m unittest discover -s prophet-cli/tests -p 'test_*.py' -v
python3 -m build prophet-cli
python3 -m twine check prophet-cli/dist/*
```

From `examples/java/prophet_example_spring`:

```bash
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen --wire-gradle
$(git rev-parse --show-toplevel)/.venv/bin/prophet check --show-reasons
./gradlew :prophet_generated:compileJava compileJava
./gradlew test
```

## Contribution Workflow

1. Create a branch from `main`.
2. Make focused changes with tests/docs.
3. Ensure all validation commands pass.
4. Commit with clear messages.
5. Open a PR with:
   - what changed
   - why
   - validation commands + results

## Guidelines

- Treat `id` values in ontology definitions as immutable compatibility anchors.
- Prefer deterministic generation changes over ad hoc runtime behavior.
- Do not hand-edit generated files under `gen/`; update templates/CLI and regenerate.
- Update docs when behavior or contracts change.

## Open Items (Good First/Next Contributions)

### Migration and Schema Evolution

- Improve delta migration diff quality for renames (table/column) with explicit rename hints.
- Add optional “strict safety mode” that blocks generation when destructive flags are detected.
- Extend delta report with machine-readable remediation steps.

### Query and API Contracts

- Add typed `notEq` / `notIn` / `isNull` operators to generated filter DSL.
- Add stable sort DSL (`field + direction`) to typed query contract.
- Add end-to-end HTTP tests for typed query endpoint behavior.

### Action Runtime Integration

- Add optional service-level interception hooks (auth, audit, metrics) in generated boundaries.
- Add generated action service test scaffolding templates.

### Compatibility and Versioning

- Expand compatibility rules for enum value additions/removals with configurable strictness.
- Add per-change “why” references in CLI output (rule IDs mapped to policy tables).

### Tooling and DX

- Add richer `prophet check --json` output for CI systems.
- Add first-class upgrade docs from `0.1.x` to `0.2.x`.
- Improve CLI diagnostics with field/state hyperlinks in terminal-friendly format.

### Runtime Coverage

- Add optional Testcontainers-backed real PostgreSQL integration tests for the example app.
- Add sample app for a second server framework integration target.
