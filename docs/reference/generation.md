# Generation Reference

## Output Roots

- `.prophet/` for internal IR/cache/baselines
- `gen/` for generated artifacts

## Core Generated Artifacts

- `.prophet/ir/current.ir.json`
- `.prophet/cache/generation.json`
- `gen/sql/schema.sql`
- `gen/openapi/openapi.yaml`
- `gen/turtle/ontology.ttl` (when `turtle` target is enabled)
- `gen/manifest/generated-files.json`
- `gen/manifest/extension-hooks.json`

Turtle details:
- [Turtle Target Reference](turtle.md)
- output is designed to conform to [`prophet.ttl`](../../prophet.ttl) and can be validated with `pyshacl`

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

## Python Stack Outputs

- `gen/python/pyproject.toml`
- `gen/python/src/generated/domain.py`
- `gen/python/src/generated/actions.py`
- `gen/python/src/generated/event_contracts.py`
- `gen/python/src/generated/events.py`
- `gen/python/src/generated/query.py`
- `gen/python/src/generated/persistence.py`
- `gen/python/src/generated/action_handlers.py`
- `gen/python/src/generated/action_service.py`
- `gen/manifest/python-autodetect.json` (when Python autodetection is active)

FastAPI stacks add:
- `gen/python/src/generated/fastapi_routes.py`

Flask stacks add:
- `gen/python/src/generated/flask_routes.py`

Django stack adds:
- `gen/python/src/generated/django_urls.py`
- `gen/python/src/generated/django_views.py`

SQLAlchemy stacks add:
- `gen/python/src/generated/sqlalchemy_models.py`
- `gen/python/src/generated/sqlalchemy_adapters.py`

SQLModel stacks add:
- `gen/python/src/generated/sqlmodel_models.py`
- `gen/python/src/generated/sqlmodel_adapters.py`

Django ORM stack adds:
- `gen/python/src/generated/django_models.py`
- `gen/python/src/generated/django_adapters.py`

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
