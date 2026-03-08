"""Page tests — workspace vs project, auto-routing, children, description_html."""

import pytest

pytestmark = pytest.mark.integration


class TestWorkspacePages:
    def test_create_workspace_page(self, api, ws, cleanup):
        """Create a workspace page (no project_id)."""
        page = api(
            "POST",
            f"workspaces/{ws}/pages",
            json={"name": "Test Workspace Page", "access": 0},
        )
        assert page["name"] == "Test Workspace Page"
        assert page["id"]
        # Archive for cleanup (can't delete workspace pages via v1 API)
        cleanup(f"workspaces/{ws}/pages/{page['id']}/archive")

    def test_list_workspace_pages(self, api, ws):
        result = api("GET", f"workspaces/{ws}/pages")
        assert isinstance(result, list)

    def test_workspace_page_with_description_html(self, api, ws, cleanup):
        page = api(
            "POST",
            f"workspaces/{ws}/pages",
            json={
                "name": "Page with HTML",
                "description_html": "<h1>Heading</h1><p>Content</p>",
                "access": 0,
            },
        )
        detail = api("GET", f"workspaces/{ws}/pages/{page['id']}")
        assert "description_html" in detail
        cleanup(f"workspaces/{ws}/pages/{page['id']}/archive")

    def test_update_workspace_page(self, api, ws, cleanup):
        page = api(
            "POST",
            f"workspaces/{ws}/pages",
            json={"name": "Page to update", "access": 0},
        )
        updated = api(
            "PATCH",
            f"workspaces/{ws}/pages/{page['id']}",
            json={"name": "Updated page name"},
        )
        assert updated["name"] == "Updated page name"
        cleanup(f"workspaces/{ws}/pages/{page['id']}/archive")


class TestProjectPages:
    def test_create_project_page(self, api, ws, project_id):
        page = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/pages",
            json={"name": "Test Project Page", "access": 0},
        )
        assert page["name"] == "Test Project Page"
        # No cleanup needed — project deletion cascades

    def test_list_project_pages(self, api, ws, project_id):
        result = api("GET", f"workspaces/{ws}/projects/{project_id}/pages")
        assert isinstance(result, list)


class TestPageChildren:
    def test_create_child_page(self, api, ws, cleanup):
        """Create a parent page, then a child page, then list children."""
        parent = api(
            "POST",
            f"workspaces/{ws}/pages",
            json={"name": "Parent page", "access": 0},
        )
        child = api(
            "POST",
            f"workspaces/{ws}/pages",
            json={"name": "Child page", "parent": parent["id"], "access": 0},
        )

        children = api("GET", f"workspaces/{ws}/pages/{parent['id']}/children")
        assert isinstance(children, list)
        child_ids = [c["id"] for c in children]
        assert child["id"] in child_ids

        cleanup(f"workspaces/{ws}/pages/{child['id']}/archive")
        cleanup(f"workspaces/{ws}/pages/{parent['id']}/archive")

    def test_child_page_ids_in_parent(self, api, ws, cleanup):
        """Parent page response includes child_page_ids."""
        parent = api(
            "POST",
            f"workspaces/{ws}/pages",
            json={"name": "Parent with children", "access": 0},
        )
        child = api(
            "POST",
            f"workspaces/{ws}/pages",
            json={"name": "Another child", "parent": parent["id"], "access": 0},
        )

        parent_detail = api("GET", f"workspaces/{ws}/pages/{parent['id']}")
        assert "child_page_ids" in parent_detail
        assert child["id"] in parent_detail["child_page_ids"]

        cleanup(f"workspaces/{ws}/pages/{child['id']}/archive")
        cleanup(f"workspaces/{ws}/pages/{parent['id']}/archive")
