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

The generated default handlers throw until you implement action handlers.
