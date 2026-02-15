# AGENTS Guide

This file is for AI coding agents working in this repository.

## Mission

Prophet is an ontology-to-artifact compiler.  
Prioritize deterministic generation, compatibility safety, and clear developer experience.

## First Steps

1. Read [README.md](README.md) for repo entry points.
2. Read [Quickstart](docs/quickstart/quickstart.md) and [Reference Index](docs/reference/index.md) for user-facing behavior.
3. Use the example app matching your target stack:
   - [examples/java/prophet_example_spring](examples/java/prophet_example_spring)
   - [examples/node/prophet_example_express_prisma](examples/node/prophet_example_express_prisma)
   - [examples/node/prophet_example_express_typeorm](examples/node/prophet_example_express_typeorm)
4. Read [Developer Index](docs/developer/index.md) before changing internal architecture.

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

Node example generation + checks:

```bash
cd examples/node/prophet_example_express_prisma
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
npm install
npm run prisma:generate
npm run build

cd ../prophet_example_express_typeorm
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
npm install
npm run build
```

## Where to Edit

- CLI command orchestration: [prophet-cli/src/prophet_cli/cli.py](prophet-cli/src/prophet_cli/cli.py)
- Core compiler modules: [prophet-cli/src/prophet_cli/core/](prophet-cli/src/prophet_cli/core/)
- Codegen contracts/pipeline/artifacts: [prophet-cli/src/prophet_cli/codegen/](prophet-cli/src/prophet_cli/codegen/)
- Stack generators: [prophet-cli/src/prophet_cli/targets/](prophet-cli/src/prophet_cli/targets/)
- CLI package docs: [prophet-cli/README.md](prophet-cli/README.md)
- User docs: [docs/quickstart/](docs/quickstart/) and [docs/reference/](docs/reference/)
- Developer docs: [docs/developer/](docs/developer/)
- Contributor guidance/backlog: [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/developer/contributing.md](docs/developer/contributing.md)

## Release Notes

- Toolchain version lives in:
  - [prophet-cli/pyproject.toml](prophet-cli/pyproject.toml)
  - [prophet-cli/src/prophet_cli/cli.py](prophet-cli/src/prophet_cli/cli.py) (`TOOLCHAIN_VERSION`)
- Keep them in sync (enforced by tests).
- See [prophet-cli/RELEASING.md](prophet-cli/RELEASING.md) and [prophet-cli/CHANGELOG.md](prophet-cli/CHANGELOG.md).
