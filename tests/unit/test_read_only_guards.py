"""Unit tests for read-only resource guards.

The CRUD tools (create_resource, update_resource, delete_resource) all check
get_resource_def(type).read_only before making any API call. These tests
verify that the flags are correctly set on the expected types.
"""

import pytest

from plane_mcp.tools.registry import RESOURCES, get_resource_def

pytestmark = pytest.mark.unit

READ_ONLY_TYPES = ["email_reference", "activity", "linked_email", "linked_page"]


@pytest.mark.parametrize("resource_type", READ_ONLY_TYPES)
def test_read_only_flag_set(resource_type):
    """Read-only types have read_only=True in the registry."""
    assert RESOURCES[resource_type].read_only is True


@pytest.mark.parametrize("resource_type", READ_ONLY_TYPES)
def test_get_resource_def_returns_read_only(resource_type):
    """get_resource_def correctly resolves read-only types."""
    # Need project_id for work-item-scoped types
    rdef = get_resource_def(resource_type, project_id="fake")
    assert rdef.read_only is True


def test_no_false_positives():
    """Non-read-only types are NOT marked read-only."""
    writable = [k for k, v in RESOURCES.items() if not v.read_only]
    assert len(writable) > 0
    for resource_type in writable:
        assert RESOURCES[resource_type].read_only is False


def test_exactly_four_read_only_types():
    """Exactly 4 types are read-only. Update this test if the set changes."""
    actual = sorted(k for k, v in RESOURCES.items() if v.read_only)
    assert actual == sorted(READ_ONLY_TYPES)
