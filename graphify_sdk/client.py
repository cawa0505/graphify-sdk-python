"""Graphify Python SDK — main client.

Provides access to all graphify tools over Stdio/JSON-RPC.
Auto-derives ``workspace_key`` from the project path.
Lazy initialization: the transport subprocess spawns on the first request.
"""

from __future__ import annotations

import os
import zlib
from typing import Any

from .errors import ProtocolError
from .transport import Transport
from .types import (
    CoverageResult,
    GraphOutput,
    GraphSummary,
    MemoryQueryResult,
    ReindexResult,
    RelayStatus,
    WorkspaceContext,
)

__all__ = ["Client"]


class Client:
    """Main Graphify SDK client.

    Args:
        project_path: Project root path (auto-detects from ``cwd`` if empty).
        binary_path: Path to the ``graphify`` binary (default: ``"graphify"``).
        timeout: I/O timeout in seconds (default: 30).
    """

    def __init__(
        self,
        project_path: str = "",
        *,
        binary_path: str = "graphify",
        timeout: float = 30.0,
    ) -> None:
        if not project_path:
            project_path = os.getcwd()
        project_path = os.path.abspath(project_path)

        self._project_path = project_path
        self._workspace_key = _derive_workspace_key(project_path)
        self._workspace_name = os.path.basename(project_path)
        self._transport = Transport(binary_path, timeout, project_path)

    # ── Properties ──────────────────────────────────────────────────────

    @property
    def workspace_key(self) -> str:
        """The auto-derived workspace key."""
        return self._workspace_key

    @property
    def project_path(self) -> str:
        """The project root path."""
        return self._project_path

    # ── Workspace ────────────────────────────────────────────────────────

    def workspace_context(self) -> WorkspaceContext:
        """Return the current workspace context."""
        import time

        return WorkspaceContext(
            workspace_key=self._workspace_key,
            workspace_name=self._workspace_name,
            root_path=self._project_path,
            timestamp=int(time.time()),
        )

    # ── Core Graph Tools ─────────────────────────────────────────────────

    def graph_summary(self) -> GraphSummary:
        """Return high-level topology metrics."""
        result = self._call("graphify_graph_summary", None)
        return _map_to(GraphSummary, result)

    def query_graph(self, question: str) -> GraphOutput:
        """Perform a BFS traversal by question."""
        result = self._call("graphify_graph_query", {"question": question})
        return _map_to(GraphOutput, result)

    def query_node(self, node_id: str, depth: int | None = None) -> GraphOutput:
        """Query a node by ID with optional depth."""
        args: dict[str, Any] = {"node_id": node_id}
        if depth is not None and depth > 0:
            args["depth"] = depth
        result = self._call("graphify_graph_query_node", args)
        return _map_to(GraphOutput, result)

    def trace_path(self, from_: str, to: str) -> list[str]:
        """Find the shortest path between two nodes."""
        result = self._call(
            "graphify_graph_trace_path", {"from": from_, "to": to}
        )
        raw = result.get("path", [])
        return [str(v) for v in raw] if isinstance(raw, list) else []

    def reindex_file(self, file_path: str) -> ReindexResult:
        """Reindex a file into the graph."""
        result = self._call("graphify_graph_reindex", {"file_path": file_path})
        return _map_to(ReindexResult, result)

    # ── Memory Query ────────────────────────────────────────────────────

    def memory_query(self, query: str, limit: int | None = None) -> MemoryQueryResult:
        """Perform a semantic memory search."""
        args: dict[str, Any] = {
            "workspace_key": self._workspace_key,
            "query": query,
        }
        if limit is not None and limit > 0:
            args["limit"] = limit
        result = self._call("graphify_memory_query", args)
        return _map_to(MemoryQueryResult, result)

    # ── Relay / Handoff Tools ───────────────────────────────────────────

    def relay_init(self, project_context: str, kind: str | None = None) -> dict[str, Any]:
        """Initialize a relay session."""
        args: dict[str, Any] = {"project_context": project_context}
        if kind is not None:
            args["kind"] = kind
        return self._call("graphify_relay_init", args)

    def relay_save(self, params: dict[str, Any]) -> dict[str, Any]:
        """Save session state."""
        return self._call("graphify_relay_save", params)

    def relay_close(self, repo: str, next: str) -> dict[str, Any]:
        """Close a relay session."""
        return self._call("graphify_relay_close", {"repo": repo, "next": next})

    def relay_switch(self, repo: str, kind: str | None = None) -> dict[str, Any]:
        """Switch to another repo."""
        args: dict[str, Any] = {"repo": repo}
        if kind is not None:
            args["kind"] = kind
        return self._call("graphify_relay_switch", args)

    def relay_resume(self, repo: str, kind: str | None = None) -> dict[str, Any]:
        """Resume a relay session."""
        args: dict[str, Any] = {"repo": repo}
        if kind is not None:
            args["kind"] = kind
        return self._call("graphify_relay_resume", args)

    def relay_status(self) -> RelayStatus:
        """Return relay status summary."""
        result = self._call("graphify_relay_status", None)
        return _map_to(RelayStatus, result)

    def relay_add(self, file: str, repo: str) -> dict[str, Any]:
        """Ingest a TODO/handoff doc into relay."""
        return self._call("graphify_relay_add", {"file": file, "repo": repo})

    # ── OpenDoc Tools ──────────────────────────────────────────────────

    def opendoc_index(self, doc_paths: list[str] | None = None) -> dict[str, Any]:
        """Index all spec blocks in the workspace."""
        args: dict[str, Any] = {}
        if doc_paths is not None:
            args["doc_paths"] = doc_paths
        return self._call("graphify_opendoc_index", args)

    def opendoc_get_context(self, symbol: str) -> dict[str, Any]:
        """Return spec blocks documenting a symbol."""
        return self._call("graphify_opendoc_get_context", {"symbol": symbol})

    def opendoc_audit_drift(self) -> dict[str, Any]:
        """Audit doc-side drift."""
        return self._call("graphify_opendoc_audit_drift", None)

    # ── Review Tools ────────────────────────────────────────────────────

    def review_ingest(self, payload: str) -> dict[str, Any]:
        """Import a CRG review payload."""
        return self._call("graphify_review_ingest", {"payload": payload})

    def review_get_context(self, node: str) -> dict[str, Any]:
        """Query unresolved reviews for a node."""
        return self._call("graphify_review_get_context", {"node": node})

    def review_resolve(self, review_id: str, reason: str) -> dict[str, Any]:
        """Mark a review as resolved."""
        return self._call(
            "graphify_review_resolve",
            {"review_id": review_id, "reason": reason},
        )

    def review_search_crg(self, base: str | None = None) -> dict[str, Any]:
        """Search CRG for changed functions."""
        args: dict[str, Any] = {}
        if base is not None:
            args["base"] = base
        return self._call("graphify_review_search_crg", args)

    # ── Telemetry Tools ─────────────────────────────────────────────────

    def telemetry_ingest(
        self, source: str, path_or_draco_params: str | None = None
    ) -> dict[str, Any]:
        """Import telemetry metrics."""
        args: dict[str, Any] = {"source": source}
        if path_or_draco_params is not None:
            args["path_or_draco_params"] = path_or_draco_params
        return self._call("graphify_telemetry_ingest", args)

    def telemetry_get_context(
        self, node: str, include_impact_radius: bool = False
    ) -> dict[str, Any]:
        """Query telemetry bindings for a node."""
        args: dict[str, Any] = {"node": node}
        if include_impact_radius:
            args["include_impact_radius"] = True
        return self._call("graphify_telemetry_get_context", args)

    # ── Coverage Tools ──────────────────────────────────────────────────

    def coverage_ingest(self, format: str, data: str) -> dict[str, Any]:
        """Import coverage data."""
        return self._call(
            "graphify_coverage_ingest", {"format": format, "data": data}
        )

    def coverage_get_context(self, node: str) -> CoverageResult:
        """Query coverage for a node."""
        result = self._call("graphify_coverage_get_context", {"node": node})
        return _map_to(CoverageResult, result)

    def coverage_blindspots(self) -> dict[str, Any]:
        """List low-coverage nodes."""
        return self._call("graphify_coverage_blindspots", None)

    # ── Plugin Gateway ──────────────────────────────────────────────────

    def plugin_notify(self, kind: str) -> dict[str, Any]:
        """Broadcast a graph update notification to all plugins."""
        return self._call("graphify_plugin_notify", {"kind": kind})

    # ── Lifecycle ───────────────────────────────────────────────────────

    def start(self) -> None:
        """Explicitly start the transport. Auto-starts on first request."""
        self._transport.start()

    def stop(self) -> None:
        """Stop the transport and clean up."""
        self._transport.stop()

    @property
    def is_running(self) -> bool:
        """Whether the transport subprocess is running."""
        return self._transport.is_running

    # ── Internal ────────────────────────────────────────────────────────

    def _call(self, method: str, args: dict[str, Any] | None) -> dict[str, Any]:
        """Low-level MCP tool call."""
        if args is None:
            args = {}
        return self._transport.call(method, args)


