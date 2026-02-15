# Releasing

## Version Anchors

Update both:
- [prophet-cli/pyproject.toml](../../prophet-cli/pyproject.toml) -> `[project].version`
- [prophet-cli/src/prophet_cli/cli.py](../../prophet-cli/src/prophet_cli/cli.py) -> `TOOLCHAIN_VERSION`

## Validation Before Tag

```bash
python3 -m unittest discover -s prophet-cli/tests -p 'test_*.py' -v
cd examples/java/prophet_example_spring
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen --wire-gradle
$(git rev-parse --show-toplevel)/.venv/bin/prophet check --show-reasons
./gradlew test
```

## Build + Metadata Checks

```bash
python3 -m build prophet-cli
python3 -m twine check prophet-cli/dist/*
```

## Cut Release

1. update changelog
2. commit
3. create annotated tag (`vX.Y.Z`)
4. push commit + tag

Tag push triggers PyPI publish workflow.

## Detailed Runbook

- [prophet-cli/RELEASING.md](../../prophet-cli/RELEASING.md)
- [prophet-lib Runtime Runbook](prophet-lib-release.md)
