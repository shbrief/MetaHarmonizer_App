"""LinkML export gate — enforce the cBioPortal controlled vocabularies (G9).

The contract's export gate is "passing LinkML + passing validateData.py". This
module is the LinkML half: it loads the controlled vocabularies from
``data/linkml/cbioportal_clinical.yaml`` (the authoritative transcription of the
curation checklist) and checks a harmonized table's values against them.

It deliberately does not pull the heavy ``linkml`` runtime — it reads the same
LinkML schema with PyYAML and enforces the enum ranges + the survival-status
pattern. A curator who wants full ``linkml-validate`` can point it at the same
YAML; the permissible values live in one place.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "data" / "linkml" / "cbioportal_clinical.yaml"


@lru_cache(maxsize=1)
def _schema() -> dict[str, Any]:
    with open(_SCHEMA_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@lru_cache(maxsize=1)
def _enum_for_slot() -> dict[str, set[str]]:
    """Map each slot name (e.g. ``SEX``) to its permissible value set."""
    schema = _schema()
    enums = schema.get("enums", {})
    out: dict[str, set[str]] = {}
    for slot_name, slot in (schema.get("slots") or {}).items():
        enum_name = (slot or {}).get("range")
        if enum_name and enum_name in enums:
            pvs = enums[enum_name].get("permissible_values") or {}
            out[slot_name] = set(pvs.keys())
    return out


def _survival_settings() -> tuple[str, re.Pattern[str], set[str]]:
    settings = _schema().get("settings", {})
    suffix = settings.get("survival_status_suffix", "_STATUS")
    pattern = re.compile(settings.get("survival_status_pattern", "^[01]:"))
    exclude = set(settings.get("survival_status_exclude", []))
    return suffix, pattern, exclude


def validate_clinical_columns(columns: dict[str, list[Any]]) -> list[dict[str, Any]]:
    """Validate harmonized columns against the LinkML vocabularies.

    ``columns`` maps a cBioPortal attribute id (UPPER_CASE, e.g. ``SEX``) to its
    list of cell values. Returns a list of violation dicts, each with the
    offending column, value, the rule, the allowed values, and a ``count`` of
    how many rows hold that value. Violations are de-duplicated per
    ``(column, value)`` so a bad value repeated across 500 rows is one entry,
    not 500. Empty when the table passes the gate.
    """
    enum_for_slot = _enum_for_slot()
    suffix, surv_pattern, surv_exclude = _survival_settings()
    # (column, value) -> violation dict (with running count)
    seen: dict[tuple[str, str], dict[str, Any]] = {}

    for column, values in columns.items():
        allowed = enum_for_slot.get(column)
        is_survival = column.endswith(suffix) and column not in surv_exclude and allowed is None

        for value in values:
            if value is None:
                continue
            text = str(value).strip()
            if text == "":
                continue

            violation: dict[str, Any] | None = None
            if allowed is not None and text not in allowed:
                violation = {
                    "column": column,
                    "value": text,
                    "rule": "enum",
                    "allowed": sorted(allowed),
                }
            elif is_survival and not surv_pattern.match(text):
                violation = {
                    "column": column,
                    "value": text,
                    "rule": "survival_status_prefix",
                    "allowed": ["0:<status>", "1:<status>"],
                }

            if violation is None:
                continue
            key = (column, text)
            if key in seen:
                seen[key]["count"] += 1
            else:
                violation["count"] = 1
                seen[key] = violation

    return list(seen.values())
