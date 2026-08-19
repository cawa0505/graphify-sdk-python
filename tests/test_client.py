"""Tests for the Graphify Python SDK."""

from graphify_sdk import (
    Client,
    CoverageResult,
    EngineError,
    ProtocolError,
    ReindexResult,
    TransportError,
)
from graphify_sdk.types import NodeId, parse_nodes


class TestTypes:
    """Type construction and helpers."""

    def test_node_id_parse(self) -> None:
        nid = NodeId(id="./src/lib.rs:function:MyFunction")
        file, kind, name = nid.parse()
        assert file == "./src/lib.rs"
        assert kind == "function"
        assert name == "MyFunction"

    def test_node_id_parse_partial(self) -> None:
        nid = NodeId(id="partial")
        file, kind, name = nid.parse()
        assert file == "partial"
        assert kind == ""
        assert name == ""

    def test_reindex_is_success(self) -> None:
        r = ReindexResult(status="success", total_nodes=10, total_edges=20)
        assert r.is_success
        r2 = ReindexResult(status="error", total_nodes=0, total_edges=0)
        assert not r2.is_success

    def test_coverage_percentage(self) -> None:
        c = CoverageResult(node="x", covered_lines=80, total_lines=100, line_rate=0.8)
        assert c.percentage == 80.0

    def test_parse_nodes(self) -> None:
        raw = [
            {
                "id": "a:func:foo",
                "label": "foo",
                "file_type": "code",
                "kind": "function",
                "language": "rust",
                "source_file": "src/lib.rs",
                "start_line": 1,
                "end_line": 10,
            }
        ]
        nodes = parse_nodes(raw)
        assert len(nodes) == 1
        assert nodes[0].id == "a:func:foo"
        assert nodes[0].label == "foo"


class TestErrors:
    """Error hierarchy."""

    def test_transport_error(self) -> None:
        e = TransportError("connection failed")
        assert "connection failed" in str(e)
        assert isinstance(e, TransportError)

    def test_protocol_error(self) -> None:
        e = ProtocolError("invalid json")
        assert "invalid json" in str(e)

    def test_engine_error(self) -> None:
        e = EngineError(code=-32602, message="bad arg", data={"key": "value"})
        assert e.code == -32602
        assert "bad arg" in str(e)
        assert e.error_data == {"key": "value"}


class TestClientConstruction:
    """Client construction and properties."""

    def test_default_construction(self) -> None:
        client = Client()
        assert client.project_path != ""
        assert client.workspace_key != ""
        assert not client.is_running

    def test_custom_binary_path(self) -> None:
        client = Client(binary_path="/usr/local/bin/graphify")
        assert not client.is_running

    def test_workspace_context(self) -> None:
        client = Client("/tmp")
        ctx = client.workspace_context()
        assert ctx.workspace_key != ""
        assert ctx.root_path == "/tmp"

    def test_same_project_same_key(self) -> None:
        c1 = Client("/tmp/test-project")
        c2 = Client("/tmp/test-project")
        assert c1.workspace_key == c2.workspace_key

    def test_different_project_different_key(self) -> None:
        c1 = Client("/tmp/project-a")
        c2 = Client("/tmp/project-b")
        assert c1.workspace_key != c2.workspace_key