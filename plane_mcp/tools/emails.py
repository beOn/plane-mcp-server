"""Email reference tools for Plane MCP Server (fork-only)."""

from typing import Any

from fastmcp import FastMCP

from plane_mcp.client import get_plane_client_context
from plane_mcp.fork_api import fork_request


def register_email_tools(mcp: FastMCP) -> None:
    """Register all email-related tools with the MCP server."""

    @mcp.tool()
    def search_email_references(
        search: str | None = None,
        thread_id: str | None = None,
        folder: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search email references indexed in the workspace.

        Args:
            search: Search term (matches subject, from_address, to_addresses)
            thread_id: Filter by thread ID
            folder: Filter by folder (e.g., "INBOX", "Sent", "Archive")

        Returns:
            List of email reference objects (id, message_id, subject, from_address, date, body_preview, folder)
        """
        _, ws = get_plane_client_context()
        params = {}
        if search:
            params["search"] = search
        if thread_id:
            params["thread_id"] = thread_id
        if folder:
            params["folder"] = folder
        return fork_request("GET", f"workspaces/{ws}/email-references", params=params)

    @mcp.tool()
    def get_email_reference(email_reference_id: str) -> dict[str, Any]:
        """
        Get full details of an email reference including the complete body.

        Args:
            email_reference_id: UUID of the email reference

        Returns:
            Full email reference with body_plain, to_addresses, cc_addresses, etc.
        """
        _, ws = get_plane_client_context()
        return fork_request(
            "GET", f"workspaces/{ws}/email-references/{email_reference_id}"
        )

    @mcp.tool()
    def list_issue_linked_emails(
        project_id: str, issue_id: str
    ) -> list[dict[str, Any]]:
        """
        List emails linked to a specific issue.

        Args:
            project_id: UUID of the project
            issue_id: UUID of the issue

        Returns:
            List of linked email objects (id, email_reference_id, subject, from_address, date, body_preview)
        """
        _, ws = get_plane_client_context()
        return fork_request(
            "GET",
            f"workspaces/{ws}/projects/{project_id}/issues/{issue_id}/linked-emails",
        )

    @mcp.tool()
    def link_email_to_issue(
        project_id: str, issue_id: str, email_reference_id: str
    ) -> dict[str, Any]:
        """
        Link an email reference to an issue.

        Args:
            project_id: UUID of the project
            issue_id: UUID of the issue
            email_reference_id: UUID of the email reference to link

        Returns:
            Link object with id, email_reference_id, and subject
        """
        _, ws = get_plane_client_context()
        return fork_request(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/issues/{issue_id}/linked-emails",
            json={"email_reference_id": email_reference_id},
        )

    @mcp.tool()
    def unlink_email_from_issue(
        project_id: str, issue_id: str, email_reference_id: str
    ) -> None:
        """
        Unlink an email reference from an issue.

        Args:
            project_id: UUID of the project
            issue_id: UUID of the issue
            email_reference_id: UUID of the email reference to unlink
        """
        _, ws = get_plane_client_context()
        fork_request(
            "DELETE",
            f"workspaces/{ws}/projects/{project_id}/issues/{issue_id}/linked-emails",
            json={"email_reference_id": email_reference_id},
        )

    @mcp.tool()
    def list_issue_linked_pages(
        project_id: str, issue_id: str
    ) -> list[dict[str, Any]]:
        """
        List pages that @-mention a specific issue (reverse lookup via page editor mentions).

        Args:
            project_id: UUID of the project
            issue_id: UUID of the issue

        Returns:
            List of linked page objects (id, name, is_global, page_path, project_id, updated_at)
        """
        _, ws = get_plane_client_context()
        return fork_request(
            "GET",
            f"workspaces/{ws}/projects/{project_id}/issues/{issue_id}/linked-pages",
        )
