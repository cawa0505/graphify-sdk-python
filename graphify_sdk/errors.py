"""Graphify SDK typed error hierarchy.

All errors raised by the SDK inherit from GraphifyError.
"""

from __future__ import annotations


class GraphifyError(Exception):
    """Base error for all Graphify SDK errors."""


class TransportError(GraphifyError):
    """I/O or process management error with the MCP transport."""


class ProtocolError(GraphifyError):
    """JSON-RPC protocol error."""


class EngineError(GraphifyError):
    """Error returned by the graphify engine."""

    def __init__(self, code: int, message: str, data: dict | None = None) -> None:
        super().__init__(f"[Engine] {message}")
        self.code = code
        self.error_data = data