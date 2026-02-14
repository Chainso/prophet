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

## Spring Stack Outputs

- `gen/spring-boot/build.gradle.kts`
- `gen/spring-boot/src/main/java/**`
- `gen/spring-boot/src/main/resources/**`

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
