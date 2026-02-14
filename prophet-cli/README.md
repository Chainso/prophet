# prophet-cli

`prophet-cli` is the tooling package for Prophet's ontology workflow:

1. Parse DSL (path configured via `project.ontology_file`)
2. Validate model semantics
3. Build canonical IR (`.prophet/ir/current.ir.json`) including versioned `query_contracts`
4. Generate deterministic artifacts (`gen/sql`, `gen/openapi`, `gen/migrations`, `gen/spring-boot`)
5. Check compatibility against baseline IR

## Install (editable)

From repo root:

```bash
python3 -m venv .venv --system-site-packages
.venv/bin/pip install --no-build-isolation -e ./prophet-cli
```

Run via venv script:

```bash
.venv/bin/prophet --help
```

## Commands

### `prophet init`
Creates starter `prophet.yaml` and internal `.prophet` directories.

```bash
prophet init
```

### `prophet validate`
Parses + validates ontology references, IDs, states/transitions, action contracts, list types, and action/event/trigger links.

```bash
prophet validate
```

### `prophet plan`
Computes deterministic file changes without writing files.

```bash
prophet plan
prophet plan --show-reasons
prophet plan --json
```

### `prophet check`
Runs a CI-style gate in one command:
1. ontology validation
2. generated output cleanliness check
3. compatibility/version-bump check against baseline IR

```bash
prophet check
prophet check --show-reasons
prophet check --json
prophet check --against .prophet/baselines/main.ir.json
```

`--json` emits structured diagnostics for CI bots and automation.

### `prophet stacks`
Lists supported stack ids, framework/ORM pairings, implementation status, and capability metadata.
Entries come from a schema-validated stack manifest.
Schema reference: `docs/prophet-stack-manifest-schema-v0.1.md`.

```bash
prophet stacks
prophet stacks --json
```

### `prophet hooks`
Lists generated extension hook surfaces from `gen/manifest/extension-hooks.json`.
Useful for wiring user-owned implementations against generated interfaces.
Safety/reference docs:
- `docs/prophet-extension-hooks-safety-v0.1.md`

```bash
prophet hooks
prophet hooks --json
```

### `prophet generate` / `prophet gen`
Writes generated artifacts and current IR.

```bash
prophet generate
prophet gen
prophet gen --skip-unchanged
```

Also syncs generated Spring artifacts into `examples/java/prophet_example_spring` when present.

Stack selection is configured in `prophet.yaml`:

```yaml
generation:
  stack:
    id: java_spring_jpa
```

Current generator implementation supports artifact generation for `java_spring_jpa`.
Other declared stacks are validated and reserved for upcoming target implementations.
Allowed `generation.stack` keys are: `id`, `language`, `framework`, `orm`.

Equivalent tuple form is also supported:

```yaml
generation:
  stack:
    language: java
    framework: spring_boot
    orm: jpa
```

Default generated targets:
- `sql`
- `openapi`
- `spring_boot`
- `flyway`
- `liquibase`
- `manifest` (generated file ownership + hashes)

When baseline IR differs from current IR, Prophet also emits delta migration artifacts:
- `gen/migrations/flyway/V2__prophet_delta.sql`
- `gen/migrations/liquibase/prophet/0002-delta.sql`
- `gen/migrations/delta/report.json`

Delta SQL includes safety flags and warnings (`destructive`, `backfill_required`, `manual_review`) as comments.
Delta report JSON includes:
- `summary` counts (`safe_auto_apply_count`, `manual_review_count`, `destructive_count`)
- structured `findings` entries with classification and optional suggestions
- heuristic rename hints (`object_rename_hint`, `column_rename_hint`) for manual migration planning

Generated ownership manifest:
- `gen/manifest/generated-files.json`
- includes stack metadata and deterministic hashes for generated outputs

Generated extension hook manifest:
- `gen/manifest/extension-hooks.json`
- lists generated extension points (for example action handler interfaces + default classes)

Spring runtime migration wiring is auto-detected from the host Gradle project:
- if Flyway dependency/plugin is present, Prophet syncs Flyway resources
- if Liquibase dependency/plugin is present, Prophet syncs Liquibase resources
- if neither is present, migration files are still generated under `gen/migrations/**` but not auto-wired into Spring runtime resources

### `prophet gen --wire-gradle`
Auto-wires the current Gradle project as a multi-module setup:
- adds `:prophet_generated` in `settings.gradle.kts`/`settings.gradle`
- maps it to `gen/spring-boot`
- adds app dependency `implementation(project(\":prophet_generated\"))` in `build.gradle.kts`

