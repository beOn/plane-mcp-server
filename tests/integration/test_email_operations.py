"""Email operations — search, link/unlink, triage, 409 handling."""

import pytest
import requests

pytestmark = pytest.mark.integration


class TestEmailSearch:
    def test_list_all_emails(self, api, ws):
        """List email references without filters."""
        result = api("GET", f"workspaces/{ws}/email-references")
        assert isinstance(result, list)

    def test_search_by_keyword(self, api, ws):
        """Search uses phrase matching — single keywords work best."""
        result = api(
            "GET",
            f"workspaces/{ws}/email-references",
            params={"search": "intervan"},
        )
        assert isinstance(result, list)

    def test_filter_untriaged(self, api, ws):
        """untriaged=true returns only emails where triaged_at is null."""
        result = api(
            "GET",
            f"workspaces/{ws}/email-references",
            params={"untriaged": "true"},
        )
        assert isinstance(result, list)
        for email in result:
            assert email.get("triaged_at") is None

    def test_email_reference_shape(self, api, ws):
        """Verify email reference response has expected fields."""
        refs = api("GET", f"workspaces/{ws}/email-references")
        if not refs:
            pytest.skip("No email references in workspace")
        ref = refs[0]
        for field in ("id", "message_id", "subject", "from_address", "date"):
            assert field in ref, f"Missing field '{field}' in email reference"


class TestEmailLinkUnlink:
    def test_link_email_to_work_item(self, api, ws, project_id, cleanup):
        """Link an email to a work item via POST. Unlink uses the link record ID."""
        refs = api("GET", f"workspaces/{ws}/email-references")
        if not refs:
            pytest.skip("No email references to link")

        ref_id = refs[0]["id"]  # Full UUID
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Email link test"},
        )
        wi_id = item["id"]
        url = f"workspaces/{ws}/projects/{project_id}/issues/{wi_id}/linked-emails"

        # Link
        link_record = api("POST", url, json={"email_reference_id": ref_id})
        assert link_record["email_reference_id"] == ref_id
        link_id = link_record["id"]

        # Verify link exists
        linked = api("GET", url)
        assert isinstance(linked, list)
        assert len(linked) > 0

        # Unlink by link record ID
        cleanup(f"{url}/{link_id}")
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{wi_id}")

    def test_link_duplicate_returns_409(self, api, ws, project_id, cleanup):
        """Linking the same email twice returns 409 Conflict."""
        refs = api("GET", f"workspaces/{ws}/email-references")
        if not refs:
            pytest.skip("No email references to link")

        ref_id = refs[0]["id"]
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Duplicate link test"},
        )
        wi_id = item["id"]
        url = f"workspaces/{ws}/projects/{project_id}/issues/{wi_id}/linked-emails"

        # First link — success
        link_record = api("POST", url, json={"email_reference_id": ref_id})

        # Second link — should 409
        with pytest.raises(requests.HTTPError) as exc_info:
            api("POST", url, json={"email_reference_id": ref_id})
        assert exc_info.value.response.status_code == 409

        # Cleanup by link record ID
        cleanup(f"{url}/{link_record['id']}")
        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{wi_id}")

    def test_link_with_short_uuid_fails(self, api, ws, project_id, cleanup):
        """Short UUIDs in POST body (email_reference_id) fail.

        Short ID resolution only works in URL path params, not body fields.
        """
        refs = api("GET", f"workspaces/{ws}/email-references")
        if not refs:
            pytest.skip("No email references")

        short_id = refs[0]["id"][:8]
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Short UUID email test"},
        )
        wi_id = item["id"]
        url = f"workspaces/{ws}/projects/{project_id}/issues/{wi_id}/linked-emails"

        with pytest.raises(requests.HTTPError):
            api("POST", url, json={"email_reference_id": short_id})

        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{wi_id}")


class TestEmailUnlinkMethod:
    def test_unlink_via_delete_with_body(self, api, ws, project_id, cleanup):
        """GAP: The MCP unlink_email_from_issue tool uses DELETE with JSON body.

        This is how specialized.py implements it:
            fork_request("DELETE", url, json={"email_reference_id": ref_id})

        If this test fails (500), the MCP tool's unlink approach is broken
        and needs to switch to DELETE by link record ID instead.
        """
        refs = api("GET", f"workspaces/{ws}/email-references")
        if not refs:
            pytest.skip("No email references to link")

        ref_id = refs[0]["id"]
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Unlink method test"},
        )
        wi_id = item["id"]
        url = f"workspaces/{ws}/projects/{project_id}/issues/{wi_id}/linked-emails"

        # Link first
        link_record = api("POST", url, json={"email_reference_id": ref_id})

        # Unlink via DELETE + body (MCP tool's approach)
        api("DELETE", url, json={"email_reference_id": ref_id})

        # Verify unlinked
        linked = api("GET", url)
        assert len(linked) == 0

        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{wi_id}")


class TestEmailTriage:
    def test_triage_already_triaged_is_idempotent(self, api, ws):
        """Triaging an already-triaged email succeeds (no error)."""
        refs = api("GET", f"workspaces/{ws}/email-references")
        triaged = [r for r in refs if r.get("triaged_at") is not None]
        if not triaged:
            pytest.skip("No triaged emails to test idempotency")

        ref_id = triaged[0]["id"]
        # Should not raise
        api("PATCH", f"workspaces/{ws}/email-references/{ref_id}", json={})

    def test_email_detail_shape(self, api, ws):
        """Email reference detail includes body and address fields."""
        refs = api("GET", f"workspaces/{ws}/email-references")
        if not refs:
            pytest.skip("No email references")

        detail = api("GET", f"workspaces/{ws}/email-references/{refs[0]['id']}")
        assert detail["id"] == refs[0]["id"]
        for field in ("body_plain", "to_addresses"):
            assert field in detail, f"Missing field '{field}' in email detail"
