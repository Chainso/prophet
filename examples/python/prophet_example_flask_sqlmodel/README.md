# Prophet Example: Flask + SQLModel

This example demonstrates Prophet generation for the `python_flask_sqlmodel` stack.

## Generate

```bash
cd examples/python/prophet_example_flask_sqlmodel
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
FLASK_APP=src.app:app .venv/bin/flask run --host 0.0.0.0 --port 8080
```

Try:

1. `POST /actions/createOrder`
2. `POST /actions/approveOrder`
3. `POST /actions/shipOrder`
4. `POST /orders/query`
