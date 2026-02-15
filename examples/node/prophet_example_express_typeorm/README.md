# Prophet Example: Express + TypeORM

This example demonstrates Prophet generation for the `node_express_typeorm` stack.

## Generate

```bash
cd examples/node/prophet_example_express_typeorm
../../../.venv/bin/prophet gen
```

Generated output includes:

- `gen/node-express/src/generated/**`
- `gen/node-express/src/generated/typeorm-entities.ts`
- `gen/openapi/openapi.yaml`
- `gen/sql/schema.sql`

## Run

```bash
npm install
npm run dev
```

The example boots a local SQLite database (`prophet_example.sqlite`) and wires concrete action handlers in `src/server.ts`.
Try:

1. `POST /actions/createOrder`
2. `POST /actions/approveOrder`
3. `POST /actions/shipOrder`
4. `POST /orders/query`

## Production DB Notes

This example uses `sqlite` with `synchronize: true` for fast local testing.

For production:
- configure TypeORM `DataSource` from environment (host/port/user/password/db/ssl/pool)
- use your production driver (`postgres`, `mysql`, `mssql`, etc.)
- set `synchronize: false`
- manage schema changes with migrations
