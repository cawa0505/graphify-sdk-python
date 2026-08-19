# Graphify Python SDK

Official Python SDK for [Graphify](https://github.com/cawa0505/graphify) — access
knowledge graph capabilities over the MCP (Model Context Protocol) via Stdio/JSON-RPC.

## Requirements

- Python 3.10+
- `graphify` binary on PATH (or configured path)

## Installation

```bash
pip install graphify-sdk-python
```

## Quick Start

```python
from graphify_sdk import Client

client = Client(project_path="/path/to/your/project")

# Graph summary
summary = client.graph_summary()
print(f"Nodes: {summary.total_nodes}, Edges: {summary.total_edges}")

# Semantic memory query
result = client.memory_query("find user authentication")
if result.is_found:
    for node in result.nodes:
        print(f"{node.label} ({node.kind}) in {node.source_file}")

# Trace dependency path
path = client.trace_path(
    from_="src/models/user.py:class:User",
    to="src/http/handlers/auth.py:function:login",
)
print("Path:", path)

# Query node with depth
graph = client.query_node(
    node_id="src/services/auth.py:class:AuthService",
    depth=2,
)
print(f"Found {len(graph.nodes)} related nodes")

# Always clean up
client.stop()
```

## API Reference

The SDK wraps all 24+ `graphify` tools.

### Core Graph

| Method | Description | Returns |
|--------|-------------|---------|
| `graph_summary()` | Topology metrics | `GraphSummary` |
| `query_graph(question)` | BFS traversal | `GraphOutput` |
| `query_node(node_id, ...depth)` | Node query | `GraphOutput` |
| `trace_path(from_, to)` | Shortest path | `list[str]` |
| `reindex_file(file_path)` | Reindex file | `ReindexResult` |

### Memory & Relay

| Method | Description | Returns |
|--------|-------------|---------|
| `memory_query(query, ...limit)` | Semantic search | `MemoryQueryResult` |
| `relay_init(project_context, ...kind)` | Init handoff | `dict` |
| `relay_save(params)` | Save state | `dict` |
| `relay_close(repo, next)` | Close handoff | `dict` |
| `relay_switch(repo, ...kind)` | Switch repo | `dict` |
| `relay_resume(repo, ...kind)` | Resume | `dict` |
| `relay_status()` | Status summary | `RelayStatus` |
| `relay_add(file, repo)` | Ingest doc | `dict` |

### OpenDoc

| Method | Description | Returns |
|--------|-------------|---------|
| `opendoc_index(...doc_paths)` | Index spec blocks | `dict` |
| `opendoc_get_context(symbol)` | Get symbol docs | `dict` |
| `opendoc_audit_drift()` | Audit drift | `dict` |

### Review

| Method | Description | Returns |
|--------|-------------|---------|
| `review_ingest(payload)` | Import review | `dict` |
| `review_get_context(node)` | Query reviews | `dict` |
| `review_resolve(review_id, reason)` | Resolve review | `dict` |
| `review_search_crg(...base)` | Search CRG | `dict` |

### Telemetry & Coverage

| Method | Description | Returns |
|--------|-------------|---------|
| `telemetry_ingest(source, ...path)` | Import metrics | `dict` |
| `telemetry_get_context(node, ...radius)` | Query telemetry | `dict` |
| `coverage_ingest(format, data)` | Import coverage | `dict` |
| `coverage_get_context(node)` | Query coverage | `CoverageResult` |
| `coverage_blindspots()` | Low-coverage list | `dict` |

### Plugin Gateway

| Method | Description | Returns |
|--------|-------------|---------|
| `plugin_notify(kind)` | Broadcast update | `dict` |

## Architecture

```
Python App → Client → Transport (Stdio/JSON-RPC) → graphify (Rust)
```

- **Zero external dependencies**: uses only the Python standard library
- **Synchronous API**: thread-safe, request-response over stdio
- **Auto workspace key**: derives from project path via CRC32 (cross-SDK consistent)
- **Lazy process start**: transport spawns `graphify` on first request

## Project Structure

```
graphify-sdk-python/
├── graphify_sdk/
│   ├── __init__.py     # Public API exports
│   ├── client.py       # Client class — wraps all 24+ MCP tools
│   ├── transport.py    # Stdio/JSON-RPC transport
│   ├── errors.py       # Typed error hierarchy
│   ├── types.py        # Data transfer objects (15+ dataclasses)
│   └── plugin/
│       ├── __init__.py
│       └── host.py     # Plugin SDK — JSON-RPC stdio host
├── tests/
│   ├── __init__.py
│   └── test_client.py
├── pyproject.toml
└── README.md
```

## Plugin SDK

The `plugin` package provides a JSON-RPC stdio host for building Graphify plugins
in Python. See [graphify_sdk/plugin/host.py](graphify_sdk/plugin/host.py) for details.

```python
from graphify_sdk.plugin import Host

host = Host()
host.register_tool(
    "analyze",
    lambda args: {"status": "ok", "input": args},
    input_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Project path"},
        },
    },
    description="Analyze project structure",
)
host.run()
```

## Binary Compilation

For standalone deployment with Nuitka:

```bash
nuitka --standalone --onefile --output-filename=graphify-tools-py graphify_sdk/__init__.py
```

## Development

```bash
pip install -e ".[dev]"
pytest          # Run tests
ruff check .    # Lint
mypy graphify_sdk  # Type check
```

## License

MIT