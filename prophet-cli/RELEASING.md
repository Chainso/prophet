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
../../../.venv/bin/prophet gen --wire-gradle
./gradlew :prophet_generated:compileJava compileJava
```

## 3. Build Artifacts

From repository root:

```bash
python3 -m build prophet-cli
```

Artifacts are written under `prophet-cli/dist/`.

## 4. Update Changelog

Add a new entry in `prophet-cli/CHANGELOG.md` for the release version and summarize notable changes.

## 5. Tag and Publish

- Create annotated git tag: `vX.Y.Z`
- Push commit + tag
- Publish wheel/sdist to your package index workflow
