"""Specialized tools for operations that don't fit generic CRUD.

These handle searches, bulk operations, container management,
and other non-standard API patterns.
"""

from __future__ import annotations

from typing import Any

import requests
from fastmcp import FastMCP

from plane_mcp.client import get_plane_client_context
from plane_mcp.fork_api import fork_request


def register_specialized_tools(mcp: FastMCP) -> None:
    """Register all specialized (non-CRUD) tools."""

    # --- Search ---

    @mcp.tool()
    def search_work_items(
        query: str,
        expand: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
    ) -> dict:
        """Search work items across the workspace by text query.

        Args:
            query: Free-form text search (matches name, description, etc.)
            expand: Comma-separated fields to expand.
            fields: Comma-separated fields to include.
            order_by: Field to sort by. Prefix with '-' for descending.

        Returns:
            Search results dict.
        """
        _, ws = get_plane_client_context()
        params: dict[str, Any] = {"q": query}
        if expand:
            params["expand"] = expand
        if fields:
            params["fields"] = fields
        if order_by:
            params["order_by"] = order_by
        return fork_request("GET", f"workspaces/{ws}/work-items/search", params=params)

    @mcp.tool()
    def search_email_references(
        search: str | None = None,
        thread_id: str | None = None,
        folder: str | None = None,
        untriaged: bool | None = None,
    ) -> list[dict]:
        """Search email references indexed in the workspace.

        Args:
            search: Search term (matches subject, from_address, to_addresses).
                    Matches phrases, not individual terms — use single keywords.
            thread_id: Filter by thread ID.
            folder: Filter by folder (e.g., "INBOX", "Sent", "Archive").
            untriaged: If True, only return emails where triaged_at is null.

        Returns:
            List of email reference objects.
        """
        _, ws = get_plane_client_context()
        params: dict[str, Any] = {}
        if search:
            params["search"] = search
        if thread_id:
            params["thread_id"] = thread_id
        if folder:
            params["folder"] = folder
        if untriaged:
            params["untriaged"] = "true"
        return fork_request("GET", f"workspaces/{ws}/email-references", params=params)

    # --- Email operations ---

    @mcp.tool()
    def link_emails_to_issue(
        project_id: str,
        issue_id: str,
        email_reference_ids: list[str],
    ) -> dict:
        """Link one or more emails to an issue. Processes sequentially to handle 409 conflicts.

        Args:
            project_id: UUID of the project.
            issue_id: UUID of the work item.
            email_reference_ids: List of email reference UUIDs to link.
                NOTE: Must be full UUIDs, not short IDs (body fields don't resolve short IDs).

        Returns:
            Summary: {"linked": [...], "already_linked": [...], "errors": [...]}.
        """
        _, ws = get_plane_client_context()
        url = f"workspaces/{ws}/projects/{project_id}/issues/{issue_id}/linked-emails"
        results: dict[str, list] = {"linked": [], "already_linked": [], "errors": []}
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

    @mcp.tool()
    def unlink_email_from_issue(
        project_id: str,
        issue_id: str,
        email_reference_id: str,
    ) -> None:
        """Unlink an email reference from an issue.

        Args:
            project_id: UUID of the project.
            issue_id: UUID of the work item.
            email_reference_id: Full UUID of the email reference to unlink.
        """
        _, ws = get_plane_client_context()
        fork_request(
            "DELETE",
            f"workspaces/{ws}/projects/{project_id}/issues/{issue_id}/linked-emails",
            json={"email_reference_id": email_reference_id},
        )

    @mcp.tool()
    def mark_emails_triaged(
        email_reference_ids: list[str],
    ) -> dict:
        """Mark one or more email references as triaged (sets triaged_at to now).

        Args:
            email_reference_ids: List of email reference UUIDs.

        Returns:
            Summary: {"triaged": [...], "errors": [...]}.
        """
        _, ws = get_plane_client_context()
        results: dict[str, list] = {"triaged": [], "errors": []}
        for ref_id in email_reference_ids:
            try:
                fork_request("PATCH", f"workspaces/{ws}/email-references/{ref_id}", json={})
                results["triaged"].append(ref_id)
            except requests.HTTPError as e:
                results["errors"].append({"id": ref_id, "error": str(e)})
        return results

    # --- Cycle / Module item management ---

    @mcp.tool()
    def manage_cycle_items(
        project_id: str,
        cycle_id: str,
        action: str,
        work_item_ids: list[str] | None = None,
        new_cycle_id: str | None = None,
    ) -> list | dict | None:
        """Manage work items in a cycle.

        Args:
            project_id: UUID of the project.
            cycle_id: UUID of the cycle.
            action: One of "list", "add", "remove", "transfer".
            work_item_ids: Required for "add" (list of IDs) and "remove" (single ID in list).
            new_cycle_id: Required for "transfer" — target cycle UUID.

        Returns:
            For "list": list of work item dicts.
            For "add"/"remove"/"transfer": None on success.
        """
        _, ws = get_plane_client_context()
        base = f"workspaces/{ws}/projects/{project_id}/cycles/{cycle_id}"

        if action == "list":
            response = fork_request("GET", f"{base}/cycle-issues")
            if isinstance(response, dict) and "results" in response:
                return response["results"]
            return response or []

        if action == "add":
            if not work_item_ids:
                raise ValueError("work_item_ids required for 'add' action")
            fork_request("POST", f"{base}/cycle-issues", json={"issues": work_item_ids})
            return None

        if action == "remove":
            if not work_item_ids or len(work_item_ids) != 1:
                raise ValueError("work_item_ids must contain exactly one ID for 'remove' action")
            fork_request("DELETE", f"{base}/cycle-issues/{work_item_ids[0]}")
            return None

        if action == "transfer":
            if not new_cycle_id:
                raise ValueError("new_cycle_id required for 'transfer' action")
            fork_request("POST", f"{base}/transfer-issues", json={"new_cycle_id": new_cycle_id})
            return None

        raise ValueError(f"Invalid action '{action}'. Must be: list, add, remove, transfer")

    @mcp.tool()
    def manage_module_items(
        project_id: str,
        module_id: str,
        action: str,
        work_item_ids: list[str] | None = None,
    ) -> list | None:
        """Manage work items in a module.

        Args:
            project_id: UUID of the project.
            module_id: UUID of the module.
            action: One of "list", "add", "remove".
            work_item_ids: Required for "add" (list of IDs) and "remove" (single ID in list).

        Returns:
            For "list": list of work item dicts.
            For "add"/"remove": None on success.
        """
        _, ws = get_plane_client_context()
        base = f"workspaces/{ws}/projects/{project_id}/modules/{module_id}"

        if action == "list":
            response = fork_request("GET", f"{base}/module-issues")
            if isinstance(response, dict) and "results" in response:
                return response["results"]
            return response or []

        if action == "add":
            if not work_item_ids:
                raise ValueError("work_item_ids required for 'add' action")
            fork_request("POST", f"{base}/module-issues", json={"issues": work_item_ids})
            return None

        if action == "remove":
            if not work_item_ids or len(work_item_ids) != 1:
                raise ValueError("work_item_ids must contain exactly one ID for 'remove' action")
            fork_request("DELETE", f"{base}/module-issues/{work_item_ids[0]}")
            return None

        raise ValueError(f"Invalid action '{action}'. Must be: list, add, remove")

    # --- Archive / Unarchive ---

    @mcp.tool()
    def archive_resource(
        resource_type: str,
        resource_id: str,
        project_id: str | None = None,
        action: str = "archive",
    ) -> dict | None:
        """Archive or unarchive a cycle, module, or workspace page.

        Args:
            resource_type: One of "cycle", "module", "page".
            resource_id: UUID of the resource.
            project_id: Required for cycle and module.
            action: "archive" or "unarchive".

        Returns:
            Response dict or None.
        """
        _, ws = get_plane_client_context()

        if resource_type == "cycle":
            if not project_id:
                raise ValueError("project_id required for cycle archive")
            path = f"workspaces/{ws}/projects/{project_id}/cycles/{resource_id}"
        elif resource_type == "module":
            if not project_id:
                raise ValueError("project_id required for module archive")
            path = f"workspaces/{ws}/projects/{project_id}/modules/{resource_id}"
        elif resource_type == "page":
            path = f"workspaces/{ws}/pages/{resource_id}"
        else:
            raise ValueError(f"Cannot archive resource_type '{resource_type}'. Must be: cycle, module, page")

        if action == "archive":
            return fork_request("POST", f"{path}/archive")
        elif action == "unarchive":
            return fork_request("DELETE", f"{path}/archive")
        else:
            raise ValueError(f"Invalid action '{action}'. Must be: archive, unarchive")

    # --- Page children ---

    @mcp.tool()
    def list_page_children(
        page_id: str,
        project_id: str | None = None,
    ) -> list[dict]:
        """List child pages of a page, ordered by sort_order.

        Args:
            page_id: UUID of the parent page.
            project_id: If provided, looks up project page children.
                        If omitted, looks up workspace page children.

        Returns:
            List of child page dicts.
        """
        _, ws = get_plane_client_context()
        if project_id:
            path = f"workspaces/{ws}/projects/{project_id}/pages/{page_id}/children"
        else:
            path = f"workspaces/{ws}/pages/{page_id}/children"
        return fork_request("GET", path)

    # --- Project / Workspace info ---

    @mcp.tool()
    def get_project_info(
        project_id: str,
        info_type: str,
    ) -> list | dict:
        """Get project-level information.

        Args:
            project_id: UUID of the project.
            info_type: "members" — list of project member dicts.

        Returns:
            List of member dicts.
        """
        _, ws = get_plane_client_context()
        base = f"workspaces/{ws}/projects/{project_id}"

        if info_type == "members":
            return fork_request("GET", f"{base}/members")
        else:
            raise ValueError(f"Invalid info_type '{info_type}'. Must be: members")

    @mcp.tool()
    def get_workspace_info(
        info_type: str,
    ) -> list | dict:
        """Get workspace-level information.

        Args:
            info_type: "members" — list of workspace member dicts.

        Returns:
            List of member dicts.
        """
        _, ws = get_plane_client_context()

        if info_type == "members":
            return fork_request("GET", f"workspaces/{ws}/members")
        else:
            raise ValueError(f"Invalid info_type '{info_type}'. Must be: members")

    # --- Batch operations ---

    @mcp.tool()
    def batch_update_resources(
        updates: list[dict],
    ) -> dict:
        """Apply multiple updates in one tool call. Work items use a single
        backend request; other resource types fall back to sequential calls.

        Each entry in updates must have:
            resource_type: str — e.g. "work_item", "label", "page"
            resource_id: str — UUID of the resource
            data: dict — fields to update (partial)
            project_id: str | None — required for project-scoped resources
            work_item_id: str | None — required for work-item-scoped resources

        Returns:
            {"succeeded": int, "failed": int, "errors": [{"resource_id": ..., "error": ...}]}
        """
        from plane_mcp.tools.registry import RESOURCES, resolve_path

        _, ws = get_plane_client_context()
        succeeded = 0
        errors: list[dict] = []

        # Group work_item updates by project for bulk endpoint
        wi_by_project: dict[str, list[dict]] = {}
        other_updates: list[dict] = []

        for entry in updates:
            if entry.get("resource_type") == "work_item" and entry.get("project_id"):
                pid = entry["project_id"]
                wi_by_project.setdefault(pid, []).append(entry)
            else:
                other_updates.append(entry)

        # Bulk work item updates via backend endpoint (one HTTP call per project)
        for project_id, entries in wi_by_project.items():
            bulk_payload = []
            for entry in entries:
                item = dict(entry["data"])
                item["id"] = entry["resource_id"]
                bulk_payload.append(item)
            try:
                result = fork_request(
                    "POST",
                    f"workspaces/{ws}/projects/{project_id}/bulk-update-issues",
                    json={"updates": bulk_payload},
                )
                succeeded += len(result.get("updated", []))
                for rid, err in result.get("errors", {}).items():
                    errors.append({"resource_id": rid, "error": err})
            except Exception as e:
                # If bulk endpoint fails entirely, fall back to sequential
                for entry in entries:
                    try:
                        path = resolve_path("work_item", ws, project_id=project_id, resource_id=entry["resource_id"])
                        fork_request("PATCH", path, json=entry["data"])
                        succeeded += 1
                    except Exception as inner_e:
                        errors.append({"resource_id": entry["resource_id"], "error": str(inner_e)})

        # Other resource types: sequential updates
        for entry in other_updates:
            resource_type = entry["resource_type"]
            resource_id = entry["resource_id"]
            data = entry["data"]
            project_id = entry.get("project_id")
            work_item_id = entry.get("work_item_id")

            if resource_type not in RESOURCES:
                errors.append({"resource_id": resource_id, "error": f"Unknown resource_type '{resource_type}'"})
                continue

            try:
                path = resolve_path(resource_type, ws, project_id=project_id, work_item_id=work_item_id, resource_id=resource_id)
                fork_request("PATCH", path, json=data)
                succeeded += 1
            except Exception as e:
                errors.append({"resource_id": resource_id, "error": str(e)})

        return {"succeeded": succeeded, "failed": len(errors), "errors": errors}

    # --- Current user ---

    @mcp.tool()
    def get_me() -> dict:
        """Get current authenticated user information.

        Returns:
            User dict with id, display_name, email, etc.
        """
        _, ws = get_plane_client_context()
        return fork_request("GET", "users/me")
