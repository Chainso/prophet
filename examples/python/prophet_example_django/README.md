# Prophet Example: Django + Django ORM

This example demonstrates Prophet generation for the `python_django_django_orm` stack.

## Generate

```bash
cd examples/python/prophet_example_django
../../../.venv/bin/prophet gen
```

Generated output includes:

- `gen/python/src/generated/**`
- `gen/openapi/openapi.yaml`
- `gen/sql/schema.sql`

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
../../../.venv/bin/prophet gen
DJANGO_SETTINGS_MODULE=prophet_example_django.settings \
PYTHONPATH=src:gen/python/src \
.venv/bin/python manage.py runserver 0.0.0.0:8080
```

Try:

1. `POST /actions/createOrder`
2. `POST /actions/approveOrder`
3. `POST /actions/shipOrder`
4. `POST /orders/query`
