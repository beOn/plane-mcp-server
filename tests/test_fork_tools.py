"""
Smoke tests for fork-specific MCP tools.

Tests run against the local Plane dev instance via direct fork_request calls.
Skipped automatically if env vars not set.

Required env vars:
    PLANE_API_KEY: API key for the local dev instance
    PLANE_WORKSPACE_SLUG: Workspace slug (e.g., "intervan-dev")
    PLANE_BASE_URL: Base URL (e.g., "http://localhost:8000")
"""

import os
import pytest

# Skip entire module if env vars not set
pytestmark = pytest.mark.skipif(
    not all(
        os.getenv(v)
        for v in ("PLANE_API_KEY", "PLANE_WORKSPACE_SLUG", "PLANE_BASE_URL")
    ),
    reason="Requires PLANE_API_KEY, PLANE_WORKSPACE_SLUG, PLANE_BASE_URL",
)


@pytest.fixture(autouse=True)
def _set_env():
    """Ensure env vars are set for get_plane_client_context()."""
    # Already set if we got past skipif, but be explicit
    yield


def test_list_workspace_pages():
    """List workspace pages — should return a list."""
    from plane_mcp.fork_api import fork_request

    ws = os.environ["PLANE_WORKSPACE_SLUG"]
    result = fork_request("GET", f"workspaces/{ws}/pages")
    assert isinstance(result, list)
    if result:
        page = result[0]
        assert "id" in page
        assert "name" in page
        assert "child_page_ids" in page


def test_workspace_page_lifecycle():
    """Create → retrieve → update → archive a workspace page."""
    from plane_mcp.fork_api import fork_request

    ws = os.environ["PLANE_WORKSPACE_SLUG"]

    # Create
    page = fork_request(
        "POST",
        f"workspaces/{ws}/pages",
        json={
            "name": "MCP Smoke Test Page",
            "description_html": "<p>Created by test_fork_tools.py</p>",
            "access": 0,
        },
    )
    assert page["name"] == "MCP Smoke Test Page"
    page_id = page["id"]

    try:
        # Retrieve
        detail = fork_request("GET", f"workspaces/{ws}/pages/{page_id}")
        assert detail["id"] == page_id
        assert "description_html" in detail

        # Update
        updated = fork_request(
            "PATCH",
            f"workspaces/{ws}/pages/{page_id}",
            json={"name": "MCP Smoke Test Page (Updated)"},
        )
        assert updated["name"] == "MCP Smoke Test Page (Updated)"

        # Archive
        archive_result = fork_request(
            "POST", f"workspaces/{ws}/pages/{page_id}/archive"
        )
        assert "archived_at" in archive_result

    finally:
        # Cleanup: unarchive then... can't delete via API v1 (not exposed).
        # Leave archived — harmless test artifact.
        pass


def test_list_page_children():
    """List children of the Knowledge Base page (if it exists)."""
    from plane_mcp.fork_api import fork_request

    ws = os.environ["PLANE_WORKSPACE_SLUG"]

    # Get workspace pages, find one with children
    pages = fork_request("GET", f"workspaces/{ws}/pages")
    parent = next(
        (p for p in pages if p.get("child_page_ids") and len(p["child_page_ids"]) > 0),
        None,
    )
    if parent is None:
        pytest.skip("No workspace page with children found")

    children = fork_request(
        "GET", f"workspaces/{ws}/pages/{parent['id']}/children"
    )
    assert isinstance(children, list)
    assert len(children) > 0
    assert children[0]["parent"] == parent["id"]


def test_search_email_references():
    """Search email references — should return a list with correct shape."""
    from plane_mcp.fork_api import fork_request

    ws = os.environ["PLANE_WORKSPACE_SLUG"]
    result = fork_request("GET", f"workspaces/{ws}/email-references")
    assert isinstance(result, list)
    if result:
        ref = result[0]
        assert "id" in ref
        assert "message_id" in ref
        assert "subject" in ref
        assert "from_address" in ref
        assert "date" in ref


def test_email_reference_detail():
    """Get detail of first email reference (if any exist)."""
    from plane_mcp.fork_api import fork_request

    ws = os.environ["PLANE_WORKSPACE_SLUG"]
    refs = fork_request("GET", f"workspaces/{ws}/email-references")
    if not refs:
        pytest.skip("No email references indexed")

    detail = fork_request(
        "GET", f"workspaces/{ws}/email-references/{refs[0]['id']}"
    )
    assert detail["id"] == refs[0]["id"]
    assert "body_plain" in detail
    assert "to_addresses" in detail


def test_list_issue_templates():
    """List issue templates — should return a list with lite shape."""
    from plane_mcp.fork_api import fork_request

    ws = os.environ["PLANE_WORKSPACE_SLUG"]
    result = fork_request("GET", f"workspaces/{ws}/issue-templates")
    assert isinstance(result, list)
    if result:
        tmpl = result[0]
        assert "id" in tmpl
        assert "name" in tmpl
        assert "issue_type" in tmpl
        assert "is_active" in tmpl


def test_get_issue_template():
    """Get first issue template detail (if any exist)."""
    from plane_mcp.fork_api import fork_request

    ws = os.environ["PLANE_WORKSPACE_SLUG"]
    templates = fork_request("GET", f"workspaces/{ws}/issue-templates")
    if not templates:
        pytest.skip("No issue templates found")

    detail = fork_request(
        "GET", f"workspaces/{ws}/issue-templates/{templates[0]['id']}"
    )
    assert detail["id"] == templates[0]["id"]
    assert "template_data" in detail
    assert "description" in detail
