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
6. Docs updated across all relevant surfaces

## Recommended Validation Commands

From repository root:

```bash
./scripts/test-all.sh
python3 -m build prophet-cli
python3 -m twine check prophet-cli/dist/*
```

Target-specific coverage (example for Turtle):

```bash
python3 -m unittest prophet-cli/tests/test_turtle_target.py -v
cd examples/turtle/prophet_example_turtle_minimal
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
cd $(git rev-parse --show-toplevel)
pyshacl -s prophet.ttl -d prophet.ttl examples/turtle/prophet_example_turtle_minimal/gen/turtle/ontology.ttl -e prophet.ttl --advanced --inference owlrl --format turtle
```

## Doc Surfaces for Generation Target Changes

If you add/change/remove generation targets, update at minimum:
- `README.md`
- `AGENTS.md`
- `prophet-cli/README.md`
- `docs/reference/config.md`
- `docs/reference/generation.md`
- `docs/reference/index.md`
- `docs/reference/examples.md`
- `docs/reference/turtle.md`
- `docs/quickstart/quickstart.md`
- `docs/developer/codegen-architecture.md`

## Open Items

Source of truth backlog:
- [CONTRIBUTING.md](../../CONTRIBUTING.md)
