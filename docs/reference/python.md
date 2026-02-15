# Python Reference

## Supported Stacks

- `python_fastapi_sqlalchemy`
- `python_fastapi_sqlmodel`
- `python_flask_sqlalchemy`
- `python_flask_sqlmodel`
- `python_django_django_orm`

All Python stacks share one generated contract surface (domain, actions, events, query filters, repositories) and compose framework + ORM-specific renderers.

## Generated Artifacts

With `generation.targets` containing `python`:

- `gen/python/pyproject.toml`
- `gen/python/src/generated/domain.py`
- `gen/python/src/generated/actions.py`
- `gen/python/src/generated/event_contracts.py`
- `gen/python/src/generated/events.py`
- `gen/python/src/generated/query.py`
- `gen/python/src/generated/persistence.py`
- `gen/python/src/generated/action_handlers.py`
- `gen/python/src/generated/action_service.py`

Framework targets add:

- FastAPI (`fastapi` target): `gen/python/src/generated/fastapi_routes.py`
- Flask (`flask` target): `gen/python/src/generated/flask_routes.py`
- Django (`django` target): `gen/python/src/generated/django_urls.py`, `gen/python/src/generated/django_views.py`

ORM targets add:

- SQLAlchemy (`sqlalchemy` target): `gen/python/src/generated/sqlalchemy_models.py`, `gen/python/src/generated/sqlalchemy_adapters.py`
- SQLModel (`sqlmodel` target): `gen/python/src/generated/sqlmodel_models.py`, `gen/python/src/generated/sqlmodel_adapters.py`
- Django ORM (`django_orm` target): `gen/python/src/generated/django_models.py`, `gen/python/src/generated/django_adapters.py`

## Auto-Detection

Prophet inspects Python project signals and writes:

- `gen/manifest/python-autodetect.json`

Signals include:

- `pyproject.toml` dependencies
- `requirements*.txt`
- `manage.py` (Django signal)
- lockfile hints (`poetry.lock`, `uv.lock`, `Pipfile.lock`)

When stack config is not explicit, Prophet can auto-select one of the five Python stacks above.
Autodetection fails closed for ambiguous framework signals or missing ORM signals.

## Action and Event Behavior

- Generated action endpoints are mounted per framework.
- Generated action service emits action-output events through `EventEmitter`.
- `EventEmitterNoOp` is provided for zero-config local wiring.
- Default action handler implementations raise `NotImplementedError` until replaced by user code.

## Query Behavior

For each object query contract:

- list endpoint
- get-by-id endpoint
- typed filter endpoint

Typed filter dataclasses are generated in `query.py`, and repository adapters translate operators (`eq`, `in`, `contains`, `gte`, `lte`) to ORM-specific queries.

## Recommended Targets

FastAPI + SQLAlchemy:

```yaml
generation:
  stack:
    id: python_fastapi_sqlalchemy
  targets: [sql, openapi, python, fastapi, sqlalchemy, manifest]
```

FastAPI + SQLModel:

```yaml
generation:
  stack:
    id: python_fastapi_sqlmodel
  targets: [sql, openapi, python, fastapi, sqlmodel, manifest]
```

Flask + SQLAlchemy:

```yaml
generation:
  stack:
    id: python_flask_sqlalchemy
  targets: [sql, openapi, python, flask, sqlalchemy, manifest]
```

Flask + SQLModel:

```yaml
generation:
  stack:
    id: python_flask_sqlmodel
  targets: [sql, openapi, python, flask, sqlmodel, manifest]
```

Django + Django ORM:

```yaml
generation:
  stack:
    id: python_django_django_orm
  targets: [sql, openapi, python, django, django_orm, manifest]
```
