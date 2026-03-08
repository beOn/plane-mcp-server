"""Batch update operations — bulk work items + sequential fallback."""

import pytest

pytestmark = pytest.mark.integration


class TestBatchWorkItems:
    def test_bulk_update_same_project(self, api, ws, project_id, cleanup):
        """Work items in same project batched into one backend call."""
        items = []
        for i in range(3):
            item = api(
                "POST",
                f"workspaces/{ws}/projects/{project_id}/work-items",
                json={"name": f"Batch item {i}"},
            )
            items.append(item)

        bulk_payload = [
            {"id": items[i]["id"], "name": f"Batch {i} updated"} for i in range(3)
        ]
        result = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/bulk-update-issues",
            json={"updates": bulk_payload},
        )
        assert "updated" in result or "errors" in result

        for i, item in enumerate(items):
            detail = api(
                "GET",
                f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}",
            )
            assert detail["name"] == f"Batch {i} updated"

        for item in items:
            cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")

    def test_bulk_update_state(self, api, ws, project_id, project_states, cleanup):
        """Bulk update can change state for multiple items at once."""
        target_state = (
            project_states[-1]["id"] if len(project_states) > 1 else project_states[0]["id"]
        )
        items = []
        for i in range(2):
            item = api(
                "POST",
                f"workspaces/{ws}/projects/{project_id}/work-items",
                json={"name": f"Batch state item {i}"},
            )
            items.append(item)

        bulk_payload = [{"id": item["id"], "state": target_state} for item in items]
        api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/bulk-update-issues",
            json={"updates": bulk_payload},
        )

        for item in items:
            detail = api(
                "GET",
                f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}",
            )
            assert detail["state"] == target_state
            cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")


class TestSequentialFallback:
    def test_update_labels_sequentially(self, api, ws, project_id, cleanup):
        """Non-work-item types fall back to sequential PATCH calls."""
        labels = []
        for i in range(2):
            label = api(
                "POST",
                f"workspaces/{ws}/projects/{project_id}/labels",
                json={"name": f"Batch label {i}", "color": "#0000ff"},
            )
            labels.append(label)

        for i, label in enumerate(labels):
            updated = api(
                "PATCH",
                f"workspaces/{ws}/projects/{project_id}/labels/{label['id']}",
                json={"name": f"Batch label {i} updated"},
            )
            assert updated["name"] == f"Batch label {i} updated"

        for label in labels:
            cleanup(f"workspaces/{ws}/projects/{project_id}/labels/{label['id']}")
