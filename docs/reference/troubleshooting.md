# Troubleshooting

## `ModuleNotFoundError: No module named 'yaml'`

Cause:
- CLI runtime missing `PyYAML` dependency.

Fix:

```bash
python3 -m pip install --upgrade prophet-cli
# or for local editable installs
.venv/bin/pip install --no-build-isolation -e ./prophet-cli
```

## `prophet.yaml not found`

Cause:
- Command run outside initialized project root.

Fix:

```bash
prophet init
# then set project.ontology_file and rerun
```

## Spring compile errors for generated package imports

Cause:
- Ontology-scoped package root changed and app imports are stale.

Fix:
1. Re-run generation: `prophet gen --wire-gradle`
2. Update user code imports to `<base_package>.<ontology_name>.generated...`

## Query behavior confusion (`GET /objects` vs `/query`)

Current contract:
- `GET /<objects>` is pagination/sort only
- `POST /<objects>/query` is typed filtering

Fix:
- Move filter payloads to `/query` endpoint.

## JSON parse errors when calling APIs

Cause:
- Invalid JSON payload formatting.

Fix:
- Ensure keys/strings use double quotes in request body.

## Regeneration drift in CI

Cause:
- Checked-in generated files differ from current toolchain outputs.

Fix:

```bash
prophet gen --wire-gradle
prophet generate --verify-clean
git add -A
```

## Node stack autodetection ambiguity

Cause:
- `package.json` indicates `express` with multiple supported ORM signals (for example Prisma + TypeORM, or TypeORM + Mongoose).

Fix:
- Set stack explicitly in `prophet.yaml`:

```yaml
generation:
  stack:
    id: node_express_prisma
# or: node_express_typeorm
# or: node_express_mongoose
```

## `Node autodetect failed to resolve a safe generation stack`

Cause:
- Express was detected, but Prophet could not infer a single supported Node ORM target.
- Common cases: multiple ORMs detected, or Express detected with none of Prisma/TypeORM/Mongoose.

Fix:
- Set `generation.stack.id` explicitly in `prophet.yaml`:

```yaml
generation:
  stack:
    id: node_express_prisma
# or
#   id: node_express_typeorm
# or
#   id: node_express_mongoose
```

## `Python autodetect failed to resolve a safe generation stack`

Cause:
- Python project signals were detected, but Prophet could not infer one safe Python stack.
- Common cases: multiple frameworks detected (for example FastAPI + Flask), or framework detected without ORM signal.

Fix:
- Set `generation.stack.id` explicitly in `prophet.yaml`:

```yaml
generation:
  stack:
    id: python_fastapi_sqlalchemy
# or
#   id: python_fastapi_sqlmodel
# or
#   id: python_flask_sqlalchemy
# or
#   id: python_flask_sqlmodel
# or
#   id: python_django_django_orm
```

## Python generated import/module errors

Cause:
- Example dependencies are not installed in the active environment.

Fix:

```bash
pip install -r requirements.txt
prophet gen
```

For Django examples, ensure both paths are on `PYTHONPATH`:
- `src`
- `gen/python/src`

## Node `package.json` script rewiring concerns

Behavior:
- For Node stacks, `prophet gen` adds `prophet:gen`, `prophet:check`, `prophet:validate` scripts when missing.
- Existing custom script values are not overwritten.

If you need to remove Prophet-managed script entries:
- Run `prophet clean` in the Node project root.

## `tsc: command not found` in Node examples

Cause:
- Node dependencies are not installed yet.

Fix:

```bash
npm install
npm run build
```

## Prisma compile/runtime errors after generation

Cause:
- Prisma client not generated for `gen/node-express/prisma/schema.prisma`.

Fix:

```bash
npx prisma generate --schema gen/node-express/prisma/schema.prisma
```
