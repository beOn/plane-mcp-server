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

    @mcp.tool()
    def update_issue_template(
        template_id: str,
        name: str | None = None,
        description: str | None = None,
        issue_type: str | None = None,
        template_data: dict[str, Any] | None = None,
        is_active: bool | None = None,
        sort_order: float | None = None,
    ) -> dict[str, Any]:
        """
        Update an issue template (partial update).

        Args:
            template_id: UUID of the template to update
            name: Template display name
            description: Template description text
            issue_type: UUID of the issue type to associate (or null to clear)
            template_data: JSON object with default field values
                (description_html, priority, label_ids, assignee_ids, custom_field_values)
            is_active: Whether the template is active
            sort_order: Numeric sort order

        Returns:
            Updated template object
        """
        _, ws = get_plane_client_context()
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if issue_type is not None:
            data["issue_type"] = issue_type
        if template_data is not None:
            data["template_data"] = template_data
        if is_active is not None:
            data["is_active"] = is_active
        if sort_order is not None:
            data["sort_order"] = sort_order
        return fork_request(
            "PATCH", f"workspaces/{ws}/issue-templates/{template_id}", json=data
        )
