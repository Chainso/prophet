# AGENTS Guide

This file is for AI coding agents working in this repository.

## Mission

Prophet is an ontology-to-artifact compiler.  
Prioritize deterministic generation, compatibility safety, and clear developer experience.

## First Steps

1. Read `README.md` for repo entry points.
2. Read `docs/quickstart/quickstart.md` and `docs/reference/index.md` for user-facing behavior.
3. Use `examples/java/prophet_example_spring` as the canonical validation app.
4. Read `docs/developer/index.md` before changing internal architecture.

## Critical Rules

- Do not hand-edit generated files under `gen/` as a source of truth.
- Implement generator/template changes in source modules (`prophet_cli/core`, `prophet_cli/codegen`, `prophet_cli/targets/*`), then regenerate.
- Preserve deterministic output ordering.
- Keep ontology `id` values as immutable compatibility anchors.
- Spring generated Java package root is ontology-scoped: `<base_package>.<ontology_name>`.
- When behavior changes, update docs and tests in the same change.

## Commands

Python/CLI tests:

```bash
python3 -m unittest discover -s prophet-cli/tests -p 'test_*.py' -v
```

Example app generation + checks:

```bash
cd examples/java/prophet_example_spring
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen --wire-gradle
$(git rev-parse --show-toplevel)/.venv/bin/prophet check --show-reasons
./gradlew :prophet_generated:compileJava compileJava
./gradlew test
```

## Where to Edit

- CLI command orchestration: `prophet-cli/src/prophet_cli/cli.py`
- Core compiler modules: `prophet-cli/src/prophet_cli/core/`
- Codegen contracts/pipeline/artifacts: `prophet-cli/src/prophet_cli/codegen/`
- Stack generators: `prophet-cli/src/prophet_cli/targets/`
- CLI package docs: `prophet-cli/README.md`
- User docs: `docs/quickstart/`, `docs/reference/`
- Developer docs: `docs/developer/`
- Contributor guidance/backlog: `CONTRIBUTING.md`, `docs/developer/contributing.md`

## Release Notes

- Toolchain version lives in:
  - `prophet-cli/pyproject.toml`
  - `prophet-cli/src/prophet_cli/cli.py` (`TOOLCHAIN_VERSION`)
- Keep them in sync (enforced by tests).
- See `prophet-cli/RELEASING.md` and `prophet-cli/CHANGELOG.md`.
