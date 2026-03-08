"""Unit tests for registry.py — resolve_path, build_params, extract_results."""

import pytest

from plane_mcp.tools.registry import (
    RESOURCES,
    build_params,
    extract_results,
    get_resource_def,
    resolve_path,
)

pytestmark = pytest.mark.unit

WS = "test-workspace"


# --- resolve_path ---


class TestResolvePath:
    def test_workspace_scoped_list(self):
        path = resolve_path("project", WS)
        assert path == f"workspaces/{WS}/projects"

    def test_workspace_scoped_detail(self):
        path = resolve_path("project", WS, resource_id="abc123")
        assert path == f"workspaces/{WS}/projects/abc123"

    def test_project_scoped_list(self):
        path = resolve_path("work_item", WS, project_id="proj1")
        assert path == f"workspaces/{WS}/projects/proj1/work-items"

    def test_project_scoped_detail(self):
        path = resolve_path("label", WS, project_id="proj1", resource_id="lbl1")
        assert path == f"workspaces/{WS}/projects/proj1/labels/lbl1"

    def test_work_item_scoped_list(self):
        path = resolve_path("comment", WS, project_id="proj1", work_item_id="wi1")
        assert path == f"workspaces/{WS}/projects/proj1/work-items/wi1/comments"

    def test_work_item_scoped_detail(self):
        path = resolve_path(
            "link", WS, project_id="proj1", work_item_id="wi1", resource_id="lnk1"
        )
        assert path == f"workspaces/{WS}/projects/proj1/work-items/wi1/links/lnk1"

    def test_type_id_scoped(self):
        path = resolve_path("work_item_property", WS, project_id="proj1", type_id="type1")
        assert path == f"workspaces/{WS}/projects/proj1/work-item-properties/type1"

    def test_page_with_project_id_uses_project_path(self):
        path = resolve_path("page", WS, project_id="proj1")
        assert path == f"workspaces/{WS}/projects/proj1/pages"

    def test_page_without_project_id_uses_workspace_path(self):
        """Page auto-routing: no project_id -> workspace page."""
        path = resolve_path("page", WS)
        assert path == f"workspaces/{WS}/pages"

    def test_page_auto_routing_with_resource_id(self):
        path = resolve_path("page", WS, resource_id="pg1")
        assert path == f"workspaces/{WS}/pages/pg1"

    def test_workspace_page_explicit(self):
        path = resolve_path("workspace_page", WS)
        assert path == f"workspaces/{WS}/pages"

    def test_linked_email_uses_issues_not_work_items(self):
        """linked_email uses /issues/ not /work-items/ in the URL."""
        path = resolve_path("linked_email", WS, project_id="proj1", work_item_id="wi1")
        assert "/issues/wi1/linked-emails" in path
        assert "/work-items/" not in path

    def test_linked_page_uses_issues_not_work_items(self):
        path = resolve_path("linked_page", WS, project_id="proj1", work_item_id="wi1")
        assert "/issues/wi1/linked-pages" in path
        assert "/work-items/" not in path

    def test_unknown_resource_type_raises(self):
        with pytest.raises(ValueError, match="Unknown resource_type"):
            resolve_path("nonexistent", WS)

    def test_missing_scope_produces_empty_segment(self):
        """Calling project-scoped resource without project_id -> empty segment."""
        path = resolve_path("work_item", WS)
        assert "/projects//" in path


# --- get_resource_def ---


class TestGetResourceDef:
    def test_page_auto_routing_workspace(self):
        rdef = get_resource_def("page", project_id=None)
        assert rdef.path == "workspaces/{ws}/pages"

    def test_page_auto_routing_project(self):
        rdef = get_resource_def("page", project_id="proj1")
        assert rdef.path == "workspaces/{ws}/projects/{project_id}/pages"

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown resource_type"):
            get_resource_def("nonexistent")


# --- build_params ---


class TestBuildParams:
    def test_empty(self):
        assert build_params() == {}

    def test_all_params(self):
        result = build_params(
            cursor="abc",
            per_page=50,
            order_by="-created_at",
            expand="assignees",
            fields="id,name",
        )
        assert result == {
            "cursor": "abc",
            "per_page": 50,
            "order_by": "-created_at",
            "expand": "assignees",
            "fields": "id,name",
        }

    def test_none_values_omitted(self):
        result = build_params(cursor=None, per_page=10)
        assert result == {"per_page": 10}

    def test_extra_kwargs(self):
        result = build_params(search="hello", status="active")
        assert result == {"search": "hello", "status": "active"}

    def test_extra_kwargs_none_omitted(self):
        result = build_params(search=None, status="active")
        assert result == {"status": "active"}


# --- extract_results ---


class TestExtractResults:
    def test_paginated_response(self):
        response = {"results": [{"id": "1"}, {"id": "2"}], "next_cursor": "abc"}
        assert extract_results(response, "results") == [{"id": "1"}, {"id": "2"}]

    def test_raw_list(self):
        response = [{"id": "1"}]
        assert extract_results(response, "results") == [{"id": "1"}]

    def test_empty_list_key_with_list(self):
        """When list_key is '', return raw list response."""
        response = [{"id": "1"}]
        assert extract_results(response, "") == [{"id": "1"}]

    def test_none_response(self):
        assert extract_results(None, "results") == []

    def test_dict_without_list_key(self):
        """Dict response without the expected key is returned as-is."""
        response = {"total": 5, "items": []}
        assert extract_results(response, "results") == {"total": 5, "items": []}

    def test_dict_with_empty_list_key(self):
        """Empty list_key returns dict as-is."""
        response = {"id": "1", "name": "test"}
        assert extract_results(response, "") == {"id": "1", "name": "test"}


# --- RESOURCES completeness ---


class TestResourcesRegistry:
    def test_all_expected_types_present(self):
        expected = {
            "project", "initiative", "work_item_type", "template", "email_reference",
            "workspace_page", "label", "state", "cycle", "module", "work_item",
            "intake_item", "page", "work_item_property", "comment", "link",
            "relation", "activity", "work_log", "linked_email", "linked_page",
        }
        assert set(RESOURCES.keys()) == expected

    def test_resource_count(self):
        assert len(RESOURCES) == 21
