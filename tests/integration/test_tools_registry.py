"""Verify the MCP server registers exactly the expected 18 tools.

Replaces the broken test_integration.py which had a stale 80-tool list
from before the T-038 CRUD refactor.
"""

import pytest

pytestmark = pytest.mark.unit

EXPECTED_TOOLS = sorted([
    # 5 generic CRUD
    "list_resources",
    "create_resource",
    "get_resource",
    "update_resource",
    "delete_resource",
    # 13 specialized
    "search_work_items",
    "search_email_references",
    "link_emails_to_issue",
    "unlink_email_from_issue",
    "mark_emails_triaged",
    "manage_cycle_items",
    "manage_module_items",
    "archive_resource",
    "list_page_children",
    "get_project_info",
    "get_workspace_info",
    "batch_update_resources",
    "get_me",
])


def test_tool_count():
    """Verify expected tool list has exactly 18 entries."""
    assert len(EXPECTED_TOOLS) == 18


def test_tool_names():
    """All expected tools are registered on a fresh FastMCP instance."""
    from fastmcp import FastMCP

    from plane_mcp.tools.crud import register_crud_tools
    from plane_mcp.tools.specialized import register_specialized_tools

    mcp = FastMCP("test")
    register_crud_tools(mcp)
    register_specialized_tools(mcp)

    # Try to get tool names through available APIs
    registered = None

    # Method 1: _tool_manager._tools (FastMCP internals)
    tm = getattr(mcp, "_tool_manager", None)
    if tm and hasattr(tm, "_tools"):
        registered = sorted(tm._tools.keys())

    # Method 2: _tools dict
    if registered is None:
        tools = getattr(mcp, "_tools", None)
        if isinstance(tools, dict):
            registered = sorted(tools.keys())

    # Method 3: async get_tools / list_tools
    if registered is None:
        import asyncio

        for method_name in ("get_tools", "list_tools"):
            method = getattr(mcp, method_name, None)
            if method:
                try:
                    result = asyncio.run(method())
                    registered = sorted(t.name for t in result)
                    break
                except Exception:
                    continue

    assert registered is not None, (
        "Could not discover registered tools. "
        f"FastMCP attrs: {[a for a in dir(mcp) if 'tool' in a.lower()]}"
    )
    assert registered == EXPECTED_TOOLS, (
        f"Expected {len(EXPECTED_TOOLS)} tools, got {len(registered)}.\n"
        f"Missing: {sorted(set(EXPECTED_TOOLS) - set(registered))}\n"
        f"Extra: {sorted(set(registered) - set(EXPECTED_TOOLS))}"
    )
