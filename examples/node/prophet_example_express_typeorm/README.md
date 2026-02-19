# Prophet Example: Express + TypeORM

This example is a runnable Node/Express app generated from a Prophet ontology for a small commerce workflow.

## What This Example Models

A commerce domain with:
- users and orders
- order lifecycle transitions (`created -> approved -> shipped`)
- actions for create/approve/ship
- signal and transition events
- UI-facing display labels via DSL `name "..."` metadata

## What This Example Showcases

- `node_express_typeorm` generation end-to-end
- generated typed contracts, routes, and service seams
- generated TypeORM entities + repository adapters
- OpenAPI + SQL generation from one ontology

## Files to Inspect

- DSL source: `ontology/local/main.prophet`
- App wiring + handlers: `src/server.ts`
- Generated Node artifacts: `gen/node-express/src/generated/`
- Generated TypeORM entities: `gen/node-express/src/generated/typeorm-entities.ts`
- Generated OpenAPI: `gen/openapi/openapi.yaml`

## Generate

```bash
cd examples/node/prophet_example_express_typeorm
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
```

## Run

```bash
cd examples/node/prophet_example_express_typeorm
npm install
npm run dev
```

## Try

1. `POST /actions/createOrder`
2. `POST /actions/approveOrder`
3. `POST /actions/shipOrder`
4. `POST /orders/query`

## Test

```bash
cd examples/node/prophet_example_express_typeorm
npm run build
npm run test:integration
```

## Production DB Note

This example uses SQLite + `synchronize: true` for local speed. Use migrations and `synchronize: false` for production.
