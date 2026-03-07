"""Generic CRUD tools for all Plane resources.

Five tools replace ~80 individual list/create/get/update/delete tools.
All use fork_request() for consistent dict returns.
"""

from __future__ import annotations

from fastmcp import FastMCP

from plane_mcp.client import get_plane_client_context
from plane_mcp.fork_api import fork_request
from plane_mcp.tools.registry import (
    build_params,
    extract_results,
    get_resource_def,
    resolve_path,
)

# Resource type reference table used in docstrings
_RESOURCE_TABLE = """
Resource types and required scope params:

  Workspace-scoped (no extra params):
    project, initiative, work_item_type, template, email_reference (read-only)

  Project-scoped (needs project_id):
    label, state, cycle, module, work_item, intake_item, page*
    work_item_property (also needs type_id)

  Work-item-scoped (needs project_id + work_item_id):
    comment, link, relation, activity (read-only), work_log
    linked_email (read-only), linked_page (read-only)

  *page: If project_id is given, operates on project pages.
         If project_id is omitted, operates on workspace pages.
"""


def register_crud_tools(mcp: FastMCP) -> None:
    """Register the 5 generic CRUD tools."""

    @mcp.tool()
    def list_resources(
        resource_type: str,
        project_id: str | None = None,
        work_item_id: str | None = None,
        type_id: str | None = None,
        cursor: str | None = None,
        per_page: int | None = None,
        order_by: str | None = None,
        expand: str | None = None,
        fields: str | None = None,
    ) -> list | dict:
        f"""List resources of a given type.
{_RESOURCE_TABLE}
        Args:
            resource_type: One of the resource type names above.
            project_id: Required for project-scoped and work-item-scoped resources.
            work_item_id: Required for work-item-scoped resources.
            type_id: Required for work_item_property.
            cursor: Pagination cursor for next page.
            per_page: Results per page (1-100).
            order_by: Field to sort by. Prefix with '-' for descending.
            expand: Comma-separated fields to expand (e.g. "assignees,labels,state").
            fields: Comma-separated fields to include in response.

        Returns:
            List of resource dicts, or paginated response dict.
        """
        _, ws = get_plane_client_context()
        rdef = get_resource_def(resource_type, project_id)
        path = resolve_path(
            resource_type, ws,
            project_id=project_id,
            work_item_id=work_item_id,
            type_id=type_id,
        )
        params = build_params(
            cursor=cursor, per_page=per_page, order_by=order_by,
            expand=expand, fields=fields,
        )
        response = fork_request("GET", path, params=params)
        return extract_results(response, rdef.list_key)

    @mcp.tool()
    def create_resource(
        resource_type: str,
        data: dict,
        project_id: str | None = None,
        work_item_id: str | None = None,
        type_id: str | None = None,
    ) -> dict:
        f"""Create a new resource.
{_RESOURCE_TABLE}
        Args:
            resource_type: One of the resource type names above.
            data: Resource fields as a dict (varies by type).
            project_id: Required for project-scoped and work-item-scoped resources.
            work_item_id: Required for work-item-scoped resources.
            type_id: Required for work_item_property.

        Returns:
            Created resource dict.
        """
        _, ws = get_plane_client_context()
        rdef = get_resource_def(resource_type, project_id)
        if rdef.read_only:
            raise ValueError(f"Resource type '{resource_type}' is read-only.")
        path = resolve_path(
            resource_type, ws,
            project_id=project_id,
            work_item_id=work_item_id,
            type_id=type_id,
        )
        return fork_request("POST", path, json=data)

    @mcp.tool()
    def get_resource(
        resource_type: str,
        resource_id: str,
        project_id: str | None = None,
        work_item_id: str | None = None,
        type_id: str | None = None,
        expand: str | None = None,
        fields: str | None = None,
        identifier: str | None = None,
    ) -> dict:
        f"""Get a single resource by ID.
{_RESOURCE_TABLE}
        Args:
            resource_type: One of the resource type names above.
            resource_id: UUID of the resource to retrieve.
            project_id: Required for project-scoped and work-item-scoped resources.
            work_item_id: Required for work-item-scoped resources.
            type_id: Required for work_item_property.
            expand: Comma-separated fields to expand.
            fields: Comma-separated fields to include.
            identifier: For work items only — "EDI-42" style lookup. Overrides resource_id
                and project_id (uses workspace-level endpoint).

        Returns:
            Resource dict.
        """
        _, ws = get_plane_client_context()
        params = build_params(expand=expand, fields=fields)

        if identifier and resource_type == "work_item":
            # Workspace-level lookup by project identifier + sequence number
            return fork_request(
                "GET",
                f"workspaces/{ws}/work-items/{identifier}",
                params=params,
            )

        path = resolve_path(
            resource_type, ws,
            project_id=project_id,
            work_item_id=work_item_id,
            type_id=type_id,
            resource_id=resource_id,
        )
        return fork_request("GET", path, params=params)

    @mcp.tool()
    def update_resource(
        resource_type: str,
        resource_id: str,
        data: dict,
        project_id: str | None = None,
        work_item_id: str | None = None,
        type_id: str | None = None,
    ) -> dict:
        f"""Update a resource (partial update / PATCH).
{_RESOURCE_TABLE}
        Args:
            resource_type: One of the resource type names above.
            resource_id: UUID of the resource to update.
            data: Fields to update as a dict (partial — only include changed fields).
            project_id: Required for project-scoped and work-item-scoped resources.
            work_item_id: Required for work-item-scoped resources.
            type_id: Required for work_item_property.

        Returns:
            Updated resource dict.
        """
        _, ws = get_plane_client_context()
        rdef = get_resource_def(resource_type, project_id)
        if rdef.read_only:
            raise ValueError(f"Resource type '{resource_type}' is read-only.")
        path = resolve_path(
            resource_type, ws,
            project_id=project_id,
            work_item_id=work_item_id,
            type_id=type_id,
            resource_id=resource_id,
        )
        return fork_request("PATCH", path, json=data)

    @mcp.tool()
    def delete_resource(
        resource_type: str,
        resource_id: str,
        project_id: str | None = None,
        work_item_id: str | None = None,
        type_id: str | None = None,
    ) -> None:
        f"""Delete a resource by ID.
{_RESOURCE_TABLE}
        Args:
            resource_type: One of the resource type names above.
            resource_id: UUID of the resource to delete.
            project_id: Required for project-scoped and work-item-scoped resources.
            work_item_id: Required for work-item-scoped resources.
            type_id: Required for work_item_property.
        """
        _, ws = get_plane_client_context()
        rdef = get_resource_def(resource_type, project_id)
        if rdef.read_only:
            raise ValueError(f"Resource type '{resource_type}' is read-only.")
        path = resolve_path(
            resource_type, ws,
            project_id=project_id,
            work_item_id=work_item_id,
            type_id=type_id,
            resource_id=resource_id,
        )
        fork_request("DELETE", path)
