# Prophet Extension Hooks Safety v0.1

This document defines the regeneration-safety contract for extension code around generated Prophet artifacts.

## Scope

Prophet generates extension hook metadata in:

1. `gen/manifest/extension-hooks.json`

and exposes it via:

1. `prophet hooks`
2. `prophet hooks --json`

## Ownership Model

1. Prophet owns generated files under `gen/**`.
2. Prophet-managed sync in the Spring example owns:
   - `src/main/java/<base_package>/generated/**`
   - `src/main/resources/application-prophet.yml`
   - generated migration resource files when present
3. User extension code is expected to live outside generated ownership paths (for example `src/main/java/.../extensions/**`).

## Regeneration Safety Guarantees

When rerunning `prophet gen`:

1. User-owned extension files outside managed generated paths are not overwritten.
2. Generated extension metadata is refreshed deterministically.
3. Regeneration preserves extension hook identifiers (`action_id`, `action_name`) unless ontology semantics change.

## Recommended Workflow

1. Run `prophet gen`.
2. Inspect hooks with `prophet hooks --json`.
3. Implement user handlers/services in user-owned packages.
4. Re-run `prophet gen` as ontology evolves; update implementations only when hook contracts change.

## Test Coverage

This safety contract is covered by CLI integration tests that:

1. Create user-owned extension files in a synced example project.
2. Run repeated `prophet gen` cycles.
3. Assert user extension files remain byte-for-byte unchanged.
