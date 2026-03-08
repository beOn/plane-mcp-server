"""Resource registry for generic CRUD dispatch.

Maps resource type names to URL patterns and scope requirements.
All resources are accessed via fork_request() through /api/v1/.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ResourceDef:
    """Definition of a Plane API resource for generic CRUD dispatch."""

    path: str  # URL template, e.g. "workspaces/{ws}/projects/{project_id}/labels"
    scope: list[str] = field(default_factory=list)  # Required scope params
    list_key: str = "results"  # Key in paginated response ("" for raw list)
    read_only: bool = False  # If True, create/update/delete raise errors


RESOURCES: dict[str, ResourceDef] = {
    # --- Workspace-scoped ---
    "project": ResourceDef(
        "workspaces/{ws}/projects", list_key="results"
    ),
    "initiative": ResourceDef(
        "workspaces/{ws}/initiatives", list_key="results"
    ),
    "work_item_type": ResourceDef(
        "workspaces/{ws}/issue-types", list_key=""
    ),
    "template": ResourceDef(
        "workspaces/{ws}/issue-templates", list_key=""
    ),
    "email_reference": ResourceDef(
        "workspaces/{ws}/email-references", list_key="", read_only=True
    ),
    "workspace_page": ResourceDef(
        "workspaces/{ws}/pages", list_key=""
    ),
    # --- Project-scoped ---
    "label": ResourceDef(
        "workspaces/{ws}/projects/{project_id}/labels",
        scope=["project_id"], list_key="results",
    ),
    "state": ResourceDef(
        "workspaces/{ws}/projects/{project_id}/states",
        scope=["project_id"], list_key="results",
    ),
    "cycle": ResourceDef(
        "workspaces/{ws}/projects/{project_id}/cycles",
        scope=["project_id"], list_key="results",
    ),
    "module": ResourceDef(
        "workspaces/{ws}/projects/{project_id}/modules",
        scope=["project_id"], list_key="results",
    ),
    "work_item": ResourceDef(
        "workspaces/{ws}/projects/{project_id}/work-items",
        scope=["project_id"], list_key="results",
    ),
    "intake_item": ResourceDef(
        "workspaces/{ws}/projects/{project_id}/intake",
        scope=["project_id"], list_key="results",
    ),
    "page": ResourceDef(
        "workspaces/{ws}/projects/{project_id}/pages",
        scope=["project_id"], list_key="",
    ),
    "work_item_property": ResourceDef(
        "workspaces/{ws}/projects/{project_id}/work-item-properties/{type_id}",
        scope=["project_id", "type_id"], list_key="",
    ),
    # --- Work-item-scoped ---
    "comment": ResourceDef(
        "workspaces/{ws}/projects/{project_id}/work-items/{work_item_id}/comments",
        scope=["project_id", "work_item_id"], list_key="results",
    ),
    "link": ResourceDef(
        "workspaces/{ws}/projects/{project_id}/work-items/{work_item_id}/links",
        scope=["project_id", "work_item_id"], list_key="results",
    ),
    "relation": ResourceDef(
        "workspaces/{ws}/projects/{project_id}/issues/{work_item_id}/issue-relations",
        scope=["project_id", "work_item_id"], list_key="",
    ),
    "activity": ResourceDef(
        "workspaces/{ws}/projects/{project_id}/work-items/{work_item_id}/activities",
        scope=["project_id", "work_item_id"], list_key="results",
        read_only=True,
    ),
    "work_log": ResourceDef(
        "workspaces/{ws}/projects/{project_id}/work-items/{work_item_id}/work-logs",
        scope=["project_id", "work_item_id"], list_key="",
    ),
    # --- Read-only sub-resources (fork endpoints, use "issues" not "work-items") ---
    "linked_email": ResourceDef(
        "workspaces/{ws}/projects/{project_id}/issues/{work_item_id}/linked-emails",
        scope=["project_id", "work_item_id"], list_key="", read_only=True,
    ),
    "linked_page": ResourceDef(
        "workspaces/{ws}/projects/{project_id}/issues/{work_item_id}/linked-pages",
        scope=["project_id", "work_item_id"], list_key="", read_only=True,
    ),
}


def resolve_path(
    resource_type: str,
    ws: str,
    *,
    project_id: str | None = None,
    work_item_id: str | None = None,
    type_id: str | None = None,
    resource_id: str | None = None,
) -> str:
    """Build the URL path for a resource.

    Special case: resource_type="page" with no project_id uses workspace_page path.
    """
    # Page auto-routing: no project_id → workspace page
    effective_type = resource_type
    if resource_type == "page" and not project_id:
        effective_type = "workspace_page"

    if effective_type not in RESOURCES:
        raise ValueError(
            f"Unknown resource_type '{effective_type}'. "
            f"Valid types: {', '.join(sorted(RESOURCES))}"
        )

    rdef = RESOURCES[effective_type]
    path = rdef.path.format(
        ws=ws,
        project_id=project_id or "",
        work_item_id=work_item_id or "",
        type_id=type_id or "",
    )
    if resource_id:
        path = f"{path}/{resource_id}"
    return path


def get_resource_def(resource_type: str, project_id: str | None = None) -> ResourceDef:
    """Get the ResourceDef, handling page auto-routing."""
    effective_type = resource_type
    if resource_type == "page" and not project_id:
        effective_type = "workspace_page"
    if effective_type not in RESOURCES:
        raise ValueError(
            f"Unknown resource_type '{effective_type}'. "
            f"Valid types: {', '.join(sorted(RESOURCES))}"
        )
    return RESOURCES[effective_type]


def build_params(
    cursor: str | None = None,
    per_page: int | None = None,
    order_by: str | None = None,
    expand: str | None = None,
    fields: str | None = None,
    **extra: str,
) -> dict:
    """Build query params dict, omitting None values."""
    params: dict = {}
    if cursor:
        params["cursor"] = cursor
    if per_page:
        params["per_page"] = per_page
    if order_by:
        params["order_by"] = order_by
    if expand:
        params["expand"] = expand
    if fields:
        params["fields"] = fields
    for k, v in extra.items():
        if v is not None:
            params[k] = v
    return params


def extract_results(response: dict | list | None, list_key: str) -> list | dict:
    """Unwrap paginated responses. Returns results list or raw response."""
    if response is None:
        return []
    if list_key and isinstance(response, dict) and list_key in response:
        return response[list_key]
    if isinstance(response, list):
        return response
    return response
