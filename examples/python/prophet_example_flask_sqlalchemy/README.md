# Prophet Example: Flask + SQLAlchemy

This example is a runnable Flask app generated from a Prophet ontology for a small commerce workflow.

## What This Example Models

A commerce domain with:
- users and orders
- order lifecycle transitions (`created -> approved -> shipped`)
- actions for create/approve/ship
- signal and transition events
- UI-facing display labels via DSL `name "..."` metadata

## What This Example Showcases

- `python_flask_sqlalchemy` generation end-to-end
- generated Python contracts, query/action routes, and services
- generated SQLAlchemy models + adapters
- OpenAPI + SQL generation from one ontology

## Files to Inspect

- DSL source: `ontology/local/main.prophet`
- App wiring + handlers: `src/app.py`
- Generated Python artifacts: `gen/python/src/generated/`
- Generated SQLAlchemy models: `gen/python/src/generated/sqlalchemy_models.py`
- Generated OpenAPI: `gen/openapi/openapi.yaml`

## Generate

```bash
cd examples/python/prophet_example_flask_sqlalchemy
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
```

## Run

```bash
cd examples/python/prophet_example_flask_sqlalchemy
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
FLASK_APP=src.app:app .venv/bin/flask run --host 0.0.0.0 --port 8080
```

## Try

1. `POST /actions/createOrder`
2. `POST /actions/approveOrder`
3. `POST /actions/shipOrder`
4. `POST /orders/query`

## Test

```bash
cd examples/python/prophet_example_flask_sqlalchemy
PYTHONPATH=$(git rev-parse --show-toplevel)/prophet-lib/python/src:src:gen/python/src \
.venv/bin/python -m pytest -q tests
```
