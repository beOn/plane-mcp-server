"""Helper for making requests to custom fork /api/v1/ endpoints."""

import requests

from plane_mcp.client import get_plane_client_context


def fork_request(method: str, path: str, **kwargs) -> dict | list | None:
    """Make a request to a custom fork /api/v1/ endpoint.

    Args:
        method: HTTP method (GET, POST, PATCH, DELETE)
        path: Path relative to /api/v1/ (e.g., "workspaces/intervan/email-references")
        **kwargs: Additional kwargs passed to requests.request (json, params, etc.)

    Returns:
        Parsed JSON response, or None for 204 responses.
    """
    ctx = get_plane_client_context()
    # ctx.client.config.base_path is already "{base_url}/api/v1"
    url = f"{ctx.client.config.base_path}/{path.lstrip('/')}".rstrip("/") + "/"
    headers = {"Content-Type": "application/json"}
    if ctx.client.config.api_key:
        headers["X-Api-Key"] = ctx.client.config.api_key
    if ctx.client.config.access_token:
        headers["Authorization"] = f"Bearer {ctx.client.config.access_token}"
    resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)
    resp.raise_for_status()
    return resp.json() if resp.status_code != 204 and resp.content else None
