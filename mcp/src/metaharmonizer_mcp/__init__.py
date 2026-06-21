"""metaharmonizer-mcp — MCP server for the MetaHarmonizer engine.

Exposes three tools (harmonize_table, harmonize_columns, harmonize_values) over
the Model Context Protocol so any MCP-aware client (Claude Desktop, Cursor,
GitHub Copilot, Cline, ...) can call the same engine the dashboard uses, through
the existing ``EngineProtocol``.
"""

__version__ = "0.1.0"
