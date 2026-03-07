"""Email reference tools for Plane MCP Server (fork-only)."""

from typing import Any

import requests
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
        untriaged: bool | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search email references indexed in the workspace.

        Args:
            search: Search term (matches subject, from_address, to_addresses)
            thread_id: Filter by thread ID
            folder: Filter by folder (e.g., "INBOX", "Sent", "Archive")
            untriaged: If True, only return emails where triaged_at is null

        Returns:
            List of email reference objects (id, message_id, subject, from_address, date, body_preview, folder, triaged_at)
        """
        _, ws = get_plane_client_context()
        params = {}
        if search:
            params["search"] = search
        if thread_id:
            params["thread_id"] = thread_id
        if folder:
            params["folder"] = folder
        if untriaged:
            params["untriaged"] = "true"
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
            issue_id: UUID of the work item

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
            issue_id: UUID of the work item
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
            issue_id: UUID of the work item
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
            issue_id: UUID of the work item

        Returns:
            List of linked page objects (id, name, is_global, page_path, project_id, updated_at)
        """
        _, ws = get_plane_client_context()

        return fork_request(
            "GET",
            f"workspaces/{ws}/projects/{project_id}/issues/{issue_id}/linked-pages",
        )

    @mcp.tool()
    def mark_email_triaged(email_reference_id: str) -> dict[str, Any]:
        """
        Mark an email reference as triaged (sets triaged_at to now).

        Args:
            email_reference_id: UUID of the email reference

        Returns:
            Updated email reference object
        """
        _, ws = get_plane_client_context()
        return fork_request(
            "PATCH",
            f"workspaces/{ws}/email-references/{email_reference_id}",
            json={},
        )

    @mcp.tool()
    def mark_emails_triaged(email_reference_ids: list[str]) -> dict[str, Any]:
        """
        Mark multiple email references as triaged. Processes sequentially.

        Args:
            email_reference_ids: List of email reference UUIDs to mark as triaged

        Returns:
            Summary dict with 'triaged' (list of IDs marked) and 'errors' (list of {id, error})
        """
        _, ws = get_plane_client_context()
        results: dict[str, list] = {"triaged": [], "errors": []}
        for ref_id in email_reference_ids:
            try:
                fork_request(
                    "PATCH",
                    f"workspaces/{ws}/email-references/{ref_id}",
                    json={},
                )
                results["triaged"].append(ref_id)
            except requests.HTTPError as e:
                results["errors"].append({"id": ref_id, "error": str(e)})
        return results

    @mcp.tool()
    def bulk_link_emails_to_issue(
        project_id: str,
        issue_id: str,
        email_reference_ids: list[str],
    ) -> dict[str, Any]:
        """
        Link multiple emails to an issue in one call.

        Processes each email sequentially and gracefully handles
        already-linked emails (409 Conflict) instead of failing.

        Args:
            project_id: UUID of the project
            issue_id: UUID of the work item
            email_reference_ids: List of email reference UUIDs to link

        Returns:
            Summary dict with 'linked' (list of ref IDs successfully linked),
            'already_linked' (list of ref IDs that were already linked),
            and 'errors' (list of {id, error} for unexpected failures)
        """
        _, ws = get_plane_client_context()

        url = f"workspaces/{ws}/projects/{project_id}/issues/{issue_id}/linked-emails"

        results: dict[str, list] = {
            "linked": [],
            "already_linked": [],
            "errors": [],
        }
        for ref_id in email_reference_ids:
            try:
                fork_request("POST", url, json={"email_reference_id": ref_id})
                results["linked"].append(ref_id)
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 409:
                    results["already_linked"].append(ref_id)
                else:
                    results["errors"].append({"id": ref_id, "error": str(e)})
        return results
