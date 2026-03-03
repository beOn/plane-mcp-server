"""Page-related tools for Plane MCP Server (fork-extended)."""

from typing import Any

from fastmcp import FastMCP

from plane_mcp.client import get_plane_client_context
from plane_mcp.fork_api import fork_request


def register_page_tools(mcp: FastMCP) -> None:
    """Register all page-related tools with the MCP server."""

    # --- Workspace pages ---

    @mcp.tool()
    def list_workspace_pages() -> list[dict[str, Any]]:
        """
        List all top-level workspace pages.

        Returns:
            List of workspace page objects with name, id, child_page_ids, etc.
        """
        _, ws = get_plane_client_context()
        return fork_request("GET", f"workspaces/{ws}/pages")

    @mcp.tool()
    def retrieve_workspace_page(page_id: str) -> dict[str, Any]:
        """
        Retrieve a workspace page by ID, including description_html and issue_ids.

        Args:
            page_id: UUID of the page

        Returns:
            Full page object with description and linked issue IDs
        """
        _, ws = get_plane_client_context()
        return fork_request("GET", f"workspaces/{ws}/pages/{page_id}")

    @mcp.tool()
    def create_workspace_page(
        name: str,
        description_html: str = "<p></p>",
        parent: str | None = None,
        access: int = 0,
    ) -> dict[str, Any]:
        """
        Create a workspace page.

        Args:
            name: Page name/title
            description_html: Page content in HTML format
            parent: UUID of parent page for nesting (optional)
            access: 0 for public (visible to all members), 1 for private (owner only)

        Returns:
            Created page object
        """
        _, ws = get_plane_client_context()
        data = {"name": name, "description_html": description_html, "access": access}
        if parent:
            data["parent"] = parent
        return fork_request("POST", f"workspaces/{ws}/pages", json=data)

    @mcp.tool()
    def update_workspace_page(
        page_id: str,
        name: str | None = None,
        description_html: str | None = None,
        parent: str | None = None,
        access: int | None = None,
    ) -> dict[str, Any]:
        """
        Update a workspace page.

        Args:
            page_id: UUID of the page to update
            name: New page name (optional)
            description_html: New page content in HTML (optional)
            parent: New parent page UUID, or "null" to move to top level (optional)
            access: 0 for public, 1 for private (optional)

        Returns:
            Updated page object
        """
        _, ws = get_plane_client_context()
        data = {}
        if name is not None:
            data["name"] = name
        if description_html is not None:
            data["description_html"] = description_html
        if parent is not None:
            data["parent"] = None if parent == "null" else parent
        if access is not None:
            data["access"] = access
        return fork_request("PATCH", f"workspaces/{ws}/pages/{page_id}", json=data)

    @mcp.tool()
    def archive_workspace_page(page_id: str) -> dict[str, Any]:
        """
        Archive a workspace page and its descendants.

        Args:
            page_id: UUID of the page to archive

        Returns:
            Object with archived_at timestamp
        """
        _, ws = get_plane_client_context()
        return fork_request("POST", f"workspaces/{ws}/pages/{page_id}/archive")

    @mcp.tool()
    def list_workspace_page_children(page_id: str) -> list[dict[str, Any]]:
        """
        List child pages of a workspace page, ordered by sort_order.

        Args:
            page_id: UUID of the parent page

        Returns:
            List of child page objects
        """
        _, ws = get_plane_client_context()
        return fork_request("GET", f"workspaces/{ws}/pages/{page_id}/children")

    # --- Project pages ---

    @mcp.tool()
    def list_project_pages(project_id: str) -> list[dict[str, Any]]:
        """
        List all top-level pages in a project.

        Args:
            project_id: UUID of the project

        Returns:
            List of project page objects
        """
        _, ws = get_plane_client_context()
        return fork_request("GET", f"workspaces/{ws}/projects/{project_id}/pages")

    @mcp.tool()
    def retrieve_project_page(project_id: str, page_id: str) -> dict[str, Any]:
        """
        Retrieve a project page by ID, including description_html and issue_ids.

        Args:
            project_id: UUID of the project
            page_id: UUID of the page

        Returns:
            Full page object with description and linked issue IDs
        """
        _, ws = get_plane_client_context()
        return fork_request("GET", f"workspaces/{ws}/projects/{project_id}/pages/{page_id}")

    @mcp.tool()
    def create_project_page(
        project_id: str,
        name: str,
        description_html: str = "<p></p>",
        parent: str | None = None,
        access: int = 0,
    ) -> dict[str, Any]:
        """
        Create a project page.

        Args:
            project_id: UUID of the project
            name: Page name/title
            description_html: Page content in HTML format
            parent: UUID of parent page for nesting (optional)
            access: 0 for public, 1 for private

        Returns:
            Created page object
        """
        _, ws = get_plane_client_context()
        data = {"name": name, "description_html": description_html, "access": access}
        if parent:
            data["parent"] = parent
        return fork_request("POST", f"workspaces/{ws}/projects/{project_id}/pages", json=data)

    @mcp.tool()
    def update_project_page(
        project_id: str,
        page_id: str,
        name: str | None = None,
        description_html: str | None = None,
        parent: str | None = None,
        access: int | None = None,
    ) -> dict[str, Any]:
        """
        Update a project page.

        Args:
            project_id: UUID of the project
            page_id: UUID of the page to update
            name: New page name (optional)
            description_html: New page content in HTML (optional)
            parent: New parent page UUID, or "null" to move to top level (optional)
            access: 0 for public, 1 for private (optional)

        Returns:
            Updated page object
        """
        _, ws = get_plane_client_context()
        data = {}
        if name is not None:
            data["name"] = name
        if description_html is not None:
            data["description_html"] = description_html
        if parent is not None:
            data["parent"] = None if parent == "null" else parent
        if access is not None:
            data["access"] = access
        return fork_request(
            "PATCH", f"workspaces/{ws}/projects/{project_id}/pages/{page_id}", json=data
        )

    @mcp.tool()
    def list_project_page_children(
        project_id: str, page_id: str
    ) -> list[dict[str, Any]]:
        """
        List child pages of a project page, ordered by sort_order.

        Args:
            project_id: UUID of the project
            page_id: UUID of the parent page

        Returns:
            List of child page objects
        """
        _, ws = get_plane_client_context()
        return fork_request(
            "GET", f"workspaces/{ws}/projects/{project_id}/pages/{page_id}/children"
        )
