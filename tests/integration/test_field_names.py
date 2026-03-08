"""Documents actual v1 API field name behavior.

Each test validates what field names the /api/v1/ endpoints accept and return.
When these tests fail, it means the API behavior has changed and skills/docs
need updating.

Known divergence: /api/v1/ uses different field names than /api/ (internal).
  - v1: state, assignees, labels, parent
  - internal: state_id, assignee_ids, label_ids, parent_id
"""

import pytest

pytestmark = pytest.mark.integration


class TestCreateFieldNames:
    """What field names does POST /work-items accept?"""

    def test_create_minimal(self, api, ws, project_id, cleanup):
        """Minimum required fields: just 'name'."""
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Minimal work item"},
        )
        assert item["id"]
        assert item["name"] == "Minimal work item"
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")

    def test_create_with_v1_state_field(self, api, ws, project_id, default_state_id, cleanup):
        """v1 API accepts 'state' (not 'state_id') for setting state on create."""
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "State field test", "state": default_state_id},
        )
        assert item["state"] == default_state_id
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")

    def test_create_with_state_id_field(self, api, ws, project_id, default_state_id, cleanup):
        """v1 API: 'state_id' in create body — documents whether it's respected or ignored.

        The item should still get a state (either the requested one or the project default).
        """
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "state_id field test", "state_id": default_state_id},
        )
        assert "state" in item
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")

    def test_create_with_type_id_works(self, api, ws, project_id, work_item_type_id, cleanup):
        """type_id in create body now works (was a known bug, now fixed).

        Previously returned 400. As of 2026-03-07, create with type_id succeeds.
        """
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "type_id create test", "type_id": work_item_type_id},
        )
        assert item.get("type_id") == work_item_type_id
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")

    def test_update_with_type_id_works(self, api, ws, project_id, work_item_type_id, cleanup):
        """type_id works in PATCH (update)."""
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "type_id update test"},
        )
        updated = api(
            "PATCH",
            f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}",
            json={"type_id": work_item_type_id},
        )
        assert updated.get("type_id") == work_item_type_id
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")

    def test_create_with_full_fields(
        self, api, ws, project_id, work_item_type_id, default_state_id, cleanup
    ):
        """Create with name + state + type_id all at once."""
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={
                "name": "Full fields test",
                "state": default_state_id,
                "type_id": work_item_type_id,
            },
        )
        assert item.get("type_id") == work_item_type_id
        assert item["state"] == default_state_id
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")


class TestResponseFieldNames:
    """What field names appear in v1 responses?"""

    def test_v1_response_uses_state_not_state_id(self, api, ws, project_id, cleanup):
        """v1 responses use 'state' (UUID string), not 'state_id'."""
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Response field test"},
        )
        assert "state" in item, "v1 response should have 'state' field"
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")

    def test_v1_response_uses_assignees_not_assignee_ids(self, api, ws, project_id, cleanup):
        """v1 responses use 'assignees' (list), not 'assignee_ids'."""
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Assignees field test"},
        )
        assert "assignees" in item, "v1 response should have 'assignees' field"
        assert isinstance(item["assignees"], list)
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")

    def test_v1_response_uses_labels_not_label_ids(self, api, ws, project_id, cleanup):
        """v1 responses use 'labels' (list), not 'label_ids'."""
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Labels field test"},
        )
        assert "labels" in item, "v1 response should have 'labels' field"
        assert isinstance(item["labels"], list)
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")


class TestUpdateFieldNames:
    """What field names does PATCH /work-items accept?"""

    def test_update_with_v1_state_field(self, api, ws, project_id, project_states, cleanup):
        """PATCH accepts 'state' (UUID) to change state."""
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Update state test"},
        )
        target = project_states[-1]["id"] if len(project_states) > 1 else project_states[0]["id"]
        updated = api(
            "PATCH",
            f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}",
            json={"state": target},
        )
        assert updated["state"] == target
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")

    def test_description_html_field(self, api, ws, project_id, cleanup):
        """v1 uses 'description_html' for HTML content."""
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Description test", "description_html": "<p>Test content</p>"},
        )
        assert "description_html" in item
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")

    def test_parent_field_name(self, api, ws, project_id, cleanup):
        """v1 uses 'parent' (UUID), not 'parent_id'."""
        parent = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Parent item"},
        )
        child = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Child item"},
        )
        updated = api(
            "PATCH",
            f"workspaces/{ws}/projects/{project_id}/work-items/{child['id']}",
            json={"parent": parent["id"]},
        )
        assert updated.get("parent") == parent["id"]
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{child['id']}")
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{parent['id']}")

    def test_priority_field_values(self, api, ws, project_id, cleanup):
        """Priority: v1 accepts string values like 'urgent', 'high', 'medium', 'low', 'none'."""
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Priority test"},
        )
        updated = api(
            "PATCH",
            f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}",
            json={"priority": "high"},
        )
        assert "priority" in updated
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")
