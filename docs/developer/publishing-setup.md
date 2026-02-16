# Publishing Setup

This doc is the one-time setup checklist for Prophet publishing.

It covers:
- `prophet-cli` release publishing to PyPI
- `prophet-lib` runtime publishing to npm, TestPyPI/PyPI, and Maven Central

## Prerequisites

- GitHub admin access for the repository.
- Maintainer accounts with publish rights in:
  - npm (for `@prophet-ontology/events-runtime`)
  - PyPI/TestPyPI (`prophet-cli`, `prophet-events-runtime`)
  - Sonatype Central Portal (for `io.github.chainso:prophet-events-runtime`)
- GPG key pair for Maven Central signing (ASCII-armored private key).

## Workflows Used

- `prophet-cli`: [`.github/workflows/publish-pypi.yml`](../../.github/workflows/publish-pypi.yml)
- `prophet-lib`: [`.github/workflows/publish-prophet-lib.yml`](../../.github/workflows/publish-prophet-lib.yml)

Runtime publish triggers:
- tag pushes matching `lib-v*.*.*` (automatic `public` stage for all runtime languages)
- manual dispatch (supports `test` and selective language toggles)

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

## 2. Configure `prophet-lib` Runtime Publishing

Add these repository secrets in GitHub settings:

Public stage:
- `SONATYPE_USERNAME`
- `SONATYPE_PASSWORD`
- `SONATYPE_NAMESPACE` (required, for example `io.github.chainso`)
- `MAVEN_GPG_PRIVATE_KEY`
- `MAVEN_GPG_PASSPHRASE`

For JavaScript runtime publishing, configure npm trusted publishing:

1. In npm package settings for `@prophet-ontology/events-runtime`, add a trusted publisher for:
   - owner/repo: `Chainso/prophet`
   - workflow: `.github/workflows/publish-prophet-lib.yml`

For Python runtime publishing, configure trusted publishers in both indexes:

1. In TestPyPI, add a trusted publisher for:
   - owner/repo: `Chainso/prophet`
   - workflow: `.github/workflows/publish-prophet-lib.yml`
   - environment: `testpypi`
2. In PyPI, add a trusted publisher for:
   - owner/repo: `Chainso/prophet`
   - workflow: `.github/workflows/publish-prophet-lib.yml`
   - environment: `pypi`

## 3. Configure Registry Access

### npm

- Configure npm trusted publishing for `@prophet-ontology/events-runtime` with:
  - owner/repo: `Chainso/prophet`
  - workflow: `.github/workflows/publish-prophet-lib.yml`
- This path uses OIDC and does not require npm tokens in GitHub secrets.

### PyPI/TestPyPI

- Configure trusted publishers for both TestPyPI and PyPI using:
  - owner/repo: `Chainso/prophet`
  - workflow: `.github/workflows/publish-prophet-lib.yml`
- This path uses OIDC and does not require Python package API tokens in GitHub secrets.

### Maven Central (Sonatype)

- Ensure group/artifact ownership allows publishing `io.github.chainso:prophet-events-runtime`.
- Store Sonatype Central Portal user token credentials in `SONATYPE_USERNAME` / `SONATYPE_PASSWORD`.
- Set `SONATYPE_NAMESPACE` to your verified Central Portal namespace (for example `io.github.chainso`).
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
2. Choose one public publish path:
   - preferred automatic path: push annotated tag `lib-vX.Y.Z` (must match `prophet-lib/VERSION`)
   - manual path: run Actions -> `Publish prophet-lib runtimes` with `stage = public` and matching `release_version`
3. Verify published versions:
   - `npm view @prophet-ontology/events-runtime version`
   - `pip index versions prophet-events-runtime`
   - Maven Central lookup for `io.github.chainso:prophet-events-runtime`

For `prophet-cli`, create and push annotated release tag `vX.Y.Z` after validation/changelog updates.

## Troubleshooting

- Version mismatch failures: align `prophet-lib/VERSION` with all runtime manifests.
- Missing secret failures: check exact secret names (Sonatype/GPG secrets) in workflow logs.
- npm `E404` / `Access token expired or revoked`: verify npm trusted publisher for `@prophet-ontology/events-runtime` is configured for this repository/workflow.
- PyPI `invalid-publisher`: verify trusted publisher entries for `prophet-events-runtime` match repo/workflow and environment (`pypi` or `testpypi`).
- Sonatype HTTP `402 Payment Required`: verify Sonatype Central Portal namespace entitlement and token credentials (`SONATYPE_USERNAME`/`SONATYPE_PASSWORD`) for your `SONATYPE_NAMESPACE`.
- Sonatype HTTP `401 Unauthorized`: ensure `SONATYPE_USERNAME`/`SONATYPE_PASSWORD` are Central Portal user token credentials (not account password / legacy OSSRH token) and that the token-owning account can publish to `SONATYPE_NAMESPACE`.
- Maven publish/signing failures: verify Sonatype permissions and GPG key/passphrase pair.
