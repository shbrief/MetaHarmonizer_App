"""Engine bridge — reach the MetaHarmonizer engine via the existing EngineProtocol.

The MCP tools do not import the upstream ``metaharmonizer`` package directly;
they call the same ``EngineProtocol`` adapter the dashboard uses
(``app.engine_adapter.get_engine``), so the engine boundary stays in one place.
``ENGINE_IMPL`` selects the adapter (``mock`` for tests/demos, ``metaharmonizer``
for the real engine).
"""

from __future__ import annotations

import os
import sys
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd


def _ensure_backend_on_path() -> None:
    """Make ``app.engine_adapter`` importable.

    In the monorepo / docker image the dashboard backend ships alongside this
    package; add its directory to ``sys.path`` if ``app`` isn't already
    importable. ``METAHARMONIZER_BACKEND_DIR`` overrides the location.
    """
    try:
        import app.engine_adapter  # noqa: F401
        return
    except ImportError:
        pass

    candidates: list[Path] = []
    env_dir = os.getenv("METAHARMONIZER_BACKEND_DIR")
    if env_dir:
        candidates.append(Path(env_dir))
    # mcp/src/metaharmonizer_mcp/engine.py -> repo root is parents[3]
    repo_root = Path(__file__).resolve().parents[3]
    candidates.append(repo_root / "backend")

    for cand in candidates:
        if (cand / "app" / "engine_adapter").is_dir():
            sys.path.insert(0, str(cand))
            return


@lru_cache(maxsize=1)
def get_engine():
    """Return the singleton EngineProtocol adapter for this process."""
    _ensure_backend_on_path()
    from app.engine_adapter import get_engine as _get_engine

    return _get_engine()


@lru_cache(maxsize=1)
def _curated_df() -> pd.DataFrame:
    """Load the curated target schema (column names the engine maps onto).

    ``METAHARMONIZER_CURATED`` overrides the path; otherwise fall back to the
    bundled ``metadata_samples/curated_meta.csv``. Returns an empty frame if no
    curated file is found (the real engine ignores this arg and uses its own
    schema dictionary; only the mock heuristic reads the columns).
    """
    env_path = os.getenv("METAHARMONIZER_CURATED")
    repo_root = Path(__file__).resolve().parents[3]
    path = Path(env_path) if env_path else repo_root / "metadata_samples" / "curated_meta.csv"
    if path.exists():
        return pd.read_csv(path, nrows=0)
    return pd.DataFrame()


def _df_to_temp_csv(df: pd.DataFrame) -> str:
    """Write a DataFrame to a temp CSV and return its path.

    The metaharmonizer adapter takes a ``csv_path``; this materializes one.
    """
    fd, path = tempfile.mkstemp(suffix=".csv", prefix="mh_mcp_")
    os.close(fd)
    df.to_csv(path, index=False)
    return path


def harmonize_columns(columns: list[str]) -> list[dict[str, Any]]:
    """Map a list of raw column names to curated schema fields."""
    raw_df = pd.DataFrame({c: [] for c in columns})
    csv_path = _df_to_temp_csv(raw_df)
    try:
        return get_engine().harmonize_schema(
            raw_df, _curated_df(), csv_path=csv_path
        )
    finally:
        Path(csv_path).unlink(missing_ok=True)


def harmonize_values(field_name: str, values: list[str]) -> list[dict[str, Any]]:
    """Map a list of raw cell values (for one field) to ontology terms."""
    raw_df = pd.DataFrame({field_name: values})
    schema_mappings = [{"raw_column": field_name, "matched_field": field_name}]
    return get_engine().map_values(raw_df, schema_mappings)


def harmonize_table(csv_text: str) -> dict[str, Any]:
    """Harmonize a whole CSV: column mapping + value-level ontology mapping."""
    from io import StringIO

    raw_df = pd.read_csv(StringIO(csv_text))
    csv_path = _df_to_temp_csv(raw_df)
    try:
        engine = get_engine()
        schema_mappings = engine.harmonize_schema(
            raw_df, _curated_df(), csv_path=csv_path
        )
        ontology_mappings = engine.map_values(raw_df, schema_mappings)
    finally:
        Path(csv_path).unlink(missing_ok=True)
    return {
        "columns": list(raw_df.columns),
        "row_count": int(len(raw_df)),
        "schema_mappings": schema_mappings,
        "ontology_mappings": ontology_mappings,
    }