```bash
prophet gen --wire-gradle
```

Wiring is idempotent (safe to run repeatedly).

### `prophet generate --verify-clean`
CI mode. Fails if committed generated files differ from current generation.

```bash
prophet generate --verify-clean
```

### `prophet gen --skip-unchanged`
Skips no-op regeneration when the current config + IR signature matches the last successful generation cache.

- cache file: `.prophet/cache/generation.json`
- ignored when `--wire-gradle` is used
- incompatible with `--verify-clean`

```bash
prophet gen --skip-unchanged
```

### `prophet clean`
Removes generated artifacts from current project.

Default removals:
- `gen/`
- `.prophet/ir/current.ir.json`
- `.prophet/cache/generation.json`
- `src/main/java/<base_package>/<ontology_name>/generated`
- `src/main/resources/application-prophet.yml`
- `src/main/resources/schema.sql` (only if it looks generated)
- `src/main/resources/db/migration/V1__prophet_init.sql` (if generated)
- `src/main/resources/db/migration/V2__prophet_delta.sql` (if generated)
- `src/main/resources/db/changelog/**` Prophet-managed generated files, including `0002-delta.sql`
- Gradle multi-module wiring for `:prophet_generated` in `settings.gradle(.kts)` and `build.gradle(.kts)`

```bash
prophet clean
prophet clean --verbose
prophet clean --remove-baseline
prophet clean --keep-gradle-wire
```

### `prophet version check`
Compares current IR against baseline and reports compatibility + required bump.

```bash
prophet version check --against .prophet/baselines/main.ir.json
```

Compatibility rules used by CLI are documented in:
- `docs/prophet-compatibility-policy-v0.2.md`

## Expected Project Files

- `prophet.yaml`
- `<your ontology file>` (configured in `project.ontology_file`)
- `.prophet/baselines/main.ir.json`
- `.prophet/ir/current.ir.json` (generated)
- `gen/` (generated)

## DSL Notes

- Field types support scalars, custom types, object refs (`ref(User)`), lists (`string[]`, `list(string)`), and reusable `struct` types.
- Nested list types are supported (for example `string[][]`, `list(list(string))`).
- Description metadata supports both `description "..."` and `documentation "..."`.
- Object keys support field-level and object-level declarations:
  - `key primary`
  - `key primary (fieldA, fieldB)` (composite)
  - `key display (...)` (metadata marker)
- Generated Java record component order follows DSL field declaration order.
- Actions are not auto-implemented; generated endpoints call handler beans.
- Generated action services (`generated.actions.services.*`) are the API boundary used by controllers.
- Default generated services delegate to handler beans; generated default handler stubs throw `UnsupportedOperationException` until user handlers are provided.

## Config (`prophet.yaml`)

Required keys currently used by CLI:

```yaml
project:
  ontology_file: path/to/your-ontology.prophet
generation:
  out_dir: gen
  targets: [sql, openapi, spring_boot, flyway, liquibase]
  spring_boot:
    base_package: com.example.prophet
    boot_version: 3.3
compatibility:
  baseline_ir: .prophet/baselines/main.ir.json
  strict_enums: false
```

Note: generated Spring package root is `<base_package>.<ontology_name>`.

## Release Prep

- Release process: `prophet-cli/RELEASING.md`
- Changelog: `prophet-cli/CHANGELOG.md`
- Version sync is test-enforced between:
  - `prophet-cli/pyproject.toml` `[project].version`
  - `prophet-cli/src/prophet_cli/cli.py` `TOOLCHAIN_VERSION`

## Development Notes

- Entry point module: `src/prophet_cli/cli.py`
- Console script: `prophet`
- Root `./prophet` is a launcher wrapper for local repo usage.
- No-op benchmark script: `scripts/benchmark_noop_generation.py`
- Spring query APIs generated by v0.1 include:
  - `GET /<objects>/{id}` for single-field primary keys
  - `GET /<objects>/{k1}/{k2}/...` for composite primary keys
  - `GET /<objects>` with pagination/sort only
  - `POST /<objects>/query` with typed filter DSL (`eq`, `in`, `gte`, `lte`, `contains`) for all filtering
  - list responses returned as generated `*ListResponse` DTOs (no raw Spring `Page` payload)
- Generated Spring query layer now uses dedicated `generated.mapping.*DomainMapper` classes for entity-to-domain mapping.
- Example Spring app includes both `h2` (default) and `postgres` runtime profiles with context tests for both.

## Contributing

- See root contribution guide: `CONTRIBUTING.md`
- Open contributor backlog: `CONTRIBUTING.md` (`Open Items`)
