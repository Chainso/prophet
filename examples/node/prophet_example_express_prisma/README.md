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
npm run dev
```

The generated default handlers throw until you implement action handlers.
