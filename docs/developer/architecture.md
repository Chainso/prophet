# Architecture

## Compiler Pipeline

1. Parse DSL into in-memory model
2. Validate semantic rules
3. Build canonical IR
4. Execute target generation pipeline
5. Emit manifests/cache metadata for deterministic regeneration

## Primary Modules

- `prophet_cli/core/`
  - parser, validation, config, compatibility, IR model
- `prophet_cli/codegen/`
  - generation contracts, stack manifest, pipeline, artifacts, cache
- `prophet_cli/targets/`
  - concrete stack generators (Java/Spring/JPA, Node/Express, Python frameworks)

## Design Constraints

- Deterministic output ordering
- Immutable ontology IDs as compatibility anchors
- Explicit ownership boundary between generated and user files
