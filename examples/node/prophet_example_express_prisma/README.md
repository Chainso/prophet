# Prophet Example: Express + Prisma

This example is a runnable Node/Express app generated from a Prophet ontology for a small commerce workflow.

## What This Example Models

A commerce domain with:
- users and orders
- order lifecycle transitions (`created -> approved -> shipped`)
- actions for create/approve/ship
- signal and transition events
- UI-facing display labels via DSL `name "..."` metadata

## What This Example Showcases

- `node_express_prisma` generation end-to-end
- generated typed contracts, routes, and service seams
- generated Prisma schema + adapters
- OpenAPI + SQL generation from one ontology

## Files to Inspect

- DSL source: `ontology/local/main.prophet`
- App wiring + handlers: `src/server.ts`
- Generated Node artifacts: `gen/node-express/src/generated/`
- Generated Prisma schema: `gen/node-express/prisma/schema.prisma`
- Generated OpenAPI: `gen/openapi/openapi.yaml`

## Generate

```bash
cd examples/node/prophet_example_express_prisma
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
```

## Run

```bash
cd examples/node/prophet_example_express_prisma
npm install
export DATABASE_URL="file:./dev.db"
npm run prisma:generate
npm run prisma:push
npm run dev
```

## Try

1. `POST /actions/createOrder`
2. `POST /actions/approveOrder`
3. `POST /actions/shipOrder`
4. `POST /orders/query`

## Test

```bash
cd examples/node/prophet_example_express_prisma
export DATABASE_URL="file:./dev.db"
npm run prisma:generate
npm run prisma:push
npm run build
npm run test:integration
```
