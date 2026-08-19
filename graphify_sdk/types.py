"""Graphify SDK data transfer objects (DTOs).

These types mirror the Rust structs in graphify_core and provide
JSON deserialization from graphify tool responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ─── FileType ───────────────────────────────────────────────────────────────

class FileType:
    """File classification constants."""
    CODE = "code"
    DOCUMENT = "document"
    PAPER = "paper"
    IMAGE = "image"
    RATIONALE = "rationale"
    CONCEPT = "concept"


# ─── NodeId ─────────────────────────────────────────────────────────────────

@dataclass
class NodeId:
    """Value object representing a node ID in the knowledge graph.

    Format: ``./path/to/file:kind:Name``
    (e.g., ``./src/lib.rs:function:MyFunction``)
    """
    id: str

    def parse(self) -> tuple[str, str, str]:
        """Split into (file, kind, name) components."""
        parts = self.id.split(":", 2)
        file = parts[0] if len(parts) > 0 else ""
        kind = parts[1] if len(parts) > 1 else ""
        name = parts[2] if len(parts) > 2 else ""
        return file, kind, name


# ─── Node ───────────────────────────────────────────────────────────────────

@dataclass
class Node:
    """A node in the Graphify knowledge graph."""
    id: str = ""
    label: str = ""
    file_type: str = ""
    kind: str = ""
    language: str = ""
    source_file: str = ""
    start_line: int = 0
    end_line: int = 0
    doc_comment: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None


# ─── Edge ───────────────────────────────────────────────────────────────────

@dataclass
class Edge:
    """A relationship between two nodes."""
    source: str = ""
    target: str = ""
    relation: str = ""
    source_file: str = ""
    confidence: str = ""
    source_location: str = ""
    description: str | None = None


# ─── GraphMetadata ──────────────────────────────────────────────────────────

@dataclass
class GraphMetadata:
    """Metadata about a knowledge graph."""
    version: str = ""
    generated_at: str = ""
    total_nodes: int = 0
    total_edges: int = 0
    languages: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    plugin_data: dict[str, Any] | None = None


# ─── GraphOutput ────────────────────────────────────────────────────────────

@dataclass
class GraphOutput:
    """Complete result of a graph traversal query."""
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    metadata: GraphMetadata | None = None


# ─── GraphSummary ───────────────────────────────────────────────────────────

@dataclass
class GraphSummary:
    """Result of a graphify_graph_summary call."""
    total_nodes: int = 0
    total_edges: int = 0
    languages: list[str] = field(default_factory=list)


# ─── WorkspaceContext ───────────────────────────────────────────────────────

@dataclass
class WorkspaceContext:
    """Workspace identification information."""
    workspace_key: str = ""
    workspace_name: str = ""
    root_path: str = ""
    timestamp: int = 0


# ─── MemoryQueryResult ──────────────────────────────────────────────────────

@dataclass
class MemoryQueryResult:
    """Result of a semantic memory query."""
    status: str = ""
    nodes: list[Node] = field(default_factory=list)

    @property
    def is_found(self) -> bool:
        return self.status == "found"


# ─── CoverageResult ─────────────────────────────────────────────────────────

@dataclass
class CoverageResult:
    """Coverage information for a node."""
    node: str = ""
    covered_lines: int = 0
    total_lines: int = 0
    line_rate: float = 0.0

    @property
    def percentage(self) -> float:
        """Coverage ratio as a percentage (0-100)."""
        return self.line_rate * 100


# ─── ReindexResult ──────────────────────────────────────────────────────────

@dataclass
class ReindexResult:
    """Result of a reindex operation."""
    status: str = ""
    total_nodes: int = 0
    total_edges: int = 0

    @property
    def is_success(self) -> bool:
        return self.status == "success"


# ─── RelayStatus ────────────────────────────────────────────────────────────

@dataclass
class RelayStatus:
    """Result of a relay_status call."""
    repos: dict[str, Any] = field(default_factory=dict)
    active_baton: str | None = None
    spec_drift: str | None = None
    last_update: str | None = None


# ─── ReviewFinding ──────────────────────────────────────────────────────────

@dataclass
class ReviewFinding:
    """A code review finding."""
    review_id: str = ""
    affected_symbols: list[str] = field(default_factory=list)
    finding_severity: str = ""
    resolution_status: str = ""
    review_comment: str = ""
    git_commit_sha: str | None = None

    @property
    def is_resolved(self) -> bool:
        return self.resolution_status == "resolved"


# ─── TelemetryBinding ───────────────────────────────────────────────────────

@dataclass
class TelemetryBinding:
    """Telemetry metrics for a node."""
    node: str = ""
    p99_latency: float = 0.0
    alloc_bytes: float = 0.0
    call_rate: float = 0.0
    is_hotspot: bool = False
    impact_radius: list[dict[str, Any]] | None = None


# ─── Helpers ────────────────────────────────────────────────────────────────

def _node_from_dict(d: dict[str, Any]) -> Node:
    return Node(
        id=str(d.get("id", "")),
        label=str(d.get("label", "")),
        file_type=str(d.get("file_type", "")),
        kind=str(d.get("kind", "")),
        language=str(d.get("language", "")),
        source_file=str(d.get("source_file", "")),
        start_line=int(d.get("start_line", 0)),
        end_line=int(d.get("end_line", 0)),
        doc_comment=_opt_str(d, "doc_comment"),
        description=_opt_str(d, "description"),
        metadata=d.get("metadata"),
    )


def _opt_str(d: dict[str, Any], key: str) -> str | None:
    v = d.get(key)
    return str(v) if v else None


def parse_nodes(raw: list[dict[str, Any]]) -> list[Node]:
    """Convert a list of raw dicts to Node values."""
    return [_node_from_dict(r) for r in raw]