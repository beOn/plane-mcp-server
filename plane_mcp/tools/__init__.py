"""Tools for Plane MCP Server."""

from fastmcp import FastMCP

from plane_mcp.tools.crud import register_crud_tools
from plane_mcp.tools.specialized import register_specialized_tools


def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the MCP server."""
    register_crud_tools(mcp)
    register_specialized_tools(mcp)
