"""Root pytest configuration — markers, credential setup."""

import os
import subprocess


def _keychain_get(service: str, account: str) -> str | None:
    """Retrieve a password from macOS Keychain. Returns None on failure."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def pytest_configure(config):
    """Register markers and set up credentials early (before collection)."""
    config.addinivalue_line("markers", "unit: pure logic tests, no API credentials needed")
    config.addinivalue_line("markers", "integration: tests that hit the real Plane API")

    # Set defaults early so skipif markers evaluate correctly.
    # Default to local ephemeral test stack; override with env vars for production.
    if not os.getenv("PLANE_BASE_URL"):
        os.environ["PLANE_BASE_URL"] = "http://localhost:18000"
    if not os.getenv("PLANE_WORKSPACE_SLUG"):
        os.environ["PLANE_WORKSPACE_SLUG"] = "test-workspace"
    if not os.getenv("PLANE_API_KEY"):
        # Try env-based key first (set by setup-test-env.sh), then Keychain
        key = os.getenv("PLANE_TEST_API_KEY") or _keychain_get("intervan-plane", "plane-api-key")
        if key:
            os.environ["PLANE_API_KEY"] = key
