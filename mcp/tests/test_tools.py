"""Tests for the metaharmonizer-mcp tools (against ENGINE_IMPL=mock).

These exercise the engine bridge that the MCP tools wrap, so no real model
download or torch is needed. The mock adapter ships with the dashboard backend;
the bridge adds it to sys.path automatically.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("ENGINE_IMPL", "mock")

from metaharmonizer_mcp import engine  # noqa: E402


@pytest.fixture(autouse=True)
def _force_mock_engine(monkeypatch):
    monkeypatch.setenv("ENGINE_IMPL", "mock")
    engine.get_engine.cache_clear()
    engine._curated_df.cache_clear()
    yield
    engine.get_engine.cache_clear()


def test_engine_is_mock():
    assert engine.get_engine().name == "mock"


def test_harmonize_columns():
    rows = engine.harmonize_columns(["gender", "age", "tumor_stage"])
    assert len(rows) == 3
    raw_cols = {r["raw_column"] for r in rows}
    assert raw_cols == {"gender", "age", "tumor_stage"}
    for r in rows:
        assert "matched_field" in r
        assert "confidence_score" in r
        assert isinstance(r.get("alternatives"), list)


def test_harmonize_values():
    rows = engine.harmonize_values("SEX", ["male", "female", "male"])
    assert rows  # at least one resolved value
    for r in rows:
        # Field is normalized to the engine's lowercase canonical form.
        assert r["field_name"] == "sex"
        assert "ontology_term" in r
        assert "ontology_id" in r
    # Distinct values only (mock dedupes via unique()).
    raw_values = {r["raw_value"] for r in rows}
    assert raw_values == {"male", "female"}


def test_harmonize_values_normalizes_field_case():
    # The engine's value dictionary keys fields lowercase; an upper-case field
    # from the caller must still resolve (regression: real engine returned 0
    # rows for "SEX" before the bridge lowercased the field name).
    upper = engine.harmonize_values("SEX", ["male", "female"])
    lower = engine.harmonize_values("sex", ["male", "female"])
    assert len(upper) == len(lower) > 0


def test_harmonize_table():
    csv_text = "gender,age\nmale,57\nfemale,61\n"
    result = engine.harmonize_table(csv_text)
    assert result["columns"] == ["gender", "age"]
    assert result["row_count"] == 2
    assert len(result["schema_mappings"]) == 2
    assert result["ontology_mappings"]  # values resolved


def test_tools_are_registered():
    # The FastMCP server exposes exactly the three contracted tools.
    from metaharmonizer_mcp import server

    names = {t.name for t in server.mcp._tool_manager.list_tools()}
    assert {"harmonize_table", "harmonize_columns", "harmonize_values"} <= names
