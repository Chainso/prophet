# Prophet Example Java (Spring Boot)

This app was generated via Spring Initializr and then wired with Prophet-generated Spring/JPA artifacts.

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
- `POST /actions/approve_order`
- `POST /actions/ship_order`

## Notes

- Hibernate generates schema from JPA entities at startup (`ddl-auto=update`).
- Generated classes live under `src/main/java/com/example/prophet/generated`.
- Seer owns event ingestion/dispatch; this app only exposes action endpoints.
