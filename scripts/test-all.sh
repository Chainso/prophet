#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

VENV_PYTHON="${ROOT_DIR}/.venv/bin/python"
VENV_PROPHET="${ROOT_DIR}/.venv/bin/prophet"
RUN_INSTALL=0

if [[ "${1:-}" == "--install" ]]; then
  RUN_INSTALL=1
fi

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "error: required command not found: $1" >&2
    exit 1
  fi
}

require_file() {
  if [[ ! -x "$1" ]]; then
    echo "error: required executable not found: $1" >&2
    exit 1
  fi
}

section() {
  echo
  echo "== $1 =="
}

run_prophet_checks() {
  "$VENV_PROPHET" gen ${2:-}
  "$VENV_PROPHET" generate --verify-clean
  "$VENV_PROPHET" check --show-reasons
}

python_module_installed() {
  local python_bin="$1"
  local module="$2"
  "$python_bin" - "$module" <<'PY'
import importlib.util
import sys

module = sys.argv[1]
sys.exit(0 if importlib.util.find_spec(module) else 1)
PY
}

ensure_python_requirements() {
  local python_bin="$1"
  local module="$2"
  if [[ $RUN_INSTALL -eq 1 ]]; then
    "$python_bin" -m pip install -r requirements.txt
    return
  fi
  if ! python_module_installed "$python_bin" "$module"; then
    echo "Installing missing Python dependencies from $(pwd)/requirements.txt"
    "$python_bin" -m pip install -r requirements.txt
  fi
}

require_cmd npm
require_cmd java
require_file "$VENV_PYTHON"
require_file "$VENV_PROPHET"

if [[ $RUN_INSTALL -eq 1 ]]; then
  section "Installing Prophet CLI Test Dependencies"
  "$VENV_PYTHON" -m pip install -e ./prophet-cli
fi

section "CLI Unit Tests"
"$VENV_PYTHON" -m unittest discover -s prophet-cli/tests -p 'test_*.py' -v

section "Runtime Libraries"
npm --prefix prophet-lib/javascript test
PYTHONPATH="${ROOT_DIR}/prophet-lib/python/src" \
  "$VENV_PYTHON" -m unittest discover -s prophet-lib/python/tests -p 'test_*.py' -v
pushd examples/java/prophet_example_spring >/dev/null
./gradlew -p ../../../prophet-lib/java test
./gradlew -p ../../../prophet-lib/java publishToMavenLocal
popd >/dev/null

section "Java Spring Example"
pushd examples/java/prophet_example_spring >/dev/null
run_prophet_checks "$PWD" "--wire-gradle"
./gradlew test
popd >/dev/null

NODE_EXAMPLES=(
  "examples/node/prophet_example_express_prisma"
  "examples/node/prophet_example_express_typeorm"
  "examples/node/prophet_example_express_mongoose"
)

for dir in "${NODE_EXAMPLES[@]}"; do
  section "Node Example: $(basename "$dir")"
  pushd "$dir" >/dev/null

  run_prophet_checks "$PWD"

  if [[ $RUN_INSTALL -eq 1 ]]; then
    npm install
  fi

  npm run build

  if [[ "$dir" == "examples/node/prophet_example_express_prisma" ]]; then
    npm run prisma:generate
    npm run prisma:push
  fi

  npm run test:integration
  popd >/dev/null
done

PYTHON_EXAMPLES=(
  "examples/python/prophet_example_fastapi_sqlalchemy"
  "examples/python/prophet_example_fastapi_sqlmodel"
  "examples/python/prophet_example_flask_sqlalchemy"
  "examples/python/prophet_example_flask_sqlmodel"
  "examples/python/prophet_example_django"
)

for dir in "${PYTHON_EXAMPLES[@]}"; do
  section "Python Example: $(basename "$dir")"
  pushd "$dir" >/dev/null

  run_prophet_checks "$PWD"
  PYTHON_RUNTIME_PATH="${ROOT_DIR}/prophet-lib/python/src"
  EXAMPLE_PYTHON="$VENV_PYTHON"
  if [[ -x ".venv/bin/python" ]]; then
    EXAMPLE_PYTHON=".venv/bin/python"
  fi
  case "$dir" in
    *fastapi*) ensure_python_requirements "$EXAMPLE_PYTHON" "fastapi" ;;
    *flask*) ensure_python_requirements "$EXAMPLE_PYTHON" "flask" ;;
    *django*) ensure_python_requirements "$EXAMPLE_PYTHON" "django" ;;
    *) ensure_python_requirements "$EXAMPLE_PYTHON" "unittest" ;;
  esac
  ensure_python_requirements "$EXAMPLE_PYTHON" "pytest"

  if [[ "$dir" == "examples/python/prophet_example_django" ]]; then
    PYTHONPATH="${PYTHON_RUNTIME_PATH}:src:gen/python/src" DJANGO_SETTINGS_MODULE=prophet_example_django.settings \
      "$EXAMPLE_PYTHON" -m pytest -q tests
  else
    PYTHONPATH="${PYTHON_RUNTIME_PATH}:src:gen/python/src" \
      "$EXAMPLE_PYTHON" -m pytest -q tests
  fi
  popd >/dev/null
done

section "All Tests Passed"
echo "CLI + Java + Node + Python example suites completed successfully."
