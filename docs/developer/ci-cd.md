# CI/CD

## CI Workflow (`.github/workflows/ci.yml`)

Main jobs:
- package validation (tests, build, twine check, wheel smoke install)
- Spring integration validation (generate, verify-clean, check, compile, tests)

Guardrails:
- workflow concurrency cancellation for redundant runs
- generated file cleanliness checks
- tracked-file drift checks

## Publish Workflow (`.github/workflows/publish-pypi.yml`)

Triggers:
- tag pushes matching `v*.*.*`
- manual dispatch

Flow:
1. validate + build distribution
2. publish to PyPI via trusted publishing (OIDC)

Requires GitHub environment `pypi` and PyPI trusted publisher config.
