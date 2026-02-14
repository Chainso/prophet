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

From `examples/java/prophet_example_spring`:

```bash
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen --wire-gradle
$(git rev-parse --show-toplevel)/.venv/bin/prophet check --show-reasons
./gradlew :prophet_generated:compileJava compileJava
./gradlew test
```

## Packaging Validation

```bash
python3 -m build prophet-cli
python3 -m twine check prophet-cli/dist/*
```