# ── Helpers ────────────────────────────────────────────────────────────────

def _derive_workspace_key(project_path: str) -> str:
    """Create a stable workspace key from a project path.

    Uses CRC32 for cross-platform stability (mirrors the Go and PHP SDKs).
    """
    crc = zlib.crc32(project_path.encode("utf-8"))
    return format(crc & 0xFFFFFFFF, "x")


def _map_to(cls: type, data: dict[str, Any]) -> Any:
    """Convert a raw dict to a typed dataclass via JSON round-trip."""
    import json as _json

    try:
        raw = _json.dumps(data)
        return _json.loads(raw, object_hook=_make_hook(cls))
    except (TypeError, _json.JSONDecodeError) as e:
        raise ProtocolError(f"marshal to {cls.__name__}: {e}") from e


def _make_hook(cls: type) -> Any:
    """Create a JSON object hook that maps dicts to the target dataclass."""

    def hook(d: dict[str, Any]) -> Any:
        import dataclasses

        if not hasattr(cls, "__dataclass_fields__"):
            return d
        fields = {f.name for f in dataclasses.fields(cls)}
        if not fields.issuperset(d.keys()):
            return d
        try:
            return cls(**{k: v for k, v in d.items() if k in fields})
        except (TypeError, ValueError):
            return d

    return hook