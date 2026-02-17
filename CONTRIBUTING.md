# Contributing to Prophet

Thanks for contributing.

Primary contributor docs now live under:
- [docs/developer/index.md](docs/developer/index.md)
- [docs/developer/contributing.md](docs/developer/contributing.md)
- [docs/developer/testing.md](docs/developer/testing.md)
- [docs/developer/ci-cd.md](docs/developer/ci-cd.md)
- [docs/developer/releasing.md](docs/developer/releasing.md)
- [docs/reference/index.md](docs/reference/index.md)
- [docs/quickstart/quickstart.md](docs/quickstart/quickstart.md)

## Quick Setup

```bash
python3 -m venv .venv --system-site-packages
.venv/bin/pip install --no-build-isolation -e ./prophet-cli
.venv/bin/pip install build twine
```

## Core Validation Commands

From repo root:

```bash
python3 -m unittest discover -s prophet-cli/tests -p 'test_*.py' -v
./scripts/test-all.sh
python3 -m build prophet-cli
python3 -m twine check prophet-cli/dist/*
```

Turtle target coverage (included in CLI suite):

```bash
python3 -m unittest prophet-cli/tests/test_turtle_target.py -v
cd examples/turtle/prophet_example_turtle_minimal
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
cd $(git rev-parse --show-toplevel)
pyshacl -s prophet.ttl -d prophet.ttl examples/turtle/prophet_example_turtle_minimal/gen/turtle/ontology.ttl -e prophet.ttl --advanced --inference owlrl --format turtle
```

From [examples/java/prophet_example_spring](examples/java/prophet_example_spring):

```bash
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen --wire-gradle
$(git rev-parse --show-toplevel)/.venv/bin/prophet check --show-reasons
./gradlew :prophet_generated:compileJava compileJava
./gradlew test
```

From Python examples (framework test clients + pytest):

```bash
cd examples/python/prophet_example_fastapi_sqlalchemy
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=$(git rev-parse --show-toplevel)/prophet-lib/python/src:src:gen/python/src \
.venv/bin/python -m pytest -q tests
```

From Node examples (Mocha + Supertest):

```bash
cd examples/node/prophet_example_express_prisma
npm install
npm run test:integration
```

## Documentation Surfaces to Update for Target Changes

When adding/changing generation targets, update these surfaces in the same change:
- [README.md](README.md)
- [AGENTS.md](AGENTS.md)
- [prophet-cli/README.md](prophet-cli/README.md)
- [docs/reference/config.md](docs/reference/config.md)
- [docs/reference/generation.md](docs/reference/generation.md)
- [docs/reference/index.md](docs/reference/index.md)
- [docs/reference/dsl.md](docs/reference/dsl.md)
- [docs/reference/examples.md](docs/reference/examples.md)
- [docs/reference/turtle.md](docs/reference/turtle.md)
- [docs/quickstart/quickstart.md](docs/quickstart/quickstart.md)
- [docs/developer/codegen-architecture.md](docs/developer/codegen-architecture.md)
- [docs/developer/transition-event-redesign-spec.md](docs/developer/transition-event-redesign-spec.md)
- [prophet-lib/README.md](prophet-lib/README.md)
- [prophet-lib/specs/wire-contract.md](prophet-lib/specs/wire-contract.md)
- [prophet-lib/specs/wire-event-envelope.schema.json](prophet-lib/specs/wire-event-envelope.schema.json)

When changing action output or transition behavior, also verify docs cover:
- event-based action outputs (`output {}`, `output signal`, `output transition`)
- reserved DSL field name `state`
- transition drafts (`fromState` / `toState` + implicit primary keys)
- generated transition validators and `TransitionValidationResult` runtime contracts

## Open Items (Good First/Next Contributions)

### Migration and Schema Evolution

- Improve delta migration diff quality for renames (table/column) with explicit rename hints.
- Add optional strict safety mode that blocks generation when destructive flags are detected.
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
- Add per-change rule references in CLI output.

### Tooling and DX

- Add richer `prophet check --json` output for CI systems.
- Improve CLI diagnostics with field/state hyperlinks in terminal-friendly format.

### Runtime Coverage

- Add optional Testcontainers-backed real PostgreSQL integration tests for the example app.
- Add sample app for a second server framework integration target.
