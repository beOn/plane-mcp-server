"""Work item-related tools for Plane MCP Server.

All tools use fork_request() for HTTP calls, bypassing the upstream SDK's
pydantic models which are too strict (e.g., WorkItemDetail.labels expects
Label dicts but the API returns UUID strings; PaginatedWorkItemResponse
rejects expanded state dicts). Returns raw dicts for maximum compatibility.
"""

from fastmcp import FastMCP

from plane_mcp.client import get_plane_client_context
from plane_mcp.fork_api import fork_request


def register_work_item_tools(mcp: FastMCP) -> None:
    """Register all work item-related tools with the MCP server."""

    @mcp.tool()
    def list_work_items(
        project_id: str,
        cursor: str | None = None,
        per_page: int | None = None,
        expand: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        external_id: str | None = None,
        external_source: str | None = None,
    ) -> list[dict]:
        """
        List all work items in a project.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project
            cursor: Pagination cursor for getting next set of results
            per_page: Number of results per page (1-100)
            expand: Comma-separated list of related fields to expand in response
            fields: Comma-separated list of fields to include in response
            order_by: Field to order results by. Prefix with '-' for descending order
            external_id: External system identifier for filtering or lookup
            external_source: External system source name for filtering or lookup

        Returns:
            List of work item dicts
        """
        _, workspace_slug = get_plane_client_context()

        params: dict = {}
        if cursor:
            params["cursor"] = cursor
        if per_page:
            params["per_page"] = per_page
        if expand:
            params["expand"] = expand
        if fields:
            params["fields"] = fields
        if order_by:
            params["order_by"] = order_by
        if external_id:
            params["external_id"] = external_id
        if external_source:
            params["external_source"] = external_source

        response = fork_request(
            "GET",
            f"workspaces/{workspace_slug}/projects/{project_id}/work-items",
            params=params,
        )

        if isinstance(response, dict) and "results" in response:
            return response["results"]
        if isinstance(response, list):
            return response
        return []

    @mcp.tool()
    def create_work_item(
        project_id: str,
        name: str,
        assignees: list[str] | None = None,
        labels: list[str] | None = None,
        type_id: str | None = None,
        point: int | None = None,
        description_html: str | None = None,
        description_stripped: str | None = None,
        priority: str | None = None,
        start_date: str | None = None,
        target_date: str | None = None,
        sort_order: float | None = None,
        is_draft: bool | None = None,
        external_source: str | None = None,
        external_id: str | None = None,
        parent: str | None = None,
        state: str | None = None,
        estimate_point: str | None = None,
        type: str | None = None,
    ) -> dict:
        """
        Create a new work item.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project
            name: Work item name (required)
            assignees: List of user IDs to assign to the work item
            labels: List of label IDs to attach to the work item
            type_id: UUID of the work item type
            point: Story point value
            description_html: HTML description of the work item
            description_stripped: Plain text description (stripped of HTML)
            priority: Priority level (urgent, high, medium, low, none)
            start_date: Start date (ISO 8601 format)
            target_date: Target/end date (ISO 8601 format)
            sort_order: Sort order value
            is_draft: Whether the work item is a draft
            external_source: External system source name
            external_id: External system identifier
            parent: UUID of the parent work item
            state: UUID of the state
            estimate_point: Estimate point value
            type: Work item type identifier

        Returns:
            Created work item dict
        """
        _, workspace_slug = get_plane_client_context()

        body: dict = {"name": name}
        if assignees is not None:
            body["assignees"] = assignees
        if labels is not None:
            body["labels"] = labels
        if type_id is not None:
            body["type_id"] = type_id
        if point is not None:
            body["point"] = point
        if description_html is not None:
            body["description_html"] = description_html
        if description_stripped is not None:
            body["description_stripped"] = description_stripped
        if priority is not None:
            body["priority"] = priority
        if start_date is not None:
            body["start_date"] = start_date
        if target_date is not None:
            body["target_date"] = target_date
        if sort_order is not None:
            body["sort_order"] = sort_order
        if is_draft is not None:
            body["is_draft"] = is_draft
        if external_source is not None:
            body["external_source"] = external_source
        if external_id is not None:
            body["external_id"] = external_id
        if parent is not None:
            body["parent"] = parent
        if state is not None:
            body["state"] = state
        if estimate_point is not None:
            body["estimate_point"] = estimate_point
        if type is not None:
            body["type"] = type

        return fork_request(
            "POST",
            f"workspaces/{workspace_slug}/projects/{project_id}/work-items",
            json=body,
        )

    @mcp.tool()
    def retrieve_work_item(
        project_id: str,
        work_item_id: str,
        expand: str | None = None,
        fields: str | None = None,
    ) -> dict:
        """
        Retrieve a work item by ID.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project
            work_item_id: UUID of the work item
            expand: Comma-separated fields to expand (e.g., "assignees,labels,state")
            fields: Comma-separated fields to include in response

        Returns:
            Work item dict with all fields
        """
        _, workspace_slug = get_plane_client_context()

        params: dict = {}
        if expand:
            params["expand"] = expand
        if fields:
            params["fields"] = fields

        return fork_request(
            "GET",
            f"workspaces/{workspace_slug}/projects/{project_id}/work-items/{work_item_id}",
            params=params,
        )

    @mcp.tool()
    def retrieve_work_item_by_identifier(
        project_identifier: str,
        issue_identifier: int,
        expand: str | None = None,
        fields: str | None = None,
    ) -> dict:
        """
        Retrieve a work item by project identifier and issue sequence number.

        Args:
            workspace_slug: The workspace slug identifier
            project_identifier: Project identifier string (e.g., "MP" for "My Project")
            issue_identifier: Issue sequence number (e.g., 1, 2, 3)
            expand: Comma-separated fields to expand (e.g., "assignees,labels,state")
            fields: Comma-separated list of fields to include in response

        Returns:
            Work item dict with all fields
        """
        _, workspace_slug = get_plane_client_context()

        params: dict = {}
        if expand:
            params["expand"] = expand
        if fields:
            params["fields"] = fields

        return fork_request(
            "GET",
            f"workspaces/{workspace_slug}/work-items/{project_identifier}-{issue_identifier}",
            params=params,
        )

    @mcp.tool()
    def update_work_item(
        project_id: str,
        work_item_id: str,
        name: str | None = None,
        assignees: list[str] | None = None,
        labels: list[str] | None = None,
        type_id: str | None = None,
        point: int | None = None,
        description_html: str | None = None,
        description_stripped: str | None = None,
        priority: str | None = None,
        start_date: str | None = None,
        target_date: str | None = None,
        sort_order: float | None = None,
        is_draft: bool | None = None,
        external_source: str | None = None,
        external_id: str | None = None,
        parent: str | None = None,
        state: str | None = None,
        estimate_point: str | None = None,
        type: str | None = None,
    ) -> dict:
        """
        Update a work item by ID.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project
            work_item_id: UUID of the work item
            name: Work item name
            assignees: List of user IDs to assign to the work item
            labels: List of label IDs to attach to the work item
            type_id: UUID of the work item type
            point: Story point value
            description_html: HTML description of the work item
            description_stripped: Plain text description (stripped of HTML)
            priority: Priority level (urgent, high, medium, low, none)
            start_date: Start date (ISO 8601 format)
            target_date: Target/end date (ISO 8601 format)
            sort_order: Sort order value
            is_draft: Whether the work item is a draft
            external_source: External system source name
            external_id: External system identifier
            parent: UUID of the parent work item
            state: UUID of the state
            estimate_point: Estimate point value
            type: Work item type identifier

        Returns:
            Updated work item dict
        """
        _, workspace_slug = get_plane_client_context()

        body: dict = {}
        if name is not None:
            body["name"] = name
        if assignees is not None:
            body["assignees"] = assignees
        if labels is not None:
            body["labels"] = labels
        if type_id is not None:
            body["type_id"] = type_id
        if point is not None:
            body["point"] = point
        if description_html is not None:
            body["description_html"] = description_html
        if description_stripped is not None:
            body["description_stripped"] = description_stripped
        if priority is not None:
            body["priority"] = priority
        if start_date is not None:
            body["start_date"] = start_date
        if target_date is not None:
            body["target_date"] = target_date
        if sort_order is not None:
            body["sort_order"] = sort_order
        if is_draft is not None:
            body["is_draft"] = is_draft
        if external_source is not None:
            body["external_source"] = external_source
        if external_id is not None:
            body["external_id"] = external_id
        if parent is not None:
            body["parent"] = parent
        if state is not None:
            body["state"] = state
        if estimate_point is not None:
            body["estimate_point"] = estimate_point
        if type is not None:
            body["type"] = type

        return fork_request(
            "PATCH",
            f"workspaces/{workspace_slug}/projects/{project_id}/work-items/{work_item_id}",
            json=body,
        )

    @mcp.tool()
    def delete_work_item(project_id: str, work_item_id: str) -> None:
        """
        Delete a work item by ID.

        Args:
            workspace_slug: The workspace slug identifier
            project_id: UUID of the project
            work_item_id: UUID of the work item
        """
        _, workspace_slug = get_plane_client_context()
        fork_request(
            "DELETE",
            f"workspaces/{workspace_slug}/projects/{project_id}/work-items/{work_item_id}",
        )

    @mcp.tool()
    def search_work_items(
        query: str,
        expand: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
    ) -> dict:
        """
        Search work items across a workspace.

        Args:
            workspace_slug: The workspace slug identifier
            query: This is a free-form text search and will be used to search the work items
                    by name, description etc.
            expand: Comma-separated list of related fields to expand in response
            fields: Comma-separated list of fields to include in response
            order_by: Field to order results by. Prefix with '-' for descending order

        Returns:
            Search results dict
        """
        _, workspace_slug = get_plane_client_context()

        params: dict = {"q": query}
        if expand:
            params["expand"] = expand
        if fields:
            params["fields"] = fields
        if order_by:
            params["order_by"] = order_by

        return fork_request(
            "GET",
            f"workspaces/{workspace_slug}/work-items/search",
            params=params,
        )
