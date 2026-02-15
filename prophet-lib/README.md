# prophet-lib

Shared, non-generated Prophet runtime libraries used by generated stacks.

Packages:
- JavaScript: `@prophet/events-runtime`
- Python: `prophet-events-runtime`
- Java: `io.prophet:prophet-events-runtime`

All runtimes expose async-first `EventPublisher` contracts and the event wire envelope model.

## Local Validation

From repository root:

```bash
npm --prefix prophet-lib/javascript test
PYTHONPATH=prophet-lib/python/src python3 -m unittest discover -s prophet-lib/python/tests -p 'test_*.py' -v
cd examples/java/prophet_example_spring && ./gradlew -p ../../../prophet-lib/java test
```

## Publishing

- CI validation: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
- Runtime publish workflow: [`.github/workflows/publish-prophet-lib.yml`](../.github/workflows/publish-prophet-lib.yml)
- Maintainer runbook: [`docs/developer/prophet-lib-release.md`](../docs/developer/prophet-lib-release.md)
