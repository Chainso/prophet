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
- `GET /orders?page=0&size=20&currentState=CREATED&customerUserId=u_123`
- `GET /users/{userId}`
- `GET /users?page=0&size=20`
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

## Notes

- Hibernate generates schema from JPA entities at startup (`ddl-auto=update`) in this example.
- Prophet also generates migration artifacts:
  - Flyway: `gen/migrations/flyway/V1__prophet_init.sql`
  - Liquibase: `gen/migrations/liquibase/**`
  - Spring runtime resources under `gen/spring-boot/src/main/resources/db/**` are auto-detected from existing app dependencies/plugins.
- Generated classes live under `gen/spring-boot/src/main/java/com/example/prophet/generated`.
- Event ingestion/dispatch is external; this app only exposes action endpoints.
