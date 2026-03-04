"""Work item type tools for Plane MCP Server.

Uses ForkWorkItemTypes to hit workspace-scoped /api/v1/workspaces/{slug}/issue-types/
instead of the upstream project-scoped endpoints (which don't exist in the fork).
"""

from typing import Any

from fastmcp import FastMCP
from plane.models.work_item_types import (
    CreateWorkItemType,
    UpdateWorkItemType,
    WorkItemType,
)

from plane_mcp.client import get_plane_client_context
from plane_mcp.fork_work_item_types import ForkWorkItemTypes


def register_work_item_type_tools(mcp: FastMCP) -> None:
    """Register all work item type-related tools with the MCP server."""

    @mcp.tool()
    def list_work_item_types() -> list[WorkItemType]:
        """
        List all work item types in the workspace.

        Returns:
            List of WorkItemType objects
        """
        client, workspace_slug = get_plane_client_context()
        fork_types = ForkWorkItemTypes(client.config)
        return fork_types.list(workspace_slug=workspace_slug)

    @mcp.tool()
    def create_work_item_type(
        name: str,
        description: str | None = None,
        logo_props: Any | None = None,
        is_epic: bool | None = None,
        is_default: bool | None = None,
        is_active: bool | None = None,
        level: int | None = None,
    ) -> WorkItemType:
        """
        Create a new work item type.

        Args:
            name: Work item type name
            description: Work item type description
            logo_props: Icon/logo properties dict
            is_epic: Whether this is an epic type
            is_default: Whether this is the default type
            is_active: Whether the type is active
            level: Sort level (lower = higher priority)

        Returns:
            Created WorkItemType object
        """
        client, workspace_slug = get_plane_client_context()
        fork_types = ForkWorkItemTypes(client.config)

        data = CreateWorkItemType(
            name=name,
            description=description,
            is_epic=is_epic,
            is_active=is_active,
        )

        return fork_types.create(workspace_slug=workspace_slug, data=data)

    @mcp.tool()
    def retrieve_work_item_type(
        work_item_type_id: str,
    ) -> WorkItemType:
        """
        Retrieve a work item type by ID.

        Args:
            work_item_type_id: UUID of the work item type

        Returns:
            WorkItemType object
        """
        client, workspace_slug = get_plane_client_context()
        fork_types = ForkWorkItemTypes(client.config)
        return fork_types.retrieve(
            workspace_slug=workspace_slug,
            type_id=work_item_type_id,
        )

    @mcp.tool()
    def update_work_item_type(
        work_item_type_id: str,
        name: str | None = None,
        description: str | None = None,
        logo_props: Any | None = None,
        is_epic: bool | None = None,
        is_default: bool | None = None,
        is_active: bool | None = None,
        level: int | None = None,
    ) -> WorkItemType:
        """
        Update a work item type by ID.

        Args:
            work_item_type_id: UUID of the work item type
            name: Work item type name
            description: Work item type description
            logo_props: Icon/logo properties dict
            is_epic: Whether this is an epic type
            is_default: Whether this is the default type
            is_active: Whether the type is active
            level: Sort level (lower = higher priority)

        Returns:
            Updated WorkItemType object
        """
        client, workspace_slug = get_plane_client_context()
        fork_types = ForkWorkItemTypes(client.config)

        data = UpdateWorkItemType(
            name=name,
            description=description,
            is_epic=is_epic,
            is_active=is_active,
        )

        return fork_types.update(
            workspace_slug=workspace_slug,
            type_id=work_item_type_id,
            data=data,
        )

    @mcp.tool()
    def delete_work_item_type(
        work_item_type_id: str,
    ) -> None:
        """
        Delete (soft-delete) a work item type by ID.

        Args:
            work_item_type_id: UUID of the work item type
        """
        client, workspace_slug = get_plane_client_context()
        fork_types = ForkWorkItemTypes(client.config)
        fork_types.delete(
            workspace_slug=workspace_slug,
            type_id=work_item_type_id,
        )
