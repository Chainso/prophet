# AGENTS Guide

This file is for AI coding agents working in this repository.

## Mission

Prophet is an ontology-to-artifact compiler.  
Prioritize deterministic generation, compatibility safety, and clear developer experience.

## First Steps

1. Read [README.md](README.md) for repo entry points.
2. Read quickstarts and reference:
   - [Quickstart Overview](docs/quickstart/quickstart.md)
   - [Java Quickstart](docs/quickstart/java.md)
   - [Node Quickstart](docs/quickstart/node.md)
   - [Python Quickstart](docs/quickstart/python.md)
   - [Turtle Target Reference](docs/reference/turtle.md)
   - [Reference Index](docs/reference/index.md)
3. Use the example app matching your target stack:
   - [examples/java/prophet_example_spring](examples/java/prophet_example_spring)
   - [examples/node/prophet_example_express_prisma](examples/node/prophet_example_express_prisma)
   - [examples/node/prophet_example_express_typeorm](examples/node/prophet_example_express_typeorm)
   - [examples/node/prophet_example_express_mongoose](examples/node/prophet_example_express_mongoose)
   - [examples/python/prophet_example_fastapi_sqlalchemy](examples/python/prophet_example_fastapi_sqlalchemy)
   - [examples/python/prophet_example_fastapi_sqlmodel](examples/python/prophet_example_fastapi_sqlmodel)
   - [examples/python/prophet_example_flask_sqlalchemy](examples/python/prophet_example_flask_sqlalchemy)
   - [examples/python/prophet_example_flask_sqlmodel](examples/python/prophet_example_flask_sqlmodel)
   - [examples/python/prophet_example_django](examples/python/prophet_example_django)
   - [examples/turtle/prophet_example_turtle_minimal](examples/turtle/prophet_example_turtle_minimal)
4. Read [Developer Index](docs/developer/index.md) before changing internal architecture.

## Critical Rules

- Do not hand-edit generated files under `gen/` as a source of truth.
- Implement generator/template changes in source modules (`prophet_cli/core`, `prophet_cli/codegen`, `prophet_cli/targets/*`), then regenerate.
- Preserve deterministic output ordering.
- Keep ontology `id` values as immutable compatibility anchors.
- Spring generated Java package root is ontology-scoped: `<base_package>.<ontology_name>`.
- When behavior changes, update docs and tests in the same change.
- Action outputs are event-based: use `output { ... }`, `output signal <SignalName>`, or `output transition <Object>.<transition>`.
- User-defined DSL field name `state` is reserved globally and must be rejected by validation.

## Commands

Python/CLI tests:

```bash
python3 -m unittest discover -s prophet-cli/tests -p 'test_*.py' -v
```

All suites (CLI + Java + Node + Python examples):

```bash
./scripts/test-all.sh
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
npm run prisma:push
npm run build
npm run test:integration

cd ../prophet_example_express_typeorm
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
npm install
npm run build
npm run test:integration

cd ../prophet_example_express_mongoose
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
npm install
npm run build
npm run test:integration
```

Python example generation + checks:

```bash
cd examples/python/prophet_example_fastapi_sqlalchemy
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
$(git rev-parse --show-toplevel)/.venv/bin/prophet check --show-reasons
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=$(git rev-parse --show-toplevel)/prophet-lib/python/src:src:gen/python/src \
.venv/bin/python -m pytest -q tests

cd ../prophet_example_django
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
$(git rev-parse --show-toplevel)/.venv/bin/prophet check --show-reasons
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
DJANGO_SETTINGS_MODULE=prophet_example_django.settings \
PYTHONPATH=$(git rev-parse --show-toplevel)/prophet-lib/python/src:src:gen/python/src \
.venv/bin/python -m pytest -q tests
```

Turtle target smoke check:

```bash
python3 -m unittest prophet-cli/tests/test_turtle_target.py -v
cd examples/turtle/prophet_example_turtle_minimal
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
cd $(git rev-parse --show-toplevel)
pyshacl -s prophet.ttl -d prophet.ttl examples/turtle/prophet_example_turtle_minimal/gen/turtle/ontology.ttl -e prophet.ttl --advanced --inference owlrl --format turtle
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
- Runtime wire contract/spec docs: [prophet-lib/specs/wire-contract.md](prophet-lib/specs/wire-contract.md) and [prophet-lib/specs/wire-event-envelope.schema.json](prophet-lib/specs/wire-event-envelope.schema.json)

## Release Notes

- Toolchain version lives in:
  - [prophet-cli/pyproject.toml](prophet-cli/pyproject.toml)
  - [prophet-cli/src/prophet_cli/cli.py](prophet-cli/src/prophet_cli/cli.py) (`TOOLCHAIN_VERSION`)
- Keep them in sync (enforced by tests).
- See [prophet-cli/RELEASING.md](prophet-cli/RELEASING.md) and [prophet-cli/CHANGELOG.md](prophet-cli/CHANGELOG.md).
