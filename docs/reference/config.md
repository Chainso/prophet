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
  - `manifest`
- `stack`: stack selection
  - `id: java_spring_jpa`
  - or tuple form (`language/framework/orm`)
- `spring_boot.base_package`: Java package base
- `spring_boot.boot_version`: host Spring Boot line

Generated Spring package root is:
- `<base_package>.<ontology_name>`

## `compatibility`

- `baseline_ir`: baseline IR path used by `plan/check/version check`
- `strict_enums`: enum strictness toggle in validation/comparison
