# Node/Express Reference

## Supported Stacks

- `node_express_prisma`
- `node_express_typeorm`

Both stacks generate a shared Express runtime surface and stack-specific ORM artifacts.

## Generated Artifacts

With `generation.targets` containing `node_express`:

- `gen/node-express/src/generated/domain.ts`
- `gen/node-express/src/generated/actions.ts`
- `gen/node-express/src/generated/event-contracts.ts`
- `gen/node-express/src/generated/validation.ts`
- `gen/node-express/src/generated/persistence.ts`
- `gen/node-express/src/generated/action-handlers.ts`
- `gen/node-express/src/generated/action-service.ts`
- `gen/node-express/src/generated/action-routes.ts`
- `gen/node-express/src/generated/query.ts`
- `gen/node-express/src/generated/query-routes.ts`
- `gen/node-express/src/generated/events.ts`
- `gen/node-express/src/generated/index.ts`

Prisma-only (`prisma` target):

- `gen/node-express/prisma/schema.prisma`
- `gen/node-express/src/generated/prisma-adapters.ts`

TypeORM-only (`typeorm` target):

- `gen/node-express/src/generated/typeorm-entities.ts`
- `gen/node-express/src/generated/typeorm-adapters.ts`

## Auto-Detection

Prophet auto-detects Node project signals and writes a detection report:

- `gen/manifest/node-autodetect.json`

Signals include:

- package manager lock file (`npm`, `pnpm`, `yarn`, `bun`)
- `package.json` dependencies (`express`, `@prisma/client`, `typeorm`)
- module mode (`type: module` / `commonjs`)
- tsconfig presence
- candidate app entrypoint

When no explicit stack is configured, Prophet can auto-select:

- `node_express_prisma`
- `node_express_typeorm`

If both Prisma and TypeORM are detected, Prophet reports ambiguity and expects explicit config.
Autodetect now fails closed when Express is detected but a safe ORM stack cannot be inferred.

## Node Auto-Wiring

On `prophet gen` for Node stacks, Prophet adds scripts to host `package.json` when missing:

- `prophet:gen`
- `prophet:check`
- `prophet:validate`

`prophet clean` removes those scripts only when they still match Prophet defaults.

## Action and Event Behavior

- Generated action routes are available under `/actions/<actionName>`.
- Generated action service emits action output events by default through `GeneratedEventEmitter`.
- A `GeneratedEventEmitterNoOp` is provided for zero-config integration.
- Default handler stubs throw until replaced by user-owned implementations.

## Query Behavior

For each object query contract:

- list route: `GET <list_path>`
- get-by-id route: `GET <get_by_id_path>`
- typed filter route: `POST <typed_query_path>`

Typed filter interfaces are generated in `query.ts`.
Filter operators are generated per-field from the ontology query contract (not as a global superset).

## Repository Integrations

Prisma generated repositories:

- constructor expects `PrismaClient`
- generated methods implement paging, typed filtering, `getById`, and `save` via `upsert`
- Prisma schema includes object refs, state column (`current_state`), and supports composite primary keys
- datasource provider/url are driven by `DATABASE_PROVIDER` and `DATABASE_URL`

TypeORM generated repositories:

- constructor expects `DataSource`
- generated entities include columns, relations, and state column (`current_state`)
- generated methods implement paging, typed filtering, `getById`, and `save`
- query filtering is translated through `QueryBuilder`

## Recommended Targets

Prisma stack:

```yaml
generation:
  stack:
    id: node_express_prisma
  targets: [sql, openapi, node_express, prisma, manifest]
```

TypeORM stack:

```yaml
generation:
  stack:
    id: node_express_typeorm
  targets: [sql, openapi, node_express, typeorm, manifest]
```
