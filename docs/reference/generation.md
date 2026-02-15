# Generation Reference

## Output Roots

- `.prophet/` for internal IR/cache/baselines
- `gen/` for generated artifacts

## Core Generated Artifacts

- `.prophet/ir/current.ir.json`
- `.prophet/cache/generation.json`
- `gen/sql/schema.sql`
- `gen/openapi/openapi.yaml`
- `gen/manifest/generated-files.json`
- `gen/manifest/extension-hooks.json`

## Extension Hook Safety

- Generate hooks with `prophet gen`.
- Inspect hooks with `prophet hooks` or `prophet hooks --json`.
- Implement extension code outside generated ownership paths.
- Re-running generation refreshes hook metadata but must not overwrite user-owned extension implementations.

## Spring Stack Outputs

- `gen/spring-boot/build.gradle.kts`
- `gen/spring-boot/src/main/java/**`
- `gen/spring-boot/src/main/resources/**`

## Node/Express Stack Outputs

- `gen/node-express/package.json`
- `gen/node-express/tsconfig.json`
- `gen/node-express/src/generated/**`
- `gen/manifest/node-autodetect.json` (when Node autodetection is active)

Prisma stack adds:
- `gen/node-express/prisma/schema.prisma`
- `gen/node-express/src/generated/prisma-adapters.ts`
- generated Prisma repositories implement list/query/getById/save against `PrismaClient`

TypeORM stack adds:
- `gen/node-express/src/generated/typeorm-entities.ts`
- `gen/node-express/src/generated/typeorm-adapters.ts`
- generated TypeORM repositories implement list/query/getById/save against `DataSource`

Mongoose stack adds:
- `gen/node-express/src/generated/mongoose-models.ts`
- `gen/node-express/src/generated/mongoose-adapters.ts`
- generated Mongoose repositories implement list/query/getById/save against `Model` bindings

## Migration Outputs

- Flyway init: `gen/migrations/flyway/V1__prophet_init.sql`
- Liquibase init: `gen/migrations/liquibase/prophet/0001-init.sql`
- Delta (when baseline differs):
  - `gen/migrations/flyway/V2__prophet_delta.sql`
  - `gen/migrations/liquibase/prophet/0002-delta.sql`
  - `gen/migrations/delta/report.json`

## Ownership Model

Generated paths are tool-owned.
Do not hand-edit generated files; change ontology/config/generator and regenerate.
