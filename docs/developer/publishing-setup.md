# Publishing Setup

This doc is the one-time setup checklist for Prophet publishing.

It covers:
- `prophet-cli` release publishing to PyPI
- `prophet-lib` runtime publishing to npm, TestPyPI/PyPI, and Maven Central

## Prerequisites

- GitHub admin access for the repository.
- Maintainer accounts with publish rights in:
  - npm (for `@prophet/events-runtime`)
  - PyPI/TestPyPI (`prophet-cli`, `prophet-events-runtime`)
  - Sonatype OSSRH (for `io.prophet:prophet-events-runtime`)
- GPG key pair for Maven Central signing (ASCII-armored private key).

## Workflows Used

- `prophet-cli`: [`.github/workflows/publish-pypi.yml`](../../.github/workflows/publish-pypi.yml)
- `prophet-lib`: [`.github/workflows/publish-prophet-lib.yml`](../../.github/workflows/publish-prophet-lib.yml)

## 1. Configure `prophet-cli` PyPI Trusted Publishing

1. In PyPI, add a trusted publisher for:
   - owner/repo: `Chainso/prophet`
   - workflow: `.github/workflows/publish-pypi.yml`
   - environment: `pypi`
2. In GitHub, create environment `pypi` in repo settings.
3. Restrict the environment according to your release policy (recommended).
4. Run a dry release on a non-production version first.

Notes:
- This path uses OIDC trusted publishing, not API tokens.
- Tag pattern trigger is `v*.*.*`.

## 2. Configure `prophet-lib` Runtime Publishing Secrets

Add these repository secrets in GitHub settings:

Test stage:
- `TEST_PYPI_API_TOKEN`

Public stage:
- `NPM_TOKEN`
- `PYPI_API_TOKEN`
- `SONATYPE_USERNAME`
- `SONATYPE_PASSWORD`
- `MAVEN_GPG_PRIVATE_KEY`
- `MAVEN_GPG_PASSPHRASE`

## 3. Configure Registry Access

### npm

- Ensure the npm user/token in `NPM_TOKEN` can publish `@prophet/events-runtime`.
- If org-scoped, confirm org permissions and 2FA policy compatibility for automation tokens.

### PyPI/TestPyPI

- Create API tokens for:
  - TestPyPI (`TEST_PYPI_API_TOKEN`)
  - PyPI (`PYPI_API_TOKEN`)
- Scope tokens to least privilege practical for release automation.

### Maven Central (Sonatype)

- Ensure group/artifact ownership allows publishing `io.prophet:prophet-events-runtime`.
- Store Sonatype credentials in `SONATYPE_USERNAME` / `SONATYPE_PASSWORD`.
- Export ASCII-armored private signing key into `MAVEN_GPG_PRIVATE_KEY`.
- Store passphrase in `MAVEN_GPG_PASSPHRASE`.

## 4. Validate Before First Publish

From repo root:

```bash
./scripts/test-all.sh
```

For runtime-only checks:

```bash
npm --prefix prophet-lib/javascript test
PYTHONPATH=prophet-lib/python/src python3 -m unittest discover -s prophet-lib/python/tests -p 'test_*.py' -v
cd examples/java/prophet_example_spring && ./gradlew -p ../../../prophet-lib/java test
```

## 5. First Dry Run (Recommended)

Run `prophet-lib` test-stage workflow manually:

1. Open Actions -> `Publish prophet-lib runtimes`.
2. `stage = test`
3. `release_version` must equal `prophet-lib/VERSION`.
4. Enable all language toggles.
5. Confirm:
   - Python package uploads to TestPyPI
   - JavaScript package validates and pack dry-run passes
   - Java package publishes to local Maven in CI job

## 6. First Public Publish

1. Re-validate local + CI.
2. Run Actions -> `Publish prophet-lib runtimes` with:
   - `stage = public`
   - matching `release_version`
3. Verify published versions:
   - `npm view @prophet/events-runtime version`
   - `pip index versions prophet-events-runtime`
   - Maven Central lookup for `io.prophet:prophet-events-runtime`

For `prophet-cli`, create and push annotated release tag `vX.Y.Z` after validation/changelog updates.

## Troubleshooting

- Version mismatch failures: align `prophet-lib/VERSION` with all runtime manifests.
- Missing secret failures: check exact secret names in workflow logs.
- Maven publish/signing failures: verify Sonatype permissions and GPG key/passphrase pair.
