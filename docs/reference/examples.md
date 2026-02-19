# Examples

This page is the sample catalog (runnable apps + Turtle target examples).

Use [Quickstart](../quickstart/quickstart.md) when integrating Prophet into your own project.
Each example directory includes a dedicated README describing the modeled domain and what that stack showcases.

## Java

### Spring + JPA

Path:
- [examples/java/prophet_example_spring](../../examples/java/prophet_example_spring)
- [README](../../examples/java/prophet_example_spring/README.md)

Run:

```bash
cd examples/java/prophet_example_spring
prophet gen --wire-gradle
./gradlew test
./gradlew bootRun
```

## Node

### Express + Prisma

Path:
- [examples/node/prophet_example_express_prisma](../../examples/node/prophet_example_express_prisma)
- [README](../../examples/node/prophet_example_express_prisma/README.md)

Run:

```bash
cd examples/node/prophet_example_express_prisma
prophet gen
npm install
npm run prisma:generate
npm run prisma:push
npm run dev
```

### Express + TypeORM

Path:
- [examples/node/prophet_example_express_typeorm](../../examples/node/prophet_example_express_typeorm)
- [README](../../examples/node/prophet_example_express_typeorm/README.md)

Run:

```bash
cd examples/node/prophet_example_express_typeorm
prophet gen
npm install
npm run dev
```

### Express + Mongoose

Path:
- [examples/node/prophet_example_express_mongoose](../../examples/node/prophet_example_express_mongoose)
- [README](../../examples/node/prophet_example_express_mongoose/README.md)

Run:

```bash
cd examples/node/prophet_example_express_mongoose
prophet gen
npm install
MONGO_URL="mongodb://127.0.0.1:27017/prophet_example_mongoose" npm run dev
```

## Python

### FastAPI + SQLAlchemy

Path:
- [examples/python/prophet_example_fastapi_sqlalchemy](../../examples/python/prophet_example_fastapi_sqlalchemy)
- [README](../../examples/python/prophet_example_fastapi_sqlalchemy/README.md)

Run:

```bash
cd examples/python/prophet_example_fastapi_sqlalchemy
prophet gen
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=$(git rev-parse --show-toplevel)/prophet-lib/python/src \
.venv/bin/uvicorn src.app:app --host 0.0.0.0 --port 8080
```

### FastAPI + SQLModel

Path:
- [examples/python/prophet_example_fastapi_sqlmodel](../../examples/python/prophet_example_fastapi_sqlmodel)
- [README](../../examples/python/prophet_example_fastapi_sqlmodel/README.md)

Run:

```bash
cd examples/python/prophet_example_fastapi_sqlmodel
prophet gen
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=$(git rev-parse --show-toplevel)/prophet-lib/python/src \
.venv/bin/uvicorn src.app:app --host 0.0.0.0 --port 8080
```

### Flask + SQLAlchemy

Path:
- [examples/python/prophet_example_flask_sqlalchemy](../../examples/python/prophet_example_flask_sqlalchemy)
- [README](../../examples/python/prophet_example_flask_sqlalchemy/README.md)

Run:

```bash
cd examples/python/prophet_example_flask_sqlalchemy
prophet gen
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=$(git rev-parse --show-toplevel)/prophet-lib/python/src \
FLASK_APP=src.app:app .venv/bin/flask run --host 0.0.0.0 --port 8080
```

### Flask + SQLModel

Path:
- [examples/python/prophet_example_flask_sqlmodel](../../examples/python/prophet_example_flask_sqlmodel)
- [README](../../examples/python/prophet_example_flask_sqlmodel/README.md)

Run:

```bash
cd examples/python/prophet_example_flask_sqlmodel
prophet gen
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=$(git rev-parse --show-toplevel)/prophet-lib/python/src \
FLASK_APP=src.app:app .venv/bin/flask run --host 0.0.0.0 --port 8080
```

### Django + Django ORM

Path:
- [examples/python/prophet_example_django](../../examples/python/prophet_example_django)
- [README](../../examples/python/prophet_example_django/README.md)

Run:

```bash
cd examples/python/prophet_example_django
prophet gen
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
DJANGO_SETTINGS_MODULE=prophet_example_django.settings \
PYTHONPATH=$(git rev-parse --show-toplevel)/prophet-lib/python/src:src:gen/python/src \
.venv/bin/python manage.py runserver 0.0.0.0:8080
```

## One-Command Test Sweep

From repository root:

```bash
./scripts/test-all.sh
```

## Minimal Turtle Example

Path:
- [examples/turtle/prophet_example_turtle_minimal](../../examples/turtle/prophet_example_turtle_minimal)
- [README](../../examples/turtle/prophet_example_turtle_minimal/README.md)

Generate Turtle output in any Prophet project by enabling `turtle` in `generation.targets`, then running:

```bash
prophet gen
```

Expected output:
- `gen/turtle/ontology.ttl`

Validate the generated Turtle with base SHACL shapes:

```bash
pyshacl -s prophet.ttl -d prophet.ttl examples/turtle/prophet_example_turtle_minimal/gen/turtle/ontology.ttl -e prophet.ttl --advanced --inference owlrl --format turtle
```

## Complex Turtle Example (Small Business)

Path:
- [examples/turtle/prophet_example_turtle_small_business](../../examples/turtle/prophet_example_turtle_small_business)
- [README](../../examples/turtle/prophet_example_turtle_small_business/README.md)

This example models a realistic small-business domain with:
- customers, employees, suppliers, products, inventory, purchase orders, sales orders, invoices, and deliveries
- multiple object relationships via `ref(...)`
- reusable structs for addresses, contacts, order lines, and payment details
- lifecycle state machines and transitions for purchasing, sales, and invoicing
- mixed action output forms (`output { ... }`, `output signal ...`, `output transition ...`)
- signal-driven automation via triggers

Generate and validate:

```bash
cd examples/turtle/prophet_example_turtle_small_business
prophet gen
cd $(git rev-parse --show-toplevel)
pyshacl -s prophet.ttl -d prophet.ttl examples/turtle/prophet_example_turtle_small_business/gen/turtle/ontology.ttl -e prophet.ttl --advanced --inference owlrl --format turtle
```
