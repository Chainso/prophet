# Contributing (Developer)

## Setup

```bash
python3 -m venv .venv --system-site-packages
.venv/bin/pip install --no-build-isolation -e ./prophet-cli
.venv/bin/pip install build twine
```

## Expectations

- Keep generation deterministic
- Do not hand-edit generated files as source-of-truth changes
- Preserve compatibility semantics and ID-anchor behavior
- Update docs and tests alongside behavior changes

## Pull Request Checklist

1. Focused change scope
2. Python tests pass
3. Spring example validation passes
4. Node and Python example integration tests pass
5. Packaging checks pass
6. Docs updated

## Recommended Validation Commands

From repository root:

```bash
./scripts/test-all.sh
python3 -m build prophet-cli
python3 -m twine check prophet-cli/dist/*
```

## Open Items

Source of truth backlog:
- [CONTRIBUTING.md](../../CONTRIBUTING.md)
