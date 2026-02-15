# Prophet Example: Express + Mongoose

This example demonstrates Prophet generation for the `node_express_mongoose` stack.

## Prerequisites

- A reachable MongoDB instance (local or remote)
- `MONGO_URL` set when not using the default

Default local URL used by the example:

```bash
mongodb://127.0.0.1:27017/prophet_example_mongoose
```

## Generate

```bash
cd examples/node/prophet_example_express_mongoose
../../../.venv/bin/prophet gen
```

Generated output includes:

- `gen/node-express/src/generated/**`
- `gen/node-express/src/generated/mongoose-models.ts`
- `gen/node-express/src/generated/mongoose-adapters.ts`
- `gen/openapi/openapi.yaml`

## Run

```bash
npm ci
export MONGO_URL="mongodb://127.0.0.1:27017/prophet_example_mongoose"
npm run dev
```

The example wires concrete action handlers (`createOrder`, `approveOrder`, `shipOrder`) in `src/server.ts`.
Try:

1. `POST /actions/createOrder`
2. `POST /actions/approveOrder`
3. `POST /actions/shipOrder`
4. `POST /orders/query`
