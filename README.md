# Intervan Plane MCP Server

MCP (Model Context Protocol) server for Intervan's self-hosted Plane instance. Gives AI tools (Claude Code, Cursor, etc.) direct access to work items, wiki pages, email references, and issue templates.

Forked from [makeplane/plane-mcp-server](https://github.com/makeplane/plane-mcp-server) with extensions for our custom Plane fork features.

## Quick Start

### Prerequisites

- Python 3.11+ (check with `python3 --version`)
- [uv](https://docs.astral.sh/uv/) package manager (`brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- A Plane API key (get one from God-mode or ask Ben)

### 1. Clone and install

```bash
git clone git@github.com:intervan/plane-mcp-server.git
cd plane-mcp-server
uv sync
```

### 2. Store your API key

On macOS, store it in Keychain so it's not in plain text:

```bash
security add-generic-password -a "plane-api-key" -s "intervan-plane" -w "YOUR_API_KEY_HERE"
```

On Linux, use a `.env` file (keep it out of git):

```bash
echo 'PLANE_API_KEY=your_key_here' > .env
```

### 3. Add to your AI tool

**Claude Code** — add to your project's `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "plane": {
      "command": "sh",
      "args": [
        "-c",
        "PLANE_API_KEY=$(security find-generic-password -a plane-api-key -s intervan-plane -w) PLANE_WORKSPACE_SLUG=intervan PLANE_BASE_URL=https://ividemo.benacland.com uv run --directory /path/to/plane-mcp-server python -m plane_mcp stdio"
      ]
    }
  }
}
```

Replace `/path/to/plane-mcp-server` with the actual path to your clone.

**Cursor** — add to `.cursor/mcp.json` with the same config.

### 4. Verify it works

Start a new Claude Code or Cursor session. You should see `plane` tools available. Try:

```
> List all work items in the EDI Support project
```

The project ID for EDI Support is `8c5e9fe5-2203-4dbc-93d4-5108acc09d3d`.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PLANE_API_KEY` | Yes | API key for authentication |
| `PLANE_WORKSPACE_SLUG` | Yes | Workspace slug (ours is `intervan`) |
| `PLANE_BASE_URL` | Yes | Base URL of the Plane instance (`https://ividemo.benacland.com`) |

## Available Tools

### Work Items (7 tools)

| Tool | Description |
|------|-------------|
| `list_work_items` | List work items in a project (with pagination, filtering, expansion) |
| `create_work_item` | Create a new work item |
| `retrieve_work_item` | Get a work item by UUID |
| `retrieve_work_item_by_identifier` | Get a work item by project+sequence (e.g., EDI-73) |
| `update_work_item` | Update any field on a work item |
| `delete_work_item` | Delete a work item |
| `search_work_items` | Free-text search across work item names and descriptions |

### Pages (12 tools)

| Tool | Description |
|------|-------------|
| `list_workspace_pages` | List top-level workspace (wiki) pages |
| `create_workspace_page` | Create a workspace page (with optional parent for nesting) |
| `retrieve_workspace_page` | Get a workspace page with full HTML content |
| `update_workspace_page` | Update a workspace page's name, content, or parent |
| `archive_workspace_page` | Archive a workspace page and its children |
| `list_workspace_page_children` | List child pages of a workspace page |
| `list_project_pages` | List pages in a project |
| `create_project_page` | Create a page within a project |
| `retrieve_project_page` | Get a project page with full content |
| `update_project_page` | Update a project page |
| `archive_project_page` | Archive a project page |
| `list_project_page_children` | List child pages of a project page |

### Email References (5 tools)

| Tool | Description |
|------|-------------|
| `search_email_references` | Search indexed emails by subject, sender, or folder |
| `get_email_reference` | Get full email details (body, headers, etc.) |
| `list_issue_linked_emails` | List emails linked to a work item |
| `link_email_to_issue` | Link an email reference to a work item |
| `unlink_email_from_issue` | Remove an email link from a work item |

### Issue Templates (2 tools)

| Tool | Description |
|------|-------------|
| `list_issue_templates` | List available issue templates |
| `get_issue_template` | Get full template details |

### Upstream Tools (~55 tools)

All standard Plane MCP tools are also available: projects, cycles, modules, initiatives, labels, states, work item types/properties/comments/links/relations, users, and more.

**Total: ~80 tools**

## Our Plane Instance

| Item | Value |
|------|-------|
| URL | https://ividemo.benacland.com |
| Workspace | `intervan` |
| Project | EDI Support (`8c5e9fe5-2203-4dbc-93d4-5108acc09d3d`) |
| Wiki | Workspace Pages (Knowledge Base, Partner Profiles, Reference, Procedures) |
| Emails | ~4,840 indexed from Ben's inbox |

## Development

### Running tests

```bash
# Fork-specific smoke tests (requires live Plane instance)
PLANE_API_KEY=your_key PLANE_WORKSPACE_SLUG=intervan PLANE_BASE_URL=https://ividemo.benacland.com \
  uv run pytest tests/test_fork_tools.py -v

# All tests
PLANE_API_KEY=your_key PLANE_WORKSPACE_SLUG=intervan PLANE_BASE_URL=https://ividemo.benacland.com \
  uv run pytest tests/ -v
```

### Project structure

```
plane_mcp/
  fork_api.py          # HTTP helper for custom /api/v1/ endpoints
  tools/
    work_items.py      # Work item CRUD + search (uses fork_api for reliability)
    pages.py           # Workspace + project page tools (fork addition)
    emails.py          # Email reference + linking tools (fork addition)
    templates.py       # Issue template tools (fork addition)
    ...                # Upstream tools (cycles, modules, labels, etc.)
```

### Why fork_api.py?

The upstream Plane SDK's pydantic models are strict about response shapes — for example, `WorkItemDetail.labels` expects Label objects but the API returns UUID strings when fields aren't expanded. Our `fork_request()` helper makes direct HTTP calls and returns raw dicts, avoiding these validation mismatches entirely.

## License

MIT (same as upstream)
