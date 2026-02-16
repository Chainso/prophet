# prophet-lib Runtime Runbook

This runbook covers local validation and publishing for the shared runtime packages under `prophet-lib/`.

## Scope

Runtime packages:
- JavaScript: `prophet-lib/javascript` (`@prophet/events-runtime`)
- Python: `prophet-lib/python` (`prophet-events-runtime`)
- Java: `prophet-lib/java` (`io.prophet:prophet-events-runtime`)

Release workflow:
- [`.github/workflows/publish-prophet-lib.yml`](../../.github/workflows/publish-prophet-lib.yml)

## Version Alignment

Use `prophet-lib/VERSION` as the release source of truth.

Before publishing, ensure these match exactly:
- `prophet-lib/VERSION`
- `prophet-lib/javascript/package.json` -> `version`
- `prophet-lib/python/pyproject.toml` -> `[project].version`
- `prophet-lib/java/build.gradle.kts` -> `version`

The publish workflow rejects mismatches.

## Local Validation

Run from repository root.

### JavaScript runtime

```bash
npm --prefix prophet-lib/javascript test
npm --prefix prophet-lib/javascript pack --dry-run
```

### Python runtime

```bash
python3 -m pip install --upgrade build twine
PYTHONPATH=prophet-lib/python/src \
python3 -m unittest discover -s prophet-lib/python/tests -p 'test_*.py' -v
python3 -m build prophet-lib/python
python3 -m twine check prophet-lib/python/dist/*
```

### Java runtime

Use the Spring example’s Gradle wrapper to run `prophet-lib/java` tasks:

```bash
cd examples/java/prophet_example_spring
./gradlew -p ../../../prophet-lib/java test
./gradlew -p ../../../prophet-lib/java publishToMavenLocal
```

## Local Integration Smoke Checks

After publishing Java runtime to local Maven:

```bash
cd examples/java/prophet_example_spring
$(git rev-parse --show-toplevel)/.venv/bin/prophet gen --wire-gradle
./gradlew :prophet_generated:compileJava compileJava
./gradlew test
```

For Python examples, include runtime source on `PYTHONPATH`:

```bash
cd examples/python/prophet_example_fastapi_sqlalchemy
PYTHONPATH=../../../prophet-lib/python/src:src:gen/python/src \
$(git rev-parse --show-toplevel)/.venv/bin/python -c "import app"
```

For Node examples, `file:` dependency links runtime automatically during `npm install`/`npm ci`.

## CI Integration

Main CI workflow:
- [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)

Runtime coverage added in CI:
- `prophet-lib-runtimes` job validates JavaScript, Python, and Java runtime packages.
- Spring example job publishes Java runtime to local Maven before compile/tests.
- Python example jobs prepend `prophet-lib/python/src` to `PYTHONPATH` for smoke/tests.

## Publishing

Use manual dispatch of:
- [`.github/workflows/publish-prophet-lib.yml`](../../.github/workflows/publish-prophet-lib.yml)

Inputs:
- `release_version`: must match `prophet-lib/VERSION`
- `stage`: `test` or `public`
- language toggles: `publish_javascript`, `publish_python`, `publish_java`

### Stage: `test`

- JavaScript: validation + dry-run pack (no registry publish)
- Python: publish to TestPyPI via trusted publishing (OIDC)
- Java: publish to local Maven (smoke gate for packaging)

### Stage: `public`

- JavaScript: publish to npm (`NPM_TOKEN`)
- Python: publish to PyPI via trusted publishing (OIDC)
- Java: publish to Maven Central (`SONATYPE_USERNAME`, `SONATYPE_PASSWORD`, `MAVEN_GPG_PRIVATE_KEY`, `MAVEN_GPG_PASSPHRASE`)

## Required Secrets

Public stage:
- `NPM_TOKEN`
- `SONATYPE_USERNAME`
- `SONATYPE_PASSWORD`
- `MAVEN_GPG_PRIVATE_KEY`
- `MAVEN_GPG_PASSPHRASE`

Python publish path requirements:
- Configure trusted publishers for `.github/workflows/publish-prophet-lib.yml` in both TestPyPI and PyPI.

## Post-Publish Verification

Check package registries:
- npm: `npm view @prophet/events-runtime version`
- PyPI: `pip index versions prophet-events-runtime`
- Maven Central: verify `io.prophet:prophet-events-runtime:<version>` appears

Then regenerate and compile examples from a clean checkout to confirm installability end-to-end.
