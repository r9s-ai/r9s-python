"""r9s MCP (Model Context Protocol) Server.

This module provides MCP servers that expose r9s Gateway capabilities
to AI assistants and coding tools (Claude, Cursor, VS Code, etc.).

Available servers:
- r9s-models: Model discovery, comparison, and recommendations
- r9s-agents: Agent management and invocation (planned)
- r9s-usage: Usage tracking and cost analytics (planned)

Usage:
    r9s mcp serve                      # All modules
    r9s mcp serve --module models      # Models only
    r9s mcp serve --transport sse      # SSE transport
"""

from r9s.mcp.server import MCPServer

__all__ = ["MCPServer"]
