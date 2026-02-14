# Releasing prophet-cli

This document defines the release-prep flow for `prophet-cli`.

## 1. Bump Versions

Update both version anchors to the same value:

- `prophet-cli/pyproject.toml` -> `[project].version`
- `prophet-cli/src/prophet_cli/cli.py` -> `TOOLCHAIN_VERSION`

## 2. Run Validation

From repository root:

```bash
python3 -m unittest discover -s prophet-cli/tests -p 'test_*.py' -v
cd examples/java/prophet_example_spring
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen --wire-gradle
$(git rev-parse --show-toplevel)/.venv/bin/prophet check --show-reasons
./gradlew :prophet_generated:compileJava compileJava
./gradlew test
```

The GitHub Actions workflow (`.github/workflows/ci.yml`) should also be green before tagging.

## 3. Build Artifacts

From repository root:

```bash
python3 -m build prophet-cli
python3 -m twine check prophet-cli/dist/*
```

Artifacts are written under `prophet-cli/dist/`.

## 4. Update Changelog

Add a new entry in `prophet-cli/CHANGELOG.md` for the release version and summarize notable changes.

## 5. Tag and Publish

1. Create annotated git tag: `vX.Y.Z`
2. Push commit + tag
3. GitHub Actions publishes to PyPI via `.github/workflows/publish-pypi.yml`

The publish workflow expects PyPI trusted publishing to be configured for:
- Repository: `Chainso/prophet`
- Workflow file: `.github/workflows/publish-pypi.yml`
- Environment: `pypi`
