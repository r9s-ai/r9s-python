"""CLI handler for MCP server commands.

Usage:
    r9s mcp serve                       # Start MCP server (all modules)
    r9s mcp serve --module models       # Models module only
    r9s mcp serve --transport sse       # Use SSE transport
    r9s mcp list-tools                  # List available tools
"""

import argparse
import json
import os
import sys
from typing import Optional

from r9s.cli_tools.ui.terminal import error, header, info, success


def handle_mcp_serve(args: argparse.Namespace) -> None:
    """Start the MCP server."""
    from r9s.mcp.server import MCPServer

    # Parse modules
    modules = None
    if args.module:
        modules = [m.strip() for m in args.module.split(",")]
        valid_modules = {"models", "agents", "usage"}
        for m in modules:
            if m not in valid_modules:
                error(f"Unknown module: {m}")
                error(f"Valid modules: {', '.join(sorted(valid_modules))}")
                sys.exit(1)

    # Get credentials
    api_key = args.api_key or os.getenv("R9S_API_KEY")
    base_url = args.base_url or os.getenv("R9S_BASE_URL")

    if not api_key:
        error("R9S_API_KEY not set. Set it via --api-key or environment variable.")
        sys.exit(1)

    # Create and run server
    server = MCPServer(
        modules=modules,
        api_key=api_key,
        base_url=base_url,
    )

    try:
        server.run(transport=args.transport)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        error(f"Server error: {e}")
        sys.exit(1)


def handle_mcp_list_tools(args: argparse.Namespace) -> None:
    """List available MCP tools."""
    from r9s.mcp.server import MCPServer

    # Parse modules
    modules = None
    if args.module:
        modules = [m.strip() for m in args.module.split(",")]

    server = MCPServer(modules=modules)
    tools = server.list_tools()

    if args.json:
        print(json.dumps({"tools": tools}, indent=2))
        return

    header("Available MCP Tools")
    print()

    # Group by module
    models_tools = [t for t in tools if t["name"] in {"list_models", "get_model_status", "recommend_model", "compare_models"}]
    agents_tools = [t for t in tools if t["name"] in {"list_agents", "get_agent", "invoke_agent"}]
    usage_tools = [t for t in tools if t["name"] in {"get_usage_summary", "estimate_cost", "get_budget_status"}]

    if models_tools:
        info("r9s-models:")
        for tool in models_tools:
            status = "" if "[Coming Soon]" not in tool.get("description", "") else " (coming soon)"
            print(f"  - {tool['name']}{status}")
            desc = tool.get("description", "").replace("[Coming Soon] ", "")
            print(f"    {desc[:70]}...")
        print()

    if agents_tools:
        info("r9s-agents:")
        for tool in agents_tools:
            status = "" if "[Coming Soon]" not in tool.get("description", "") else " (coming soon)"
            print(f"  - {tool['name']}{status}")
        print()

    if usage_tools:
        info("r9s-usage:")
        for tool in usage_tools:
            status = "" if "[Coming Soon]" not in tool.get("description", "") else " (coming soon)"
            print(f"  - {tool['name']}{status}")
        print()

    print(f"Total: {len(tools)} tools")


def handle_mcp_test(args: argparse.Namespace) -> None:
    """Test an MCP tool locally."""
    import asyncio
    from r9s.mcp.server import MCPServer

    api_key = args.api_key or os.getenv("R9S_API_KEY")
    base_url = args.base_url or os.getenv("R9S_BASE_URL")

    if not api_key:
        error("R9S_API_KEY not set")
        sys.exit(1)

    server = MCPServer(api_key=api_key, base_url=base_url)

    # Parse arguments
    tool_args = {}
    if args.args:
        for arg in args.args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                # Try to parse as JSON
                try:
                    tool_args[key] = json.loads(value)
                except json.JSONDecodeError:
                    tool_args[key] = value

    info(f"Testing tool: {args.tool}")
    info(f"Arguments: {json.dumps(tool_args)}")
    print()

    async def run_test():
        result = await server.call_tool(args.tool, tool_args)
        return result

    result = asyncio.run(run_test())

    if result.get("isError"):
        error("Tool returned error:")
        print(result.get("content", [{}])[0].get("text", "Unknown error"))
    else:
        success("Tool result:")
        content = result.get("content", [{}])[0].get("text", "{}")
        print(content)
