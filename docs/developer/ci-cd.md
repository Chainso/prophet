# CI/CD

## CI Workflow ([.github/workflows/ci.yml](../../.github/workflows/ci.yml))

Main jobs:
- package validation (tests, build, twine check, wheel smoke install)
- Spring integration validation (generate, verify-clean, check, compile, tests)
- Node integration validation matrix:
  - Express + Prisma (generate, npm ci, prisma generate, ts build, verify-clean, check)
  - Express + TypeORM (generate, npm ci, ts build, verify-clean, check)
  - Express + Mongoose (generate, npm ci, ts build, verify-clean, check)

Guardrails:
- workflow concurrency cancellation for redundant runs
- generated file cleanliness checks
- tracked-file drift checks

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

Requires GitHub environment `pypi` and PyPI trusted publisher config.
