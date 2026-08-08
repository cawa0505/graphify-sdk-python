# graphify-sdk-python

The official **Graphify Python SDK** — Layer 2 external SDK that lets Python
developers and third-party plugin authors access Graphify's `.toon` topology
capabilities over the Stdio/JSON-RPC (MCP) protocol.

## Positioning

Graphify's plugin ecosystem is two-layered:

1. **Layer 1 — embedded plugin trait** (Rust, in-process): first-party plugins
   (`graphify-plugin-handoff`, `graphify-plugin-review`, …) implement the
   `GraphifyPlugin` trait and run directly on Graphify Core's in-memory petgraph.
2. **Layer 2 — external SDK** (this repo): any-language access to Graphify's
   topology via Stdio/JSON-RPC, served by graphify-mcp. `graphify-sdk-python`
   is the first official language implementation.

The first first-class client of this SDK is the revamped Python Code Review MCP
(`graphify-plugin-review` → `python/review-mcp/`), which upgrades a mature
Python review tool into a topology-aware reviewer with minimal cost.

## Core API (draft)

```python
from graphify_sdk import GraphifyClient

client = GraphifyClient(workspace_key="...")  # auto-manages graphify-mcp subprocess

# Impact radius of a change set, compressed to .toon topology
radius = await client.get_blast_radius("git diff ...", depth=3)

# Up/downstream call-chain topology of a symbol
topology = await client.query_symbol_topology("parse_file")
```

- `GraphifyClient(workspace_key)` — Stdio/JSON-RPC transport + process lifecycle
  management; `workspace_key` (graphify-core v1 contract, SipHash hex) is
  transparently passed through.
- `get_blast_radius(git_diff/files, depth=3)` — requests the `.toon`-compressed
  impact-radius topology from Graphify Core.
- `query_symbol_topology(symbol_name)` — queries the symbol's call-chain
  topology.

## Repository layout

```
├── graphify_sdk/            # the SDK package
├── openspec/                # proposal / design / tasks (docs-first)
└── README.md / README.zh-TW.md
```

## Development

- Install: `pip install -e ".[dev]"`
- Test: `pytest`
- Lint: `ruff check .`
- Type: `mypy graphify_sdk`

## Ecosystem alignment

- **SDK family**: sibling of future `graphify-sdk-ts` / `-php` / `-rust` / `-go`
  (language order: Python first; per-language repos, protocol spec centralized
  in GraphifyRust).
- **Contract**: communicates with graphify-mcp via Stdio+JSON-RPC; payload
  exchanged as `.toon` (TOON serialization shared with graphify-core).
- **Open-source safe**: no private hostnames, local IPs, or machine paths in
  version-controlled files.
