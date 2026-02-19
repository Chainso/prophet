# Prophet Example: Spring Boot + JPA

This example is a runnable Spring Boot app generated from a Prophet ontology for a small commerce workflow.

## What This Example Models

A compact commerce domain with:
- users and orders
- order lifecycle transitions (`created -> approved -> shipped`)
- actions for create/approve/ship order flows
- signal and transition events
- UI-facing display labels via DSL `name "..."` metadata

## What This Example Showcases

- `java_spring_jpa` generation end-to-end
- generated Spring query + action controllers
- generated JPA entities/repositories and transition support
- OpenAPI and SQL generation from the same ontology
- generated extension seams for user-owned action handler logic

## Files to Inspect

- DSL source: `ontology/local/main.prophet`
- App wiring + handlers: `src/main/java/com/example/prophet/commerce_local/`
- Generated Spring artifacts: `gen/spring-boot/src/main/java/com/example/prophet/commerce_local/generated/`
- Generated OpenAPI: `gen/openapi/openapi.yaml`
- Generated SQL: `gen/sql/schema.sql`

## Generate

```bash
cd examples/java/prophet_example_spring
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen --wire-gradle
```

## Run

```bash
cd examples/java/prophet_example_spring
./gradlew bootRun
```

## Database

- Default: embedded H2 (no external DB needed)
- H2 console: `http://localhost:8080/h2-console`
- Default JDBC URL: `jdbc:h2:mem:prophet_example`

Optional override:

```bash
export SPRING_DATASOURCE_URL='jdbc:h2:mem:prophet_example;MODE=PostgreSQL;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE'
export SPRING_DATASOURCE_USERNAME=sa
export SPRING_DATASOURCE_PASSWORD=
```

## Example Endpoints

- `GET /orders/{orderId}`
- `GET /orders?page=0&size=20&sort=orderId,asc`
- `POST /orders/query`
- `POST /actions/createOrder`
- `POST /actions/approveOrder`
- `POST /actions/shipOrder`

## Test

```bash
cd examples/java/prophet_example_spring
./gradlew test
```
