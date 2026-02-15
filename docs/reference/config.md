# Config Reference (`prophet.yaml`)

## Minimal Config

```yaml
project:
  ontology_file: ontology/local/main.prophet

generation:
  out_dir: gen
  targets: [sql, openapi, spring_boot, flyway, liquibase]
  stack:
    id: java_spring_jpa
  spring_boot:
    base_package: com.example.prophet
    boot_version: 3.3

compatibility:
  baseline_ir: .prophet/baselines/main.ir.json
  strict_enums: false
```

## `project`

- `ontology_file`: path to the ontology DSL file

## `generation`

- `out_dir`: output root (default: `gen`)
- `targets`: enabled generators
  - `sql`
  - `openapi`
  - `spring_boot`
  - `flyway`
  - `liquibase`
  - `node_express`
  - `prisma`
  - `typeorm`
  - `manifest`
- `stack`: stack selection
  - `id: java_spring_jpa`
  - `id: node_express_prisma`
  - `id: node_express_typeorm`
  - or tuple form (`language/framework/orm`)
- `spring_boot.base_package`: Java package base
- `spring_boot.boot_version`: host Spring Boot line
- `node_express.prisma.provider`: Prisma datasource provider
  - supported: `sqlite`, `postgresql`, `mysql`, `sqlserver`, `cockroachdb`
  - default: `sqlite`

Generated Spring package root is:
- `<base_package>.<ontology_name>`

Node autodetection notes:
- If no explicit stack is set, Prophet inspects `package.json` and lockfiles to auto-select Node Express stacks.
- For Node projects, default Java init targets are automatically rewritten to Node targets when stack autodetection succeeds.
- Autodetection fails closed when a safe Node stack cannot be inferred; set `generation.stack.id` explicitly in that case.

Node DB configuration notes:
- Prisma stack:
  - provider can be configured via `generation.node_express.prisma.provider`
  - connection URL is read at runtime from `DATABASE_URL`
- TypeORM stack:
  - Prophet generates entities + repository adapters
  - actual database connection is owned by your application `DataSource` setup (host/port/db/user/password/ssl/pool)
  - no TypeORM connection keys are currently read from `prophet.yaml`

## `compatibility`

- `baseline_ir`: baseline IR path used by `plan/check/version check`
- `strict_enums`: enum strictness toggle in validation/comparison
