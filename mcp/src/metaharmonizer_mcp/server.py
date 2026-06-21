"""metaharmonizer-mcp server — three tools over the Model Context Protocol.

Tools:
  - harmonize_table   : a full CSV -> column mappings + value-level ontology mappings
  - harmonize_columns : raw column names -> curated schema fields
  - harmonize_values  : raw cell values (for one field) -> ontology terms + ids

Transports:
  - stdio (default)   : `metaharmonizer-mcp` or `metaharmonizer-mcp --transport stdio`
  - sse / http        : `metaharmonizer-mcp --transport sse`

The engine is selected by the ``ENGINE_IMPL`` env var (``mock`` for a fast,
dependency-free demo; ``metaharmonizer`` for the real engine).
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import engine

logger = logging.getLogger("metaharmonizer_mcp")

mcp = FastMCP("metaharmonizer")


@mcp.tool()
def harmonize_table(csv_text: str) -> dict[str, Any]:
    """Harmonize a whole clinical-metadata table.

    Args:
        csv_text: The CSV contents (header row + data rows) as text.

    Returns:
        A dict with ``columns``, ``row_count``, ``schema_mappings`` (each raw
        column mapped to a curated field with confidence + alternatives), and
        ``ontology_mappings`` (cell values resolved to ontology terms + ids).
    """
    return engine.harmonize_table(csv_text)


@mcp.tool()
def harmonize_columns(columns: list[str]) -> list[dict[str, Any]]:
    """Map raw column names to curated cBioPortal schema fields.

    Args:
        columns: Raw column names, e.g. ``["gender", "tumor stage", "os days"]``.

    Returns:
        One mapping per column: ``raw_column``, ``matched_field``,
        ``confidence_score``, ``stage``, ``method``, and ranked ``alternatives``.
    """
    return engine.harmonize_columns(columns)


@mcp.tool()
def harmonize_values(field_name: str, values: list[str]) -> list[dict[str, Any]]:
    """Resolve raw cell values to ontology terms for a given field.

    Args:
        field_name: The (harmonized) field the values belong to, e.g. ``SEX``.
        values: Raw cell values, e.g. ``["male", "female", "F", "M"]``.

    Returns:
        One row per distinct value: ``field_name``, ``raw_value``,
        ``ontology_term``, ``ontology_id``, ``confidence_score``, ``status``.
    """
    return engine.harmonize_values(field_name, values)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="metaharmonizer-mcp")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport (default: stdio).",
    )
    parser.add_argument(
        "--no-prewarm",
        action="store_true",
        help="Skip loading engine models at startup (first tool call pays the "
        "cold start instead).",
    )
    args = parser.parse_args(argv)

    # Pay the engine cold start (model load + KB) at server startup, not on the
    # user's first tool call. Desktop clients (Claude, Cursor) launch this as a
    # subprocess, so without pre-warm the first harmonize would block for the
    # full model-load. Best-effort: a warm-up failure must not stop the server.
    # ``METAHARMONIZER_PREWARM=0`` (or --no-prewarm) disables it.
    prewarm = not args.no_prewarm and os.getenv("METAHARMONIZER_PREWARM", "1") != "0"
    if prewarm:
        logging.basicConfig(level=logging.INFO, stream=sys.stderr)
        try:
            logger.info("metaharmonizer-mcp: pre-warming engine (%s)...",
                        os.getenv("ENGINE_IMPL", "metaharmonizer"))
            engine.get_engine().pre_warm()
            logger.info("metaharmonizer-mcp: engine ready.")
        except Exception as exc:  # noqa: BLE001 — warm-up must never block startup
            logger.warning("metaharmonizer-mcp: pre-warm skipped (%s)", exc)

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
