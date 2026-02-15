# Python Quickstart (FastAPI, Flask, Django)

Use this guide for Python framework integrations with generated typed contracts and ORM adapters.

## 1. Configure `prophet.yaml`

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

If `generation.stack` is omitted, Prophet can auto-detect based on Python dependency and project signals.

## 2. Generate

```bash
prophet validate
prophet gen
```

Generated Python runtime files are written under:
- `gen/python/src/generated/`

## 3. Create Runtime Environment

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 4. Implement Action Handlers

Generated handlers are placeholders that raise until replaced.
Implement your domain logic against generated contracts from:
- `gen/python/src/generated/action_handlers.py`
- `gen/python/src/generated/actions.py`

## 5. Wire DB Session/Connection in App Code

Prophet generates ORM models and repository adapters, but application-owned code manages:
- SQLAlchemy session lifecycle
- SQLModel session lifecycle
- Django settings/database configuration

## 6. Optional Event Emitter Integration

Generated action services emit action output events through the generated emitter interface.
Provide your own implementation to publish externally. Default no-op emitter is used otherwise.

## 7. Run Tests with Framework Test Clients

Use `pytest` and framework-native test clients (no embedded uvicorn in tests):

```bash
PYTHONPATH=src:gen/python/src .venv/bin/python -m pytest -q tests
```

Django:

```bash
DJANGO_SETTINGS_MODULE=<your_settings_module> \
PYTHONPATH=src:gen/python/src \
.venv/bin/python -m pytest -q tests
```

## Reference

- Python generation details: [Python Reference](../reference/python.md)
- DSL details: [DSL](../reference/dsl.md)
