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
PYTHONPATH=src:gen/python/src .venv/bin/python -m pytest -q tests
```

From Node examples (Mocha + Supertest):

```bash
cd examples/node/prophet_example_express_prisma
npm install
npm run test:integration
```

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
