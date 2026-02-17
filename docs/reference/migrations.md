# Migrations Reference

## Generated Migration Targets

- Flyway SQL under `gen/migrations/flyway/`
- Liquibase changelogs under `gen/migrations/liquibase/`

## Baseline-Aware Delta Generation

When current IR differs from baseline IR:
- generate Flyway delta SQL (`V2__prophet_delta.sql`)
- generate Liquibase delta SQL (`0002-delta.sql`)
- generate delta report (`gen/migrations/delta/report.json`)
- include display-index updates (`idx_<table>_display`) when `key display` declarations are added, removed, or changed

## Delta Safety Signals

Generated delta artifacts include safety hints for operations like:
- destructive schema changes
- backfill-required changes
- manual-review-required changes

## Runtime Auto-Detection

For Spring projects, Prophet inspects host Gradle config:
- if Flyway is detected, runtime Flyway resource wiring can be applied
- if Liquibase is detected, runtime Liquibase resource wiring can be applied
- if not detected, migration files are still generated under `gen/migrations/**`

## Operational Advice

- Always review delta SQL before production use.
- Treat rename-like changes as manual migration planning unless explicitly verified.
