# Prophet

Prophet is the ontology compiler kernel behind Seer.

## Current State

This repository currently contains:
- `prophet.ttl` (base ontology)
- `docs/prophet-spec-v0.1.md` (product and technical contracts)
- `docs/prophet-dsl-v0.1.md` (DSL language reference and examples)
- `docs/prophet-spring-boot-golden-stack-v0.1.md` (deep integration contract)
- `docs/prophet-jpa-mapping-v0.1.md` (ontology-to-database/JPA translation rules)
- `prophet-cli/` Python package for the CLI (`prophet_cli`)
- `./prophet` root launcher script (local convenience wrapper)
- `ontology/local/main.prophet` (reference DSL example)
- `examples/java` standalone Spring Boot example app scaffold

## CLI Flow

```bash
python3 -m venv .venv --system-site-packages
.venv/bin/pip install --no-build-isolation -e ./prophet-cli

./prophet init
./prophet validate
./prophet plan
./prophet gen --wire-gradle
./prophet clean
./prophet version check --against .prophet/baselines/main.ir.json
```

## Notes

- `gen/` is tool-owned and should be regenerated, not hand-edited.
- `id` values in ontology definitions are immutable compatibility anchors.
- Breaking/additive classification rules are defined in `docs/prophet-spec-v0.1.md`.
- v0.1 golden runtime integration target is Spring Boot.
- In v0.1 codegen, actions are generated as direct API endpoints (`/actions/*`).
- Action API payloads come from DSL `actionInput`/`actionOutput` contracts.
- Generated action endpoints delegate to user-provided Spring handler beans.
- DSL fields support scalar and list types (for example `string[]` or `list(string)`).
- DSL also supports reusable `struct` types for non-entity nested payloads.
- Event ingestion/dispatch remains a Seer platform concern, not Spring codegen output.
- `./prophet generate` also syncs generated artifacts into `examples/java/prophet_example_spring` when that project exists.
