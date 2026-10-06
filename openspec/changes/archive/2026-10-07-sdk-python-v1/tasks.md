# Tasks: graphify-sdk-python v1

## Task List

### T1 — Project Scaffolding
- [x] Create directory structure (`graphify_sdk/`, `plugin/`, `tests/`)
- [x] Create `pyproject.toml`
- [x] Create `README.md` and `README.zh-TW.md`
- [x] Create `AGENTS.md`

### T2 — Model and DTO Layer
- [x] Implement Models / DTOs (`Node`, `Edge`, `GraphOutput`, `GraphSummary`)
- [x] Implement Enums (`FileType`, error mappings)

### T3 — Transport & Client Layer
- [x] Implement `GraphifyClient` — public API facade
- [x] Implement MCP transport / stdio communication
- [x] Implement auto-detection and workspace key derivation

### T4 — Plugin SDK Layer
- [x] Implement `PluginHost` / plugin bridge runner
- [x] Tool registration and JSON-RPC dispatching

### T5 — Testing & Verification
- [x] 13 pytest tests passing (client, models, transport)
- [x] Verified python packaging (`pip install -e .` / `pyproject.toml`)
