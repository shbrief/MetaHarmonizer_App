"""Unit tests for the LinkML export gate (G9).

Validates that the controlled-vocabulary check loads the checklist enums from
the LinkML schema YAML and flags out-of-vocabulary values + unprefixed survival
statuses. Pure (no DB); needs only PyYAML.
"""

from __future__ import annotations

import pytest

pytest.importorskip("yaml")

from app.services import linkml_gate  # noqa: E402


def test_enums_loaded_from_schema():
    enum_for_slot = linkml_gate._enum_for_slot()
    assert enum_for_slot["SEX"] == {"Female", "Male"}
    assert enum_for_slot["SAMPLE_CLASS"] == {"Tumor", "CellLine", "Xenograft", "Organoid"}
    assert enum_for_slot["SAMPLE_TYPE"] == {"Primary", "Metastasis", "Recurrence"}
    assert enum_for_slot["SOMATIC_STATUS"] == {"Matched", "Unmatched"}


def test_clean_columns_pass():
    columns = {
        "PATIENT_ID": ["p1", "p2"],
        "SEX": ["Female", "Male"],
        "SAMPLE_TYPE": ["Primary", "Metastasis"],
        "OS_STATUS": ["0:LIVING", "1:DECEASED"],
    }
    assert linkml_gate.validate_clinical_columns(columns) == []


def test_bad_enum_flagged():
    columns = {"SEX": ["Female", "M", "male"]}
    violations = linkml_gate.validate_clinical_columns(columns)
    bad = {v["value"] for v in violations}
    assert bad == {"M", "male"}
    assert all(v["rule"] == "enum" for v in violations)
    assert all(v["column"] == "SEX" for v in violations)


def test_unprefixed_survival_status_flagged():
    columns = {"OS_STATUS": ["0:LIVING", "DECEASED", "LIVING"]}
    violations = linkml_gate.validate_clinical_columns(columns)
    bad = {v["value"] for v in violations}
    assert bad == {"DECEASED", "LIVING"}
    assert all(v["rule"] == "survival_status_prefix" for v in violations)


def test_somatic_status_is_enum_not_survival():
    # SOMATIC_STATUS ends in _STATUS but is an enum, not a survival column.
    columns = {"SOMATIC_STATUS": ["Matched", "Unmatched"]}
    assert linkml_gate.validate_clinical_columns(columns) == []
    columns_bad = {"SOMATIC_STATUS": ["matched"]}
    violations = linkml_gate.validate_clinical_columns(columns_bad)
    assert violations and violations[0]["rule"] == "enum"


def test_blank_and_none_values_ignored():
    columns = {"SEX": ["Female", "", None, "  "]}
    assert linkml_gate.validate_clinical_columns(columns) == []


def test_unknown_columns_ignored():
    # A column with no enum slot and not a survival status is not checked.
    columns = {"BODY_SITE": ["anything", "goes"]}
    assert linkml_gate.validate_clinical_columns(columns) == []
