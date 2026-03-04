"""Fork-compatible client for workspace-scoped issue type endpoints."""

from plane.api.base_resource import BaseResource
from plane.config import Configuration
from plane.models.work_item_types import (
    CreateWorkItemType,
    UpdateWorkItemType,
    WorkItemType,
)


class ForkWorkItemTypes(BaseResource):
    """Workspace-scoped issue type operations via /api/v1/workspaces/{slug}/issue-types/."""

    def __init__(self, config: Configuration) -> None:
        super().__init__(config, "/workspaces/")

    def list(self, workspace_slug: str) -> list[WorkItemType]:
        response = self._get(f"{workspace_slug}/issue-types")
        return [WorkItemType.model_validate(item) for item in response]

    def create(self, workspace_slug: str, data: CreateWorkItemType) -> WorkItemType:
        response = self._post(
            f"{workspace_slug}/issue-types",
            data.model_dump(exclude_none=True),
        )
        return WorkItemType.model_validate(response)

    def retrieve(self, workspace_slug: str, type_id: str) -> WorkItemType:
        response = self._get(f"{workspace_slug}/issue-types/{type_id}")
        return WorkItemType.model_validate(response)

    def update(
        self, workspace_slug: str, type_id: str, data: UpdateWorkItemType
    ) -> WorkItemType:
        response = self._patch(
            f"{workspace_slug}/issue-types/{type_id}",
            data.model_dump(exclude_none=True),
        )
        return WorkItemType.model_validate(response)

    def delete(self, workspace_slug: str, type_id: str) -> None:
        self._delete(f"{workspace_slug}/issue-types/{type_id}")
