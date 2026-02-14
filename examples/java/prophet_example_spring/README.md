# Prophet Example Java (Spring Boot)

This app was generated via Spring Initializr and then wired with Prophet-generated Spring/JPA artifacts.

## Generate First

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

- Uses embedded H2 by default (no external DB required).
- H2 console: `http://localhost:8080/h2-console`
- Default JDBC URL: `jdbc:h2:mem:prophet_example`

Optional override:

```bash
export SPRING_DATASOURCE_URL=jdbc:h2:mem:prophet_example;MODE=PostgreSQL;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE
export SPRING_DATASOURCE_USERNAME=sa
export SPRING_DATASOURCE_PASSWORD=
```

## Endpoints

- `GET /orders/{orderId}`
- `GET /orders?page=0&size=20&sort=orderId,asc` (pagination/sort only)
- `GET /users/{userId}`
- `GET /users?page=0&size=20&sort=userId,asc` (pagination/sort only)
- `POST /orders/query` (typed filter DSL with pagination/sort)
- `POST /users/query` (typed filter DSL with pagination/sort)
- `POST /actions/createOrder`
- `POST /actions/approveOrder`
- `POST /actions/shipOrder`

List endpoint response shape:
- generated DTO envelopes (`OrderListResponse`, `UserListResponse`) with:
  - `items`
  - `page`
  - `size`
  - `totalElements`
  - `totalPages`

`/orders/query` example body:

```json
{
  "customer": { "eq": "u_123" },
  "currentState": { "in": ["CREATED", "APPROVED"] },
  "totalAmount": { "gte": 50, "lte": 500 }
}
```

`/users/query` example body:

```json
{
  "email": { "contains": "@example.com" }
}
```

## Notes

- Hibernate generates schema from JPA entities at startup (`ddl-auto=update`) in this example.
- Prophet also generates migration artifacts:
  - Flyway: `gen/migrations/flyway/V1__prophet_init.sql`
  - Liquibase: `gen/migrations/liquibase/**`
  - Spring runtime resources under `gen/spring-boot/src/main/resources/db/**` are auto-detected from existing app dependencies/plugins.
- Generated classes live under `gen/spring-boot/src/main/java/com/example/prophet/commerce_local/generated` for this example.
- Event ingestion/dispatch is external; this app only exposes action endpoints.

## Tests

```bash
cd examples/java/prophet_example_spring
./gradlew test
```

Notable test coverage:
- `ActionHttpFlowIntegrationTest`: end-to-end HTTP flow (`createOrder -> approveOrder -> shipOrder -> query/get`)
- `H2ProfileContextTest`: H2 profile boot sanity
- `PostgresProfileContextTest`: real Postgres profile boot sanity via Testcontainers
