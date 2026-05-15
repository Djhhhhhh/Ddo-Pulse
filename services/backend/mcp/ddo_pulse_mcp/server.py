"""MCP server (stdio) — thin wrapper over ddo_pulse_core.mcp_tools."""

from __future__ import annotations

import json

from ddo_pulse_core import mcp_tools

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise SystemExit(
        "MCP SDK not installed. Run: pip install 'ddo-pulse[mcp]'"
    ) from exc

mcp = FastMCP(
    "ddo-pulse",
    instructions=(
        "Ddo-Pulse: blog aggregation with LLM curation. "
        "Tools list sources, trigger fetch, read today's digest, and recent analyzed items."
    ),
)


@mcp.tool()
def list_sources() -> str:
    """List all configured subscription sources (id, name, type, url, enabled)."""
    data = mcp_tools.list_sources()
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
def trigger_fetch(source_id: int | None = None) -> str:
    """
    Fetch articles from subscription sources into the database.
    If source_id is omitted, fetches all enabled sources.
    """
    stats = mcp_tools.trigger_fetch(source_id=source_id)
    return json.dumps(stats, ensure_ascii=False, indent=2)


@mcp.tool()
def get_today_digest() -> str:
    """Return today's digest as Markdown (UTC date)."""
    return mcp_tools.get_today_digest()


@mcp.tool()
def get_recent_items(days: int = 7, min_score: int | None = None) -> str:
    """
    Return recent analyzed articles (newest first).
    days: look back window (default 7). min_score: optional minimum score filter.
    """
    items = mcp_tools.get_recent_items(days=days, min_score=min_score)
    return json.dumps(items, ensure_ascii=False, indent=2)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
