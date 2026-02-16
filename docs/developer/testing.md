# Testing Strategy

## Primary Entry Point

Run every supported suite from repository root:

```bash
./scripts/test-all.sh
```

Optional dependency bootstrapping:

```bash
./scripts/test-all.sh --install
```

This runs:
- CLI/unit suites
- Java example tests
- Node example integration tests
- Python example integration tests
- generation drift/verification checks

## CLI and Compiler Tests

```bash
python3 -m unittest discover -s prophet-cli/tests -p 'test_*.py' -v
```

Coverage includes parser, IR pipeline, stack detection, compatibility rules, and generation snapshots.

## Java Example Tests

From [examples/java/prophet_example_spring](../../examples/java/prophet_example_spring):

```bash
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen --wire-gradle
$(git rev-parse --show-toplevel)/.venv/bin/prophet check --show-reasons
./gradlew :prophet_generated:compileJava compileJava
./gradlew test
```

## Node Example Tests

Node examples use Mocha + Supertest.

Prisma:

```bash
cd examples/node/prophet_example_express_prisma
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
npm install
npm run prisma:generate
npm run prisma:push
npm run build
npm run test:integration
```

TypeORM:

```bash
cd examples/node/prophet_example_express_typeorm
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
npm install
npm run build
npm run test:integration
```

Mongoose:

```bash
cd examples/node/prophet_example_express_mongoose
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
npm install
npm run build
npm run test:integration
```

## Python Example Tests

Python examples use `pytest` + framework-native test clients:
- FastAPI: `fastapi.testclient.TestClient`
- Flask: `app.test_client()`
- Django: `django.test.Client`

FastAPI / Flask:

```bash
cd <python-example>
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=$(git rev-parse --show-toplevel)/prophet-lib/python/src:src:gen/python/src \
.venv/bin/python -m pytest -q tests
```

Django:

```bash
cd examples/python/prophet_example_django
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
DJANGO_SETTINGS_MODULE=prophet_example_django.settings \
PYTHONPATH=$(git rev-parse --show-toplevel)/prophet-lib/python/src:src:gen/python/src \
.venv/bin/python -m pytest -q tests
```

No example tests should depend on launching uvicorn/flask/django servers in-process.

## Packaging Validation

```bash
python3 -m build prophet-cli
python3 -m twine check prophet-cli/dist/*
```

## Performance Benchmark

No-op generation benchmark script:
- [prophet-cli/scripts/benchmark_noop_generation.py](../../prophet-cli/scripts/benchmark_noop_generation.py)
