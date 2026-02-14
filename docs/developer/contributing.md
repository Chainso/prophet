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
4. Packaging checks pass
5. Docs updated

## Open Items

Source of truth backlog:
- `CONTRIBUTING.md`
