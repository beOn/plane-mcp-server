"""Issue template tools for Plane MCP Server (fork-only)."""

from typing import Any

from fastmcp import FastMCP

from plane_mcp.client import get_plane_client_context
from plane_mcp.fork_api import fork_request


def register_template_tools(mcp: FastMCP) -> None:
    """Register all template-related tools with the MCP server."""

    @mcp.tool()
    def list_issue_templates(
        issue_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List active issue templates in the workspace.

        Args:
            issue_type: Filter by issue type UUID (optional)

        Returns:
            List of template objects (id, name, issue_type, is_active)
        """
        _, ws = get_plane_client_context()
        params = {}
        if issue_type:
            params["issue_type"] = issue_type
        return fork_request(
            "GET", f"workspaces/{ws}/issue-templates", params=params
        )

    @mcp.tool()
    def get_issue_template(template_id: str) -> dict[str, Any]:
        """
        Get full details of an issue template including template_data.

        Args:
            template_id: UUID of the template

        Returns:
            Full template object with name, description, issue_type, template_data, sort_order
        """
        _, ws = get_plane_client_context()
        return fork_request(
            "GET", f"workspaces/{ws}/issue-templates/{template_id}"
        )
