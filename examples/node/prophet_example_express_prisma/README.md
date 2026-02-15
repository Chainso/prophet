# Prophet Example: Express + Prisma

This example demonstrates Prophet generation for the `node_express_prisma` stack.

## Generate

```bash
cd examples/node/prophet_example_express_prisma
../../../.venv/bin/prophet gen
```

Generated output includes:

- `gen/node-express/src/generated/**`
- `gen/node-express/prisma/schema.prisma`
- `gen/openapi/openapi.yaml`
- `gen/sql/schema.sql`

## Run

```bash
npm install
export DATABASE_PROVIDER=sqlite
export DATABASE_URL="file:./dev.db"
npm run prisma:generate
npm run prisma:push
npm run dev
```

The example already wires concrete action handlers (`createOrder`, `approveOrder`, `shipOrder`) in `src/server.ts`.
Try:

1. `POST /actions/createOrder`
2. `POST /actions/approveOrder`
3. `POST /actions/shipOrder`
4. `POST /orders/query`
