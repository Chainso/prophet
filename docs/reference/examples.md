# Examples

This page is the runnable sample app catalog.

Use [Quickstart](../quickstart/quickstart.md) when integrating Prophet into your own project.

## Java

### Spring + JPA

Path:
- [examples/java/prophet_example_spring](../../examples/java/prophet_example_spring)

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
