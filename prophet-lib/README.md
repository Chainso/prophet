<p align="center">
  <img src="https://raw.githubusercontent.com/Chainso/prophet/main/brand/exports/logo-horizontal-color.png" alt="Prophet logo" />
</p>

---

# prophet-lib

Shared, non-generated Prophet runtime libraries used by generated stacks.

These packages provide the common async `EventPublisher` contract and `EventWireEnvelope` model across Node, Python, and Java.

Main project repository:
- https://github.com/Chainso/prophet

## Packages

| Language | Package | README |
| --- | --- | --- |
| JavaScript | `@prophet-ontology/events-runtime` | [`prophet-lib/javascript/README.md`](javascript/README.md) |
| Python | `prophet-events-runtime` | [`prophet-lib/python/README.md`](python/README.md) |
| Java | `io.prophet:prophet-events-runtime` | [`prophet-lib/java/README.md`](java/README.md) |

## Event Wire Contract

- Human-readable spec: [`prophet-lib/specs/wire-contract.md`](specs/wire-contract.md)
- JSON Schema: [`prophet-lib/specs/wire-event-envelope.schema.json`](specs/wire-event-envelope.schema.json)

## Local Validation

From repository root:

```bash
npm --prefix prophet-lib/javascript test
PYTHONPATH=prophet-lib/python/src python3 -m unittest discover -s prophet-lib/python/tests -p 'test_*.py' -v
cd examples/java/prophet_example_spring && ./gradlew -p ../../../prophet-lib/java test
```

## More Information

- Main repository README: https://github.com/Chainso/prophet#readme
- Runtime publish runbook: [`docs/developer/prophet-lib-release.md`](../docs/developer/prophet-lib-release.md)
- Publishing setup checklist: [`docs/developer/publishing-setup.md`](../docs/developer/publishing-setup.md)
- CI/CD details: [`docs/developer/ci-cd.md`](../docs/developer/ci-cd.md)
- Stack references:
  - Node/Express: [`docs/reference/node-express.md`](../docs/reference/node-express.md)
  - Python: [`docs/reference/python.md`](../docs/reference/python.md)
  - Spring Boot: [`docs/reference/spring-boot.md`](../docs/reference/spring-boot.md)
