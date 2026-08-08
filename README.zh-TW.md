# graphify-sdk-python

Graphify 官方 **Python SDK** — Layer 2 外部 SDK，讓 Python 開發者與第三方
plugin 作者透過 Stdio/JSON-RPC（MCP 協議）存取 Graphify 的 `.toon` 拓撲能力。

## 定位

Graphify 的 plugin 生態分兩層：

1. **Layer 1 — 內嵌 plugin trait**（Rust，in-process）：第一方 plugin
   （`graphify-plugin-handoff`、`graphify-plugin-review`、…）實作
   `GraphifyPlugin` trait，直接在 Graphify Core 的記憶體 petgraph 上運行。
2. **Layer 2 — 外部 SDK**（本 repo）：任何語言透過 Stdio/JSON-RPC 存取
   Graphify 拓撲，由 graphify-mcp 服務。`graphify-sdk-python` 是第一個官方
   語言實作。

本 SDK 的第一個 first-class client 是改版 Python Code Review MCP
（`graphify-plugin-review` → `python/review-mcp/`），以最小成本把成熟的
Python review 工具升級成拓撲感知審查。

## 核心 API（草稿）

```python
from graphify_sdk import GraphifyClient

client = GraphifyClient(workspace_key="...")  # 自動管理 graphify-mcp 子進程

# 變更集的衝擊半徑，壓縮為 .toon 拓撲
radius = await client.get_blast_radius("git diff ...", depth=3)

# 符號的上下游呼叫鏈拓撲
topology = await client.query_symbol_topology("parse_file")
```

- `GraphifyClient(workspace_key)` — Stdio/JSON-RPC transport + 進程生命週期管理；
  `workspace_key`（graphify-core v1 契約，SipHash hex）自動透傳。
- `get_blast_radius(git_diff/files, depth=3)` — 向 Graphify Core 索取 `.toon`
  壓縮的衝擊半徑拓撲。
- `query_symbol_topology(symbol_name)` — 查詢符號的呼叫鏈拓撲。

## 目錄結構

```
├── graphify_sdk/            # SDK 套件
├── openspec/                # proposal / design / tasks（文件先行）
└── README.md / README.zh-TW.md
```

## 開發

- 安裝：`pip install -e ".[dev]"`
- 測試：`pytest`
- Lint：`ruff check .`
- 型別：`mypy graphify_sdk`

## 生態對齊

- **SDK 家族**：與未來的 `graphify-sdk-ts` / `-php` / `-rust` / `-go` 平行
  （語言順序：Python 優先；各語言獨立 repo，協議 spec 集中在 GraphifyRust）。
- **契約**：透過 Stdio+JSON-RPC 與 graphify-mcp 通訊；payload 以 `.toon`
  交換（TOON 序列化與 graphify-core 共用）。
- **開源安全**：受版本控制的檔案不含私有主機名、本地 IP 或本機絕對路徑。
