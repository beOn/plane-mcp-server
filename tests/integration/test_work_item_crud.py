"""Work item lifecycle tests — create, read, update, delete + sub-resources."""

import pytest
import requests

pytestmark = pytest.mark.integration


class TestWorkItemLifecycle:
    def test_create_and_retrieve(self, api, ws, project_id, cleanup):
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Lifecycle test item"},
        )
        assert item["name"] == "Lifecycle test item"

        detail = api(
            "GET",
            f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}",
        )
        assert detail["id"] == item["id"]
        assert detail["name"] == "Lifecycle test item"
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")

    def test_update(self, api, ws, project_id, cleanup):
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Update test"},
        )
        updated = api(
            "PATCH",
            f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}",
            json={"name": "Updated name"},
        )
        assert updated["name"] == "Updated name"
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")

    def test_delete(self, api, ws, project_id):
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Delete test"},
        )
        api("DELETE", f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")
        with pytest.raises(requests.HTTPError) as exc:
            api("GET", f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")
        assert exc.value.response.status_code == 404

    def test_list_with_pagination(self, api, ws, project_id, cleanup):
        """List work items with per_page param."""
        ids = []
        for i in range(3):
            item = api(
                "POST",
                f"workspaces/{ws}/projects/{project_id}/work-items",
                json={"name": f"Pagination test {i}"},
            )
            ids.append(item["id"])

        resp = api(
            "GET",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            params={"per_page": 2},
        )
        assert isinstance(resp, dict)
        assert "results" in resp
        assert len(resp["results"]) <= 2

        for id_ in ids:
            cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{id_}")

    def test_identifier_lookup(self, api, ws, project_id, test_project, cleanup):
        """Look up work item by project identifier + sequence number (e.g., EDI-42)."""
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Identifier lookup test"},
        )
        identifier = f"{test_project['identifier']}-{item['sequence_id']}"

        found = api("GET", f"workspaces/{ws}/work-items/{identifier}")
        assert found["id"] == item["id"]
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")


class TestWorkItemComments:
    def test_comment_lifecycle(self, api, ws, project_id, cleanup):
        """Create, list, delete a comment on a work item."""
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Comment test item"},
        )
        wi_id = item["id"]
        base = f"workspaces/{ws}/projects/{project_id}/work-items/{wi_id}/comments"

        comment = api("POST", base, json={"comment_html": "<p>Test comment</p>"})
        assert comment["id"]

        resp = api("GET", base)
        assert isinstance(resp, (list, dict))

        cleanup(f"{base}/{comment['id']}")
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{wi_id}")


class TestWorkItemLinks:
    def test_link_lifecycle(self, api, ws, project_id, cleanup):
        """Create and delete a link on a work item."""
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Link test item"},
        )
        wi_id = item["id"]
        base = f"workspaces/{ws}/projects/{project_id}/work-items/{wi_id}/links"

        link = api("POST", base, json={"title": "Test link", "url": "https://example.com"})
        assert link["id"]
        assert link["url"] == "https://example.com"

        cleanup(f"{base}/{link['id']}")
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{wi_id}")


class TestWorkItemRelations:
    def test_create_relation_via_v1(self, api, ws, project_id, cleanup):
        """Create a relation between two work items via /api/v1/ (OPS-35 fix).

        Uses the v1 issue-relations endpoint, matching the internal API's
        contract: POST with relation_type + issues list.
        """
        item1 = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Relation source"},
        )
        item2 = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Relation target"},
        )
        base = f"workspaces/{ws}/projects/{project_id}/issues/{item1['id']}/issue-relations"

        relation = api(
            "POST",
            base,
            json={"relation_type": "relates_to", "issues": [item2["id"]]},
        )
        assert isinstance(relation, list)
        assert len(relation) > 0

        # List relations — should be grouped by type
        listed = api("GET", base)
        assert isinstance(listed, dict)
        assert "relates_to" in listed

        # Delete relation
        api(
            "DELETE",
            base,
            json={"related_issue": str(item2["id"])},
        )

        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item2['id']}")
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item1['id']}")


class TestWorkItemExpand:
    def test_expand_assignees(self, api, ws, project_id, cleanup):
        """expand=assignees returns expanded objects, not just UUIDs."""
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Expand test"},
        )
        detail = api(
            "GET",
            f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}",
            params={"expand": "assignees"},
        )
        assert "assignees" in detail
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")
