"""Schema-version diff (G6, layer A — schema-vs-schema).

When an admin uploads a new ``curated_fields`` CSV, this shows what changed in
the *target dictionary itself*: which curated fields were added or removed, and
which fields had their allowed-value vocabulary change. A curated CSV is a wide
table — each **column is a curated field**, and a field's distinct non-empty
values are its allowed vocabulary.

This is the cheap, always-useful half of G6 that ships with versioning. The
study-impact re-score (layer B) is gated on curator demand and lives elsewhere.

Pure functions over already-parsed field→values maps, so they are trivially
testable; the router supplies the CSV parsing.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

# Cells that mean "no value" in the curated CSVs.
_MISSING = {"", "na", "nan", "none", "null"}


def field_value_map(df: pd.DataFrame) -> dict[str, set[str]]:
    """Map each curated field (column) to its set of allowed (distinct) values."""
    out: dict[str, set[str]] = {}
    for col in df.columns:
        values: set[str] = set()
        for v in df[col].tolist():
            if v is None:
                continue
            text = str(v).strip()
            if text.lower() in _MISSING:
                continue
            values.add(text)
        out[str(col)] = values
    return out


def diff_field_maps(
    old: dict[str, set[str]], new: dict[str, set[str]]
) -> dict[str, Any]:
    """Diff two field→values maps into added / removed / changed fields.

    ``changed`` lists fields present in both whose allowed-value set differs,
    with the added/removed values for each.
    """
    old_fields = set(old)
    new_fields = set(new)

    added = sorted(new_fields - old_fields)
    removed = sorted(old_fields - new_fields)

    changed: list[dict[str, Any]] = []
    for field in sorted(old_fields & new_fields):
        added_vals = sorted(new[field] - old[field])
        removed_vals = sorted(old[field] - new[field])
        if added_vals or removed_vals:
            changed.append(
                {
                    "field": field,
                    "added_values": added_vals,
                    "removed_values": removed_vals,
                }
            )

    return {
        "added_fields": [
            {"field": f, "value_count": len(new[f])} for f in added
        ],
        "removed_fields": [
            {"field": f, "value_count": len(old[f])} for f in removed
        ],
        "changed_fields": changed,
        "summary": {
            "added": len(added),
            "removed": len(removed),
            "changed": len(changed),
            "unchanged": len(old_fields & new_fields) - len(changed),
        },
    }


def diff_csv_files(old_path: str, new_path: str) -> dict[str, Any]:
    """Parse two curated-fields CSVs and diff their schemas (layer A)."""
    old_df = pd.read_csv(old_path, dtype=str, keep_default_na=False)
    new_df = pd.read_csv(new_path, dtype=str, keep_default_na=False)
    return diff_field_maps(field_value_map(old_df), field_value_map(new_df))
