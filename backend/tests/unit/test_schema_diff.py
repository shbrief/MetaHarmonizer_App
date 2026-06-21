"""Unit tests for the schema-version diff (G6 layer A).

Pure functions over field->values maps and small CSVs; needs pandas, so the
module skips in the lightweight test venv.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pandas")
import pandas as pd  # noqa: E402

from app.services import schema_diff  # noqa: E402


def test_field_value_map_ignores_missing_markers():
    df = pd.DataFrame({"sex": ["Male", "Female", "NA", "", "na"], "age": ["1", "2", "nan", "none", "null"]})
    fvm = schema_diff.field_value_map(df)
    assert fvm["sex"] == {"Male", "Female"}
    assert fvm["age"] == {"1", "2"}


def test_diff_added_and_removed_fields():
    old = {"sex": {"Male", "Female"}, "age": {"1", "2"}}
    new = {"sex": {"Male", "Female"}, "body_site": {"feces"}}
    d = schema_diff.diff_field_maps(old, new)
    assert [f["field"] for f in d["added_fields"]] == ["body_site"]
    assert [f["field"] for f in d["removed_fields"]] == ["age"]
    assert d["summary"]["added"] == 1
    assert d["summary"]["removed"] == 1


def test_diff_changed_values():
    old = {"sex": {"Male", "Female"}}
    new = {"sex": {"Male", "Female", "Unknown"}}  # added a value
    d = schema_diff.diff_field_maps(old, new)
    assert d["changed_fields"] == [
        {"field": "sex", "added_values": ["Unknown"], "removed_values": []}
    ]
    assert d["summary"]["changed"] == 1
    assert d["summary"]["unchanged"] == 0


def test_diff_unchanged_field_not_listed():
    old = {"sex": {"Male", "Female"}, "country": {"Italy"}}
    new = {"sex": {"Male", "Female"}, "country": {"Italy", "Spain"}}
    d = schema_diff.diff_field_maps(old, new)
    changed_fields = [c["field"] for c in d["changed_fields"]]
    assert changed_fields == ["country"]  # sex unchanged -> not listed
    assert d["summary"]["unchanged"] == 1


def test_diff_csv_files(tmp_path):
    old = tmp_path / "v1.csv"
    new = tmp_path / "v2.csv"
    pd.DataFrame({"sex": ["Male", "Female"], "age": ["1", "2"]}).to_csv(old, index=False)
    # v2 drops age, adds body_site, and adds a sex value.
    pd.DataFrame({"sex": ["Male", "Female", "Unknown"], "body_site": ["feces", "feces", "blood"]}).to_csv(new, index=False)
    d = schema_diff.diff_csv_files(str(old), str(new))
    assert [f["field"] for f in d["added_fields"]] == ["body_site"]
    assert [f["field"] for f in d["removed_fields"]] == ["age"]
    assert d["changed_fields"][0]["field"] == "sex"
    assert d["changed_fields"][0]["added_values"] == ["Unknown"]
