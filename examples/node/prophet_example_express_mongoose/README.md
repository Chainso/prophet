# Prophet Example: Express + Mongoose

This example is a runnable Node/Express app generated from a Prophet ontology for a small commerce workflow.

## What This Example Models

A commerce domain with:
- users and orders
- order lifecycle transitions (`created -> approved -> shipped`)
- actions for create/approve/ship
- signal and transition events
- UI-facing display labels via DSL `name "..."` metadata

## What This Example Showcases

- `node_express_mongoose` generation end-to-end
- generated typed contracts, routes, and service seams
- generated Mongoose models + adapters
- OpenAPI generation from one ontology

## Files to Inspect

- DSL source: `ontology/local/main.prophet`
- App wiring + handlers: `src/server.ts`
- Generated Node artifacts: `gen/node-express/src/generated/`
- Generated Mongoose models: `gen/node-express/src/generated/mongoose-models.ts`
- Generated OpenAPI: `gen/openapi/openapi.yaml`

## Prerequisites

- A reachable MongoDB instance
- `MONGO_URL` set when not using the default

Default local URL:

```bash
mongodb://127.0.0.1:27017/prophet_example_mongoose
```

## Generate

```bash
cd examples/node/prophet_example_express_mongoose
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
```

## Run

```bash
cd examples/node/prophet_example_express_mongoose
npm ci
export MONGO_URL="mongodb://127.0.0.1:27017/prophet_example_mongoose"
npm run dev
```

## Try

1. `POST /actions/createOrder`
2. `POST /actions/approveOrder`
3. `POST /actions/shipOrder`
4. `POST /orders/query`

## Test

```bash
cd examples/node/prophet_example_express_mongoose
npm run build
npm run test:integration
```
