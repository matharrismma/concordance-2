"""mcp — the sovereign MCP server (stdio JSON-RPC) exposing the floor to agents. See server.py."""
from __future__ import annotations

from .http import handle_http
from .server import handle, serve_stdio

__all__ = ["handle", "serve_stdio", "handle_http"]
