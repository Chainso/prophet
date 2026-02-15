# CLI Reference

## Core Commands

- `prophet init`
- `prophet validate`
- `prophet plan [--show-reasons] [--json]`
- `prophet gen` (`prophet generate` alias)
- `prophet check [--show-reasons] [--json]`
- `prophet version check --against <baseline>`
- `prophet clean`
- `prophet stacks [--json]`
- `prophet hooks [--json]`

## `prophet gen` Flags

- `--wire-gradle`: add/sync `:prophet_generated` submodule wiring
- `--skip-unchanged`: skip no-op generation using `.prophet/cache/generation.json`
- `--verify-clean`: fail if committed/generated files drift from current generator output

Node stacks also apply package.json script auto-wiring for:
- `prophet:gen`
- `prophet:check`
- `prophet:validate`

## `prophet clean` Flags

- `--verbose`
- `--remove-baseline`
- `--keep-gradle-wire`

## JSON Modes

- `prophet plan --json`
- `prophet check --json`
- `prophet stacks --json`
- `prophet hooks --json`

These are intended for CI and automation consumers.

## Help

```bash
prophet --help
prophet <subcommand> --help
```

For advanced CLI behavior and examples:
- [prophet-cli/README.md](../../prophet-cli/README.md)
