# AGENTS Guide

This file is for AI coding agents working in this repository.

## Mission

Prophet is an ontology-to-artifact compiler.  
Prioritize deterministic generation, compatibility safety, and clear developer experience.

## First Steps

1. Read `README.md` for repo entry points.
2. Read `docs/prophet-compatibility-policy-v0.2.md` before touching version logic.
3. Use `examples/java/prophet_example_spring` as the canonical validation app.

## Critical Rules

- Do not hand-edit generated files under `gen/` as a source of truth.
- Implement generator/template changes in `prophet-cli/src/prophet_cli/cli.py`, then regenerate.
- Preserve deterministic output ordering.
- Keep ontology `id` values as immutable compatibility anchors.
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

- CLI and codegen: `prophet-cli/src/prophet_cli/cli.py`
- CLI package docs: `prophet-cli/README.md`
- Root docs: `README.md`, `docs/*`
- Contributor guidance/backlog: `CONTRIBUTING.md`

## Release Notes

- Toolchain version lives in:
  - `prophet-cli/pyproject.toml`
  - `prophet-cli/src/prophet_cli/cli.py` (`TOOLCHAIN_VERSION`)
- Keep them in sync (enforced by tests).
- See `prophet-cli/RELEASING.md` and `prophet-cli/CHANGELOG.md`.
