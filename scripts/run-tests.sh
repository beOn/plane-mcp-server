#!/usr/bin/env bash
# One-command test runner: setup ephemeral stack → run pytest → teardown.
#
# Usage:
#   ./scripts/run-tests.sh                  # run all tests
#   ./scripts/run-tests.sh -k email         # run only email tests
#   ./scripts/run-tests.sh --no-teardown    # keep stack running after tests
#
# Any arguments not consumed by this script are passed through to pytest.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

TEARDOWN=true
PYTEST_ARGS=()

for arg in "$@"; do
    if [ "$arg" = "--no-teardown" ]; then
        TEARDOWN=false
    else
        PYTEST_ARGS+=("$arg")
    fi
done

cleanup() {
    if $TEARDOWN; then
        echo ""
        echo "==> Tearing down test stack..."
        "$SCRIPT_DIR/teardown-test-env.sh"
    else
        echo ""
        echo "==> Skipping teardown (--no-teardown). Stack is still running."
        echo "    Tear down manually:  ./scripts/teardown-test-env.sh"
    fi
}
trap cleanup EXIT

# Start stack and export env vars
eval "$("$SCRIPT_DIR/setup-test-env.sh")"

echo "==> Running tests..."
echo ""

# Run pytest with any extra args
.venv/bin/python -m pytest tests/ -v "${PYTEST_ARGS[@]}"
