"""MCP Server implementation for r9s Gateway.

This module implements the Model Context Protocol (MCP) server that exposes
r9s Gateway capabilities to AI assistants.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Callable, Optional, Sequence

from r9s.mcp.tools.models import MODELS_TOOLS, handle_models_tool
from r9s.mcp.tools.agents import AGENTS_TOOLS, handle_agents_tool
from r9s.mcp.tools.usage import USAGE_TOOLS, handle_usage_tool

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Server for r9s Gateway.

    Exposes r9s capabilities via the Model Context Protocol.
    Supports stdio and SSE transports.
    """

    def __init__(
        self,
        modules: Optional[Sequence[str]] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize MCP server.

        Args:
            modules: List of modules to enable ("models", "agents", "usage").
                     If None, all modules are enabled.
            api_key: r9s API key. If None, reads from R9S_API_KEY env var.
            base_url: r9s base URL. If None, reads from R9S_BASE_URL env var.
        """
        self.modules = set(modules) if modules else {"models", "agents", "usage"}
        self.api_key = api_key
        self.base_url = base_url
        self._tools: dict[str, dict[str, Any]] = {}
        self._handlers: dict[str, Callable] = {}
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Register tools based on enabled modules."""
        if "models" in self.modules:
            for tool in MODELS_TOOLS:
                self._tools[tool["name"]] = tool
                self._handlers[tool["name"]] = handle_models_tool

        if "agents" in self.modules:
            for tool in AGENTS_TOOLS:
                self._tools[tool["name"]] = tool
                self._handlers[tool["name"]] = handle_agents_tool

        if "usage" in self.modules:
            for tool in USAGE_TOOLS:
                self._tools[tool["name"]] = tool
                self._handlers[tool["name"]] = handle_usage_tool

    def get_server_info(self) -> dict[str, Any]:
        """Return MCP server information."""
        return {
            "name": "r9s",
            "version": "0.1.0",
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
            },
        }

    def list_tools(self) -> list[dict[str, Any]]:
        """Return list of available tools."""
        return list(self._tools.values())

    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a tool and return results.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if name not in self._tools:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
            }

        handler = self._handlers.get(name)
        if not handler:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"No handler for tool: {name}"}],
            }

        try:
            result = await handler(
                name,
                arguments,
                api_key=self.api_key,
                base_url=self.base_url,
            )
            return {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
            }
        except Exception as e:
            logger.exception(f"Tool {name} failed")
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            }

    async def handle_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """Handle an incoming JSON-RPC message.

        Args:
            message: JSON-RPC request

        Returns:
            JSON-RPC response
        """
        method = message.get("method", "")
        msg_id = message.get("id")
        params = message.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": self.get_server_info(),
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": self.list_tools()},
            }

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = await self.call_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result,
            }

        elif method == "notifications/initialized":
            # Client notification, no response needed
            return None  # type: ignore

        elif method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {},
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}",
                },
            }

    async def run_stdio(self) -> None:
        """Run MCP server using stdio transport."""
        logger.info("Starting MCP server (stdio transport)")
        logger.info(f"Enabled modules: {', '.join(sorted(self.modules))}")
        logger.info(f"Available tools: {', '.join(sorted(self._tools.keys()))}")

        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(
            lambda: protocol, sys.stdin
        )

        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(
            writer_transport, writer_protocol, reader, asyncio.get_event_loop()
        )

        buffer = b""
        while True:
            try:
                chunk = await reader.read(4096)
                if not chunk:
                    break

                buffer += chunk

                # Process complete messages (newline-delimited JSON)
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line.strip():
                        continue

                    try:
                        message = json.loads(line.decode("utf-8"))
                        response = await self.handle_message(message)
                        if response is not None:
                            response_bytes = json.dumps(response).encode("utf-8") + b"\n"
                            writer.write(response_bytes)
                            await writer.drain()
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON: {e}")
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": {"code": -32700, "message": "Parse error"},
                        }
                        writer.write(json.dumps(error_response).encode("utf-8") + b"\n")
                        await writer.drain()

            except Exception as e:
                logger.exception(f"Error in stdio loop: {e}")
                break

        logger.info("MCP server stopped")

    def run(self, transport: str = "stdio") -> None:
        """Run the MCP server.

        Args:
            transport: Transport type ("stdio" or "sse")
        """
        if transport == "stdio":
            asyncio.run(self.run_stdio())
        elif transport == "sse":
            raise NotImplementedError("SSE transport not yet implemented")
        else:
            raise ValueError(f"Unknown transport: {transport}")
