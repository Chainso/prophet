# CI/CD

## CI Workflow ([.github/workflows/ci.yml](../../.github/workflows/ci.yml))

Main jobs:
- package validation (tests, build, twine check, wheel smoke install)
- `prophet-lib` runtime validation:
  - JavaScript runtime tests + package dry-run
  - Python runtime tests + package build
  - Java runtime tests + local Maven publish smoke
- Spring integration validation (generate, verify-clean, check, compile, tests)
- Node integration validation matrix:
  - Express + Prisma (generate, npm ci, prisma generate, ts build, verify-clean, check)
  - Express + TypeORM (generate, npm ci, ts build, verify-clean, check)
  - Express + Mongoose (generate, npm ci, ts build, verify-clean, check)
- Python integration validation matrix:
  - FastAPI + SQLAlchemy (generate, verify-clean, check, compile, import smoke)
  - FastAPI + SQLModel (generate, verify-clean, check, compile, import smoke)
  - Flask + SQLAlchemy (generate, verify-clean, check, compile, import smoke)
  - Flask + SQLModel (generate, verify-clean, check, compile, import smoke)
  - Django + Django ORM (generate, verify-clean, check, compile, import smoke)

Guardrails:
- workflow concurrency cancellation for redundant runs
- generated file cleanliness checks
- tracked-file drift checks
- Python example smoke/tests include `prophet-lib/python/src` on `PYTHONPATH`
- Spring example compile/tests publish Java runtime to local Maven first

## Publish Workflow ([.github/workflows/publish-pypi.yml](../../.github/workflows/publish-pypi.yml))

Triggers:
- tag pushes matching `v*.*.*`
- manual dispatch

Flow:
1. validate + build distribution
2. publish to PyPI via trusted publishing (OIDC)

Release validation also covers:
- Spring example generation/runtime checks
- Node Prisma generation + compile checks
- Node TypeORM generation + compile checks
- Node Mongoose generation + compile checks
- Python FastAPI/Flask/Django generation + compile/import checks (via CI workflow matrix)

Requires GitHub environment `pypi` and PyPI trusted publisher config.

## Runtime Publish Workflow ([.github/workflows/publish-prophet-lib.yml](../../.github/workflows/publish-prophet-lib.yml))

Runtime publishing for `prophet-lib` packages:
- triggers:
  - tag pushes matching `lib-v*.*.*` (auto-public publish for all runtimes)
  - manual dispatch (staged or selective publish)
- validates version alignment against `prophet-lib/VERSION`
- validates each selected runtime package before publish
- uses OIDC trusted publishing for JavaScript and Python package release
- supports two stages:
  - `test`: TestPyPI upload for Python, dry-run packaging for JavaScript, local Maven publish for Java
  - `public`: npm, PyPI, and Maven Central publish paths

Release hygiene note:
- runtime version bumps affect generated dependency pins in example fixtures; refresh generated examples and `gen/manifest/generated-files.json` snapshots before publishing tags.

Reference runbook:
- [prophet-lib Runtime Runbook](prophet-lib-release.md)
