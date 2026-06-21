# metaharmonizer-mcp

An [MCP](https://modelcontextprotocol.io) server that exposes the MetaHarmonizer
engine as three tools, so any MCP-aware client (Claude Desktop, Cursor, GitHub
Copilot, Cline, …) can harmonize clinical metadata without going through the web
UI. It calls the **same engine the dashboard uses**, through the existing
`EngineProtocol` adapter (`ENGINE_IMPL` selects `mock` or `metaharmonizer`).

This is the G3 deliverable of the MetaHarmonizerApp grant.

## Tools

| Tool | Input | Output |
| --- | --- | --- |
| `harmonize_table` | `csv_text` (a whole CSV) | `columns`, `row_count`, `schema_mappings`, `ontology_mappings` |
| `harmonize_columns` | `columns: list[str]` | one mapping per column → curated field (+ confidence, alternatives) |
| `harmonize_values` | `field_name`, `values: list[str]` | each value → ontology term + id |

## Install

```bash
pip install metaharmonizer-mcp          # mock engine (fast, no torch)
pip install "metaharmonizer-mcp[engine]" # + the real metaharmonizer engine
```

The server reaches the engine adapter that ships with the dashboard backend. In
the monorepo / docker image it is found automatically; otherwise point
`METAHARMONIZER_BACKEND_DIR` at the `backend/` directory.

## Run

```bash
metaharmonizer-mcp                  # stdio (default — for desktop clients)
metaharmonizer-mcp --transport sse  # SSE / HTTP (for networked clients)
```

Environment:

- `ENGINE_IMPL` — `mock` (default for demos/tests) or `metaharmonizer` (real engine).
- `METAHARMONIZER_CURATED` — path to the curated target schema CSV (defaults to
  the bundled `metadata_samples/curated_meta.csv`).
- `METAHARMONIZER_BACKEND_DIR` — path to the dashboard `backend/` (only if not
  auto-discovered).
- `METAHARMONIZER_PREWARM` — `1` (default) loads the engine models **at server
  startup** so the user's first tool call is already warm; set `0` (or pass
  `--no-prewarm`) to defer the cold start to the first call. With the real
  engine, pre-warm takes ~10–15 s once; warm tool calls then run in seconds.

## Wire it into a client

### Claude Desktop

Add to `claude_desktop_config.json` (Settings → Developer → Edit Config):

```json
{
  "mcpServers": {
    "metaharmonizer": {
      "command": "metaharmonizer-mcp",
      "env": { "ENGINE_IMPL": "mock" }
    }
  }
}
```

Restart Claude Desktop, then ask: *"Use harmonize_table to map this CSV: …"*.

### Cursor

`~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "metaharmonizer": { "command": "metaharmonizer-mcp", "env": { "ENGINE_IMPL": "mock" } }
  }
}
```

### VS Code (GitHub Copilot) / Cline

Both read an `mcpServers` block of the same shape; point `command` at
`metaharmonizer-mcp` (or `python -m metaharmonizer_mcp.server`).

## Develop / test

```bash
cd mcp
pip install -e ".[dev]"
ENGINE_IMPL=mock PYTHONPATH=src pytest tests -q
```
