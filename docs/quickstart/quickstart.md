# Prophet Quickstart

This guide is for first-time users who want to generate and run a working Spring Boot integration with Prophet.

## 1. Install CLI

Install from PyPI:

```bash
python3 -m pip install --upgrade prophet-cli
prophet --help
```

Or install from this repository for local development:

```bash
python3 -m venv .venv --system-site-packages
.venv/bin/pip install --no-build-isolation -e ./prophet-cli
```

If `prophet` is not on your PATH, use `.venv/bin/prophet` in commands below.

## 2. Generate From the Example Ontology

```bash
cd examples/java/prophet_example_spring
prophet validate
prophet gen --wire-gradle
```

Expected outcome:
- `gen/sql/schema.sql`
- `gen/openapi/openapi.yaml`
- `gen/spring-boot/**`
- `.prophet/ir/current.ir.json`

## 3. Run Verification Gates

```bash
cd examples/java/prophet_example_spring
prophet check --show-reasons
./gradlew :prophet_generated:compileJava compileJava
./gradlew test
```

Expected outcome:
- `prophet check` reports no validation/compatibility drift issues
- Gradle compile and tests pass

## 4. Run the App

```bash
cd examples/java/prophet_example_spring
./gradlew bootRun
```

Default runtime profile uses embedded H2.

## 5. Explore Generated APIs

Object APIs:
- `GET /orders`
- `POST /orders/query`
- `GET /orders/{orderId}`
- `GET /users`
- `POST /users/query`
- `GET /users/{userId}`

Action APIs:
- `POST /actions/createOrder`
- `POST /actions/approveOrder`
- `POST /actions/shipOrder`

## Next Reads

- Full CLI reference: `docs/reference/cli.md`
- DSL reference: `docs/reference/dsl.md`
- Spring integration details: `docs/reference/spring-boot.md`
- Troubleshooting: `docs/reference/troubleshooting.md`
