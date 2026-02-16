# Codegen Architecture

## Stack Manifest

Supported stacks are declared in a schema-validated manifest contract.

Current implemented stacks:
- `java_spring_jpa`
- `node_express_prisma`
- `node_express_typeorm`
- `node_express_mongoose`
- `python_fastapi_sqlalchemy`
- `python_fastapi_sqlmodel`
- `python_flask_sqlalchemy`
- `python_flask_sqlmodel`
- `python_django_django_orm`

Planned stacks can exist in manifest as non-implemented entries for forward visibility and validation.

Manifest contract requirements include:
- top-level schema version
- capability catalog
- stack tuple identity (`id`, `language`, `framework`, `orm`)
- status (`implemented` or `planned`)
- capability declarations per stack
- default generation targets

Code location:
- [prophet-cli/src/prophet_cli/codegen/stack_manifest.py](../../prophet-cli/src/prophet_cli/codegen/stack_manifest.py)

## Generation Pipeline

1. Resolve stack specification
2. Build generation context
3. Route to stack generator
4. Aggregate outputs
5. Write outputs + managed-file manifest
6. Remove stale managed files

## Node Generator Layout

Node/Express generation is organized as an orchestrator plus focused renderer modules:

- Orchestrator:
  - `prophet-cli/src/prophet_cli/targets/node_express/generator.py`
- Shared render support:
  - `prophet-cli/src/prophet_cli/targets/node_express/render/support.py`
- Common (stack-agnostic) renderers:
  - `prophet-cli/src/prophet_cli/targets/node_express/render/common/`
- ORM-specific renderers:
  - `prophet-cli/src/prophet_cli/targets/node_express/render/orm/prisma.py`
  - `prophet-cli/src/prophet_cli/targets/node_express/render/orm/typeorm.py`
  - `prophet-cli/src/prophet_cli/targets/node_express/render/orm/mongoose.py`

The orchestrator is responsible for:
- target selection and stack gating
- composing per-file outputs
- applying NodeNext import normalization
- emitting extension hook and generated-file manifests

Renderer modules are responsible for converting IR into artifact content only.

## Java Generator Layout

Java/Spring generation now follows the same orchestrator + renderer split:

- Orchestrator:
  - `prophet-cli/src/prophet_cli/targets/java_spring_jpa/generator.py`
- Java-common render support (shared across Java targets):
  - `prophet-cli/src/prophet_cli/targets/java_common/render/support.py`
- Spring/JPA-specific renderer functions:
  - `prophet-cli/src/prophet_cli/targets/java_spring_jpa/render/spring.py` (stack orchestrator for Spring artifacts)
  - `prophet-cli/src/prophet_cli/targets/java_spring_jpa/render/common/` (Spring stack-common render sections)
  - `prophet-cli/src/prophet_cli/targets/java_spring_jpa/render/orm/` (JPA-specific render sections)

This mirrors the Node/Python split philosophy:
- common Java render helpers live outside the Spring target package
- Spring target keeps framework/stack-specific rendering and migration wiring

The CLI delegates generation to stack generators and renderer modules; generation implementation is no longer embedded in `cli.py`.

## Python Generator Layout

Python generation follows the same orchestrator + focused renderer split:

- Orchestrator:
  - `prophet-cli/src/prophet_cli/targets/python/generator.py`
- Shared render support:
  - `prophet-cli/src/prophet_cli/targets/python/render/support.py`
- Common (stack-agnostic) renderers:
  - `prophet-cli/src/prophet_cli/targets/python/render/common/`
- Framework-specific renderers:
  - `prophet-cli/src/prophet_cli/targets/python/render/framework/fastapi.py`
  - `prophet-cli/src/prophet_cli/targets/python/render/framework/flask.py`
  - `prophet-cli/src/prophet_cli/targets/python/render/framework/django.py`
- ORM-specific renderers:
  - `prophet-cli/src/prophet_cli/targets/python/render/orm/sqlalchemy.py`
  - `prophet-cli/src/prophet_cli/targets/python/render/orm/sqlmodel.py`
  - `prophet-cli/src/prophet_cli/targets/python/render/orm/django_orm.py`

The orchestrator is responsible for:
- target selection and stack gating
- composing per-file outputs
- selecting async/sync contract mode by framework
- emitting extension hook and generated-file manifests
- emitting autodetect report manifests when present

## Turtle Target Layout

Turtle output is implemented as a dedicated renderer module:

- `prophet-cli/src/prophet_cli/targets/turtle/render/turtle.py`

Stack generators treat Turtle like other optional targets and delegate to this renderer when `turtle` is enabled.

Conformance/testing notes:
- Renderer output is aligned to the base ontology in `prophet.ttl`
- SHACL conformance is enforced in `prophet-cli/tests/test_turtle_target.py` via `pyshacl`

## Shared Renderers

Cross-stack rendering that is not stack-orchestrator-specific is centralized in:

- `prophet-cli/src/prophet_cli/codegen/rendering.py`

This module currently owns:
- canonical SQL schema rendering
- OpenAPI rendering
- baseline delta migration rendering and metadata

## Ownership and Safety

- Generated files are tracked in `gen/manifest/generated-files.json`
- Extension points are tracked in `gen/manifest/extension-hooks.json`
- Regeneration must not overwrite user-owned extension implementations

## Performance

No-op generation can be skipped via cache signature (`prophet gen --skip-unchanged`).
