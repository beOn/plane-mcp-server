"""CRUD tests for labels, states, cycles, modules, templates, issue types."""

import pytest
from datetime import datetime, timedelta

pytestmark = pytest.mark.integration


class TestLabels:
    def test_label_lifecycle(self, api, ws, project_id, cleanup):
        label = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/labels",
            json={"name": "Test Label", "color": "#ff0000"},
        )
        assert label["name"] == "Test Label"

        updated = api(
            "PATCH",
            f"workspaces/{ws}/projects/{project_id}/labels/{label['id']}",
            json={"name": "Updated Label"},
        )
        assert updated["name"] == "Updated Label"

        cleanup(f"workspaces/{ws}/projects/{project_id}/labels/{label['id']}")

    def test_list_labels(self, api, ws, project_id):
        resp = api("GET", f"workspaces/{ws}/projects/{project_id}/labels")
        assert isinstance(resp, (list, dict))


class TestStates:
    def test_list_states(self, api, ws, project_id):
        resp = api("GET", f"workspaces/{ws}/projects/{project_id}/states")
        states = resp if isinstance(resp, list) else resp.get("results", [])
        assert len(states) > 0, "New project should have default states"

    def test_create_state(self, api, ws, project_id, cleanup):
        state = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/states",
            json={"name": "Test State", "color": "#00ff00", "group": "started"},
        )
        assert state["name"] == "Test State"
        cleanup(f"workspaces/{ws}/projects/{project_id}/states/{state['id']}")


class TestCycles:
    @pytest.mark.xfail(reason="v1 serializer requires project_id in body (OPS-34 fixed at MCP layer)")
    def test_cycle_create_without_project_in_body(self, api, ws, project_id, cleanup):
        """v1 API requires project_id in cycle create body.

        This raw API call fails (400) because the v1 serializer requires
        project_id in the JSON body. The MCP server's create_resource tool
        auto-injects it (OPS-34 fix), but this test exercises the raw API.
        """
        now = datetime.utcnow()
        cycle = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/cycles",
            json={
                "name": "Cycle without project body",
                "start_date": now.strftime("%Y-%m-%d"),
                "end_date": (now + timedelta(days=14)).strftime("%Y-%m-%d"),
            },
        )
        assert cycle["name"] == "Cycle without project body"
        cleanup(f"workspaces/{ws}/projects/{project_id}/cycles/{cycle['id']}")

    def test_cycle_lifecycle(self, api, ws, project_id, cleanup):
        """Full cycle lifecycle — v1 requires 'project_id' in the JSON body."""
        now = datetime.utcnow()
        cycle = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/cycles",
            json={
                "name": "Test Cycle",
                "project_id": project_id,
                "start_date": now.strftime("%Y-%m-%d"),
                "end_date": (now + timedelta(days=14)).strftime("%Y-%m-%d"),
            },
        )
        assert cycle["name"] == "Test Cycle"

        updated = api(
            "PATCH",
            f"workspaces/{ws}/projects/{project_id}/cycles/{cycle['id']}",
            json={"name": "Updated Cycle"},
        )
        assert updated["name"] == "Updated Cycle"

        cleanup(f"workspaces/{ws}/projects/{project_id}/cycles/{cycle['id']}")

    def test_add_work_item_to_cycle(self, api, ws, project_id, cleanup):
        now = datetime.utcnow()
        cycle = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/cycles",
            json={
                "name": "Cycle with items",
                "project_id": project_id,
                "start_date": now.strftime("%Y-%m-%d"),
                "end_date": (now + timedelta(days=14)).strftime("%Y-%m-%d"),
            },
        )
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Cycle item"},
        )

        api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/cycles/{cycle['id']}/cycle-issues",
            json={"issues": [item["id"]]},
        )

        resp = api(
            "GET",
            f"workspaces/{ws}/projects/{project_id}/cycles/{cycle['id']}/cycle-issues",
        )
        items = resp if isinstance(resp, list) else resp.get("results", [])
        assert len(items) > 0

        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")
        cleanup(f"workspaces/{ws}/projects/{project_id}/cycles/{cycle['id']}")


class TestModules:
    def test_module_create_minimal(self, api, ws, project_id, cleanup):
        """Module create with just a name (features enabled by fixture)."""
        module = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/modules",
            json={"name": "Module minimal"},
        )
        assert module["name"] == "Module minimal"
        cleanup(f"workspaces/{ws}/projects/{project_id}/modules/{module['id']}")

    def test_module_lifecycle(self, api, ws, project_id, cleanup):
        """Full module lifecycle — create, update, delete."""
        module = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/modules",
            json={"name": "Test Module", "project_id": project_id},
        )
        assert module["name"] == "Test Module"

        updated = api(
            "PATCH",
            f"workspaces/{ws}/projects/{project_id}/modules/{module['id']}",
            json={"name": "Updated Module"},
        )
        assert updated["name"] == "Updated Module"

        cleanup(f"workspaces/{ws}/projects/{project_id}/modules/{module['id']}")


class TestIssueTypes:
    def test_list_issue_types(self, api, ws):
        types = api("GET", f"workspaces/{ws}/issue-types")
        assert isinstance(types, list)

    def test_issue_type_lifecycle(self, api, ws, cleanup):
        itype = api(
            "POST",
            f"workspaces/{ws}/issue-types",
            json={"name": "Test Type (pytest)"},
        )
        assert itype["name"] == "Test Type (pytest)"

        updated = api(
            "PATCH",
            f"workspaces/{ws}/issue-types/{itype['id']}",
            json={"name": "Test Type Updated"},
        )
        assert updated["name"] == "Test Type Updated"

        cleanup(f"workspaces/{ws}/issue-types/{itype['id']}")


class TestTemplates:
    def test_list_templates(self, api, ws):
        templates = api("GET", f"workspaces/{ws}/issue-templates")
        assert isinstance(templates, list)
