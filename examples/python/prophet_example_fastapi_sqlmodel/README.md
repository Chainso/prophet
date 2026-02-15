# Prophet Example: FastAPI + SQLModel

This example demonstrates Prophet generation for the `python_fastapi_sqlmodel` stack.

## Generate

```bash
cd examples/python/prophet_example_fastapi_sqlmodel
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
.venv/bin/uvicorn src.app:app --host 0.0.0.0 --port 8080
```

Try:

1. `POST /actions/createOrder`
2. `POST /actions/approveOrder`
3. `POST /actions/shipOrder`
4. `POST /orders/query`
