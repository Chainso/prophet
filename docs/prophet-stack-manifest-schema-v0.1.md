# Prophet Stack Manifest Schema v0.1

This document defines the schema used to declare generation stacks and capabilities in `prophet_cli.codegen.stack_manifest`.

## Purpose

The stack manifest is the source of truth for:

1. Supported stack IDs and language/framework/ORM tuples.
2. Capability declarations per stack.
3. Stack lifecycle status (`implemented` vs `planned`).
4. Default generation target sets per stack.

`prophet` validates this manifest at startup and fails fast on schema violations.

## Document Shape

Top-level keys:

1. `schema_version` (integer, currently `1`)
2. `capability_catalog` (non-empty list of unique capability strings)
3. `stacks` (non-empty list of stack entries)

Unknown or missing top-level keys are rejected.

## Stack Entry Shape

Required stack entry keys:

1. `id` (unique non-empty string)
2. `language` (non-empty string)
3. `framework` (non-empty string)
4. `orm` (non-empty string)
5. `status` (`implemented` or `planned`)
6. `description` (non-empty string)
7. `capabilities` (non-empty list of unique strings, each in `capability_catalog`)
8. `default_targets` (non-empty list of unique generation targets)

Optional stack entry keys:

1. `notes` (non-empty string when present)

Unknown keys are rejected.

## Validation Guarantees

The validator enforces:

1. Unique stack IDs.
2. Unique language/framework/ORM tuples.
3. Valid status values.
4. Capability values constrained to the catalog.
5. `default_targets` constrained to known generation targets:
   - `sql`
   - `openapi`
   - `spring_boot`
   - `flyway`
   - `liquibase`
   - `manifest`

## CLI Surfaces

Manifest data is surfaced through:

1. `prophet stacks`
2. `prophet stacks --json`

JSON output includes:

1. `schema_version`
2. `capability_catalog`
3. `stacks` entries with status, capabilities, description, default targets, and notes
