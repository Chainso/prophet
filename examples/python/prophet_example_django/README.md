# Prophet Example: Django + Django ORM

This example is a runnable Django app generated from a Prophet ontology for a small commerce workflow.

## What This Example Models

A commerce domain with:
- users and orders
- order lifecycle transitions (`created -> approved -> shipped`)
- actions for create/approve/ship
- signal and transition events
- UI-facing display labels via DSL `name "..."` metadata

## What This Example Showcases

- `python_django_django_orm` generation end-to-end
- generated Django URLs/views + service seams
- generated Django ORM models + adapters
- OpenAPI + SQL generation from one ontology

## Files to Inspect

- DSL source: `ontology/local/main.prophet`
- App wiring + handlers: `src/`
- Generated Python artifacts: `gen/python/src/generated/`
- Generated Django models: `gen/python/src/generated/django_models.py`
- Generated OpenAPI: `gen/openapi/openapi.yaml`

## Generate

```bash
cd examples/python/prophet_example_django
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
```

## Run

```bash
cd examples/python/prophet_example_django
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen
DJANGO_SETTINGS_MODULE=prophet_example_django.settings \
PYTHONPATH=src:gen/python/src \
.venv/bin/python manage.py runserver 0.0.0.0:8080
```

## Try

1. `POST /actions/createOrder`
2. `POST /actions/approveOrder`
3. `POST /actions/shipOrder`
4. `POST /orders/query`

## Test

```bash
cd examples/python/prophet_example_django
DJANGO_SETTINGS_MODULE=prophet_example_django.settings \
PYTHONPATH=$(git rev-parse --show-toplevel)/prophet-lib/python/src:src:gen/python/src \
.venv/bin/python -m pytest -q tests
```
