"""Short UUID resolution — where 8-char hex prefixes work and where they don't.

The fork middleware resolves 8+ char hex prefixes in URL path params via
Cast+startswith. Short IDs do NOT work in POST/PATCH body fields.
"""

import pytest
import requests

pytestmark = pytest.mark.integration


class TestShortUUIDsInURLPath:
    def test_get_project_by_short_id(self, api, ws, project_id):
        """8-char prefix works in URL path for GET."""
        short = project_id[:8]
        result = api("GET", f"workspaces/{ws}/projects/{short}")
        assert result["id"] == project_id

    def test_get_work_item_by_short_id(self, api, ws, project_id, cleanup):
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Short UUID path test"},
        )
        short = item["id"][:8]
        result = api(
            "GET",
            f"workspaces/{ws}/projects/{project_id}/work-items/{short}",
        )
        assert result["id"] == item["id"]
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")

    def test_update_by_short_id(self, api, ws, project_id, cleanup):
        """PATCH with short ID in URL path works."""
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Short UUID PATCH test"},
        )
        short = item["id"][:8]
        updated = api(
            "PATCH",
            f"workspaces/{ws}/projects/{project_id}/work-items/{short}",
            json={"name": "Patched via short ID"},
        )
        assert updated["name"] == "Patched via short ID"
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")

    def test_short_id_minimum_length(self, api, ws, project_id):
        """8-char minimum: shorter may fail."""
        seven = project_id[:7]
        eight = project_id[:8]

        # 8-char should work
        result = api("GET", f"workspaces/{ws}/projects/{eight}")
        assert result["id"] == project_id

        # 7-char may fail
        try:
            api("GET", f"workspaces/{ws}/projects/{seven}")
        except requests.HTTPError:
            pass  # Expected — 7 chars is below minimum


class TestShortUUIDsInBody:
    def test_short_project_id_as_scope_param(self, api, ws, project_id):
        """project_id in URL path (scope param) works with short IDs."""
        short = project_id[:8]
        result = api("GET", f"workspaces/{ws}/projects/{short}/work-items")
        assert isinstance(result, (list, dict))

    def test_email_reference_id_in_body_needs_full_uuid(self, api, ws, project_id, cleanup):
        """email_reference_id in POST body does NOT resolve short IDs.

        Body fields go directly to Django ORM which expects exact UUID match.
        """
        refs = api("GET", f"workspaces/{ws}/email-references")
        if not refs:
            pytest.skip("No email references")

        short_ref_id = refs[0]["id"][:8]
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Body short UUID test"},
        )
        url = f"workspaces/{ws}/projects/{project_id}/issues/{item['id']}/linked-emails"

        with pytest.raises(requests.HTTPError):
            api("POST", url, json={"email_reference_id": short_ref_id})

        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")
