"""Integration test fixtures — session-scoped test project and helpers."""

import os
import time
import uuid

import pytest
import requests


def _with_retry(fn, max_retries=5, base_delay=3.0):
    """Wrap fork_request with retry logic for 429 rate limits."""

    def wrapper(*args, **kwargs):
        for attempt in range(max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 429 and attempt < max_retries:
                    # Use Retry-After header if present, otherwise exponential backoff
                    retry_after = e.response.headers.get("Retry-After")
                    if retry_after:
                        delay = float(retry_after)
                    else:
                        delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                raise

    return wrapper


def _safe_call(api, method, path, **kwargs):
    """Best-effort API call. Suppresses errors."""
    try:
        api(method, path, **kwargs)
    except Exception:
        pass


@pytest.fixture(scope="session")
def api():
    """The fork_request callable with 429 retry. Skips if no credentials."""
    if not os.getenv("PLANE_API_KEY"):
        pytest.skip("PLANE_API_KEY not set — cannot run integration tests")
    from plane_mcp.fork_api import fork_request

    return _with_retry(fork_request)


@pytest.fixture(scope="session")
def cleanup(api):
    """Best-effort DELETE helper for test cleanup."""

    def _cleanup(path, **kwargs):
        _safe_call(api, "DELETE", path, **kwargs)

    return _cleanup


@pytest.fixture(scope="session")
def archive_page(api):
    """Best-effort page archive (POST to /archive) for workspace page cleanup."""

    def _archive(path):
        _safe_call(api, "POST", path)

    return _archive


@pytest.fixture(scope="session")
def ws():
    """Workspace slug from env."""
    return os.environ["PLANE_WORKSPACE_SLUG"]


@pytest.fixture(scope="session")
def test_project(api, ws):
    """Disposable test project. Deleted at session end (cascade cleanup)."""
    unique = uuid.uuid4().hex[:6]
    project = api(
        "POST",
        f"workspaces/{ws}/projects",
        json={
            "name": f"MCP Test Suite {unique}",
            "identifier": f"TS{unique[:3].upper()}",
            "description": "Auto-created by pytest. Safe to delete.",
            "network": 0,
        },
    )
    # Enable features that are off by default on new projects
    _safe_call(
        api,
        "PATCH",
        f"workspaces/{ws}/projects/{project['id']}",
        json={"cycle_view": True, "module_view": True},
    )
    yield project
    _safe_call(api, "DELETE", f"workspaces/{ws}/projects/{project['id']}")


@pytest.fixture(scope="session")
def project_id(test_project):
    """Shortcut: test project UUID."""
    return test_project["id"]


@pytest.fixture(scope="session")
def project_states(api, ws, project_id):
    """Default states created with the test project."""
    resp = api("GET", f"workspaces/{ws}/projects/{project_id}/states")
    if isinstance(resp, dict) and "results" in resp:
        return resp["results"]
    return resp


@pytest.fixture(scope="session")
def default_state_id(project_states):
    """ID of the first state (usually 'Backlog')."""
    assert len(project_states) > 0, "Test project has no states"
    return project_states[0]["id"]


@pytest.fixture(scope="session")
def work_item_type(api, ws):
    """First active work item type (issue type) in the workspace."""
    types = api("GET", f"workspaces/{ws}/issue-types")
    active = [t for t in types if t.get("is_active", True)]
    if not active:
        pytest.skip("No active work item types in workspace")
    return active[0]


@pytest.fixture(scope="session")
def work_item_type_id(work_item_type):
    """UUID of the first active work item type."""
    return work_item_type["id"]
