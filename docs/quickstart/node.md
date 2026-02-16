# Node Quickstart (Express)

Use this guide for Express projects using Prisma, TypeORM, or Mongoose.

## 1. Configure `prophet.yaml`

Prisma:

```yaml
generation:
  stack:
    id: node_express_prisma
  targets: [sql, openapi, node_express, prisma, manifest]
```

TypeORM:

```yaml
generation:
  stack:
    id: node_express_typeorm
  targets: [sql, openapi, node_express, typeorm, manifest]
```

Mongoose:

```yaml
generation:
  stack:
    id: node_express_mongoose
  targets: [openapi, node_express, mongoose, manifest]
```

If you omit `generation.stack`, Prophet can auto-detect from your `package.json` dependencies.

## 2. Generate

```bash
prophet validate
prophet gen
```

Generated Node runtime files are written under:
- `gen/node-express/src/generated/`

## 3. Install Runtime Dependencies

Install your normal project dependencies:

```bash
npm install
```

Prisma stacks also need:

```bash
npm run prisma:generate
npm run prisma:push
```

## 4. Implement Action Handlers

Generated handler classes throw by default. Replace them with app-owned implementations using generated contracts from:
- `gen/node-express/src/generated/action-handlers.ts`
- `gen/node-express/src/generated/actions.ts`

## 5. Wire Persistence at Application Boundaries

Prophet generates adapters and contracts, but your app owns connection setup:
- Prisma: instantiate `PrismaClient`
- TypeORM: instantiate `DataSource`
- Mongoose: establish `mongoose.connect(...)`

## 6. Optional Event Publisher Integration

Generated action services publish event wire envelopes through the generated `EventPublisher` interface.
Provide a custom publisher implementation to publish externally. Default no-op publisher is used if none is provided.

## 7. Run Build and Tests

```bash
npm run build
npm run test:integration
prophet check --show-reasons
```

## Reference

- Node generation details: [Node/Express Reference](../reference/node-express.md)
- Config details: [Config](../reference/config.md)
