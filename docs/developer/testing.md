# Testing Strategy

## Python / CLI Suite

From repo root:

```bash
python3 -m unittest discover -s prophet-cli/tests -p 'test_*.py' -v
```

Coverage includes:
- parser/validation/compatibility
- stack resolution/manifest contracts
- generation pipeline/cache/artifacts
- deterministic snapshot tests
- CLI integration flows

## Spring Example Validation

From [examples/java/prophet_example_spring](../../examples/java/prophet_example_spring):

```bash
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen --wire-gradle
$(git rev-parse --show-toplevel)/.venv/bin/prophet check --show-reasons
./gradlew :prophet_generated:compileJava compileJava
./gradlew test
```

## Node Example Validation

Prisma example:

```bash
cd examples/node/prophet_example_express_prisma
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
npm install
npm run prisma:generate
npm run build
$(git rev-parse --show-toplevel)/.venv/bin/prophet check --show-reasons
```

TypeORM example:

```bash
cd examples/node/prophet_example_express_typeorm
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
npm install
npm run build
$(git rev-parse --show-toplevel)/.venv/bin/prophet check --show-reasons
```

## Packaging Validation

```bash
python3 -m build prophet-cli
python3 -m twine check prophet-cli/dist/*
```

## Performance Benchmark

No-op generation benchmark script:
- [prophet-cli/scripts/benchmark_noop_generation.py](../../prophet-cli/scripts/benchmark_noop_generation.py)
