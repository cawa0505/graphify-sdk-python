"""Graphify Plugin SDK — JSON-RPC stdio host for IPC plugins.

Allows Python developers to create Graphify plugins that run as subprocesses
and communicate with Graphify Core over Stdio/JSON-RPC (MCP protocol).
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from typing import Any

ToolHandler = Callable[[dict[str, Any]], dict[str, Any] | list[Any] | str]


class Host:
    """JSON-RPC stdio host for Graphify IPC plugins.

    Reads JSON-RPC requests from stdin, dispatches to registered tool handlers,
    and writes responses to stdout.

    Usage::

        host = Host()
        host.register_tool("analyze_schema", analyze_schema, {
            "type": "object",
            "properties": {
                "migration_path": {"type": "string"}
            }
        })
        host.run()
    """

    def __init__(self) -> None:
        self._tools: dict[str, tuple[ToolHandler, dict[str, Any]]] = {}

    def register_tool(
        self,
        name: str,
        handler: ToolHandler,
        input_schema: dict[str, Any] | None = None,
        description: str = "",
    ) -> None:
        """Register a tool handler.

        Args:
            name: Tool name (e.g. ``"analyze_schema"``).
            handler: Callable that receives arguments and returns a result.
            input_schema: JSON Schema for the tool's arguments (optional).
            description: Human-readable description.
        """
        schema = input_schema or {"type": "object", "properties": {}}
        self._tools[name] = (handler, {"description": description, "inputSchema": schema})

    def run(self) -> None:
        """Start the JSON-RPC listener loop.

        Reads from stdin until EOF, dispatching requests to registered handlers.
        """
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError as e:
                self._send_error(None, -32700, f"Parse error: {e}")
                continue

            req_id = request.get("id")
            method = request.get("method", "")
            params = request.get("params", {})

            if method == "initialize":
                tools_list = [
                    {"name": name, **meta}
                    for name, (_, meta) in self._tools.items()
                ]
                self._send_result(req_id, {"tools": tools_list})

            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})

                if tool_name not in self._tools:
                    self._send_error(
                        req_id, -32601, f"Tool not found: {tool_name}"
                    )
                    continue

                handler, _ = self._tools[tool_name]
                try:
                    result = handler(arguments)
                    content = self._to_content(result)
                    self._send_result(req_id, {"content": content})
                except (TypeError, ValueError, RuntimeError) as e:
                    self._send_error(req_id, -32603, str(e))

            else:
                self._send_error(req_id, -32601, f"Method not found: {method}")

    def _to_content(self, result: Any) -> list[dict[str, str]]:
        if isinstance(result, str):
            return [{"type": "text", "text": result}]
        if isinstance(result, list):
            return [{"type": "text", "text": json.dumps(result)}]
        if isinstance(result, dict):
            return [{"type": "text", "text": json.dumps(result)}]
        return [{"type": "text", "text": str(result)}]

    def _send_result(self, req_id: Any, result: Any) -> None:
        response = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result,
        }
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()

    def _send_error(self, req_id: Any, code: int, message: str) -> None:
        response = {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        }
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()