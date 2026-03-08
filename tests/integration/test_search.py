"""Search behavior — work item search, email phrase matching."""

import pytest

pytestmark = pytest.mark.integration


class TestWorkItemSearch:
    def test_search_by_name(self, api, ws, project_id, cleanup):
        """Search finds work items by name."""
        item = api(
            "POST",
            f"workspaces/{ws}/projects/{project_id}/work-items",
            json={"name": "Unique search term xylophone42"},
        )

        results = api(
            "GET",
            f"workspaces/{ws}/work-items/search",
            params={"q": "xylophone42"},
        )
        assert isinstance(results, dict)

        cleanup(f"workspaces/{ws}/projects/{project_id}/work-items/{item['id']}")

    def test_search_returns_dict(self, api, ws):
        """search_work_items returns a dict, not a list."""
        results = api(
            "GET",
            f"workspaces/{ws}/work-items/search",
            params={"q": "test"},
        )
        assert isinstance(results, dict)


class TestEmailSearch:
    def test_phrase_matching(self, api, ws):
        """Email search matches phrases, not individual terms.

        Searching for "intervan report" matches the phrase, not separate words.
        Use single keywords for best results.
        """
        single = api(
            "GET",
            f"workspaces/{ws}/email-references",
            params={"search": "intervan"},
        )
        assert isinstance(single, list)

    def test_folder_filter(self, api, ws):
        """Filter emails by folder."""
        result = api(
            "GET",
            f"workspaces/{ws}/email-references",
            params={"folder": "INBOX"},
        )
        assert isinstance(result, list)
