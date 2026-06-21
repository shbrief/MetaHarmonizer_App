"""Regression guards for two real-engine bugs found in the e2e pass:

1. Schema-mapping confidence could exceed 1.0 (stage-3 similarity).
2. cBioPortal export rendered missing values as the literal string "nan".

Both need pandas (the engine adapter + exporter import it), so the module
skips gracefully in the lightweight test venv.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pandas")
import pandas as pd  # noqa: E402


def test_to_score_clamps_to_unit_interval():
    from app.engine_adapter.metaharmonizer_impl import MetaHarmonizerAdapter as A

    assert A._to_score(1.046) == 1.0
    assert A._to_score(-0.2) == 0.0
    assert A._to_score(0.5) == 0.5
    assert A._to_score(None) == 0.0
    assert A._to_score(float("nan")) == 0.0


def test_cbioportal_export_blanks_missing_values():
    from app.services import exporter

    assert exporter._sanitize_id(pd.NA) == ""
    assert exporter._normalize_survival(float("nan")) == ""
    # A real value still passes through.
    assert exporter._sanitize_id("MG100208") == "MG100208"


def test_value_rewrite_map_applies_accepted_terms():
    """U5: a column's accepted raw_value -> term mapping rewrites cells; others pass through."""
    lookup = {"adult": "Adult", "stool": "feces"}
    col = pd.Series(["adult", "stool", "weird", None])
    rewritten = col.map(lambda v, _m=lookup: _m.get(str(v), v) if pd.notna(v) else v)
    assert list(rewritten) == ["Adult", "feces", "weird", None]

