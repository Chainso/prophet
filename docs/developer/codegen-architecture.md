# Codegen Architecture

## Stack Manifest

Supported stacks are declared in a schema-validated manifest contract.

Current implemented stacks:
- `java_spring_jpa`
- `node_express_prisma`
- `node_express_typeorm`

Planned stacks can exist in manifest as non-implemented entries for forward visibility and validation.

Manifest contract requirements include:
- top-level schema version
- capability catalog
- stack tuple identity (`id`, `language`, `framework`, `orm`)
- status (`implemented` or `planned`)
- capability declarations per stack
- default generation targets

Code location:
- [prophet-cli/src/prophet_cli/codegen/stack_manifest.py](../../prophet-cli/src/prophet_cli/codegen/stack_manifest.py)

## Generation Pipeline

1. Resolve stack specification
2. Build generation context
3. Route to stack generator
4. Aggregate outputs
5. Write outputs + managed-file manifest
6. Remove stale managed files

## Ownership and Safety

- Generated files are tracked in `gen/manifest/generated-files.json`
- Extension points are tracked in `gen/manifest/extension-hooks.json`
- Regeneration must not overwrite user-owned extension implementations

## Performance

No-op generation can be skipped via cache signature (`prophet gen --skip-unchanged`).
