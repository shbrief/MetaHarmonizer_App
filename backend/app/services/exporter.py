"""
MetaHarmonizer Dashboard — Exporter Service

Generates harmonized output files in multiple formats:
- CSV (harmonized metadata)
- cBioPortal clinical data format
- JSON mapping report (audit trail)
"""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from typing import Any

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import audit as audit_repo
from app.repositories import mappings as mappings_repo
from app.repositories import ontology as ontology_repo
from app.repositories import studies as studies_repo


# cBioPortal auto-populates these; they must not appear in a clinical data file.
BANNED_ATTRS: set[str] = {"MUTATION_COUNT", "FRACTION_GENOME_ALTERED"}

# cBioPortal IDs allow only letters, numbers, points, underscores and hyphens.
_ID_INVALID = re.compile(r"[^A-Za-z0-9._-]")

# Survival *_STATUS values must be prefixed 0: (no event) or 1: (event).
_SURVIVAL_PREFIX: dict[str, str] = {
    "LIVING": "0:LIVING",
    "ALIVE": "0:LIVING",
    "DECEASED": "1:DECEASED",
    "DEAD": "1:DECEASED",
    "DISEASEFREE": "0:DiseaseFree",
    "DISEASE FREE": "0:DiseaseFree",
    "RECURRED": "1:Recurred/Progressed",
    "PROGRESSED": "1:Recurred/Progressed",
    "RECURRED/PROGRESSED": "1:Recurred/Progressed",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sanitize_id(value: Any) -> str:
    """Coerce a value into a cBioPortal-legal ID (letters, numbers, . _ -)."""
    text = "" if value is None else str(value)
    return _ID_INVALID.sub("_", text)


def _normalize_survival(value: Any) -> str:
    """Prefix a survival-status value with 0:/1: if it isn't already."""
    text = "" if value is None else str(value).strip()
    if not text or text[:2] in ("0:", "1:"):
        return text
    return _SURVIVAL_PREFIX.get(text.upper(), text)

def _find_id_column(df: pd.DataFrame, candidates: list[str]) -> str:
    """
    Find the best existing column in `df` that matches one of the candidate
    names (case-insensitive).  If none found, return the first column that
    contains mostly unique non-null values (heuristic for an ID column).
    As a last resort, synthesize a column name — the exporter will fill it
    with row indices.
    """
    lower_cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_cols:
            return lower_cols[cand.lower()]

    # Heuristic: find a column with high cardinality (likely an ID)
    for c in df.columns:
        non_null = df[c].dropna()
        if len(non_null) > 0 and non_null.nunique() / len(non_null) > 0.9:
            return c

    # Fallback: use first column
    return df.columns[0] if len(df.columns) > 0 else "_GENERATED_ID"


# ---------------------------------------------------------------------------
# Harmonized CSV
# ---------------------------------------------------------------------------

async def export_harmonized_csv(
    db: AsyncSession, study_id: str, raw_df: pd.DataFrame
) -> str:
    """
    Produce a harmonized CSV: rename raw columns to their accepted/curated
    mappings, drop unmapped columns, and return CSV text.
    """
    mappings = await mappings_repo.get_mappings(db, study_id)

    rename_map: dict[str, str] = {}
    keep_cols: list[str] = []

    for m in mappings:
        raw = m["raw_column"]
        if m["status"] == "accepted":
            target = m.get("curator_field") or m.get("matched_field")
            if target and raw in raw_df.columns:
                rename_map[raw] = target
                keep_cols.append(raw)
        elif m["status"] == "pending" and m["matched_field"]:
            # Include pending but mapped columns with original matched field
            rename_map[raw] = m["matched_field"]
            keep_cols.append(raw)

    if not keep_cols:
        # Fallback: include all mapped columns
        for m in mappings:
            raw = m["raw_column"]
            if m["matched_field"] and raw in raw_df.columns:
                rename_map[raw] = m["matched_field"]
                keep_cols.append(raw)

    # Deduplicate keep_cols preserving order
    seen: set[str] = set()
    unique_keep: list[str] = []
    for c in keep_cols:
        if c not in seen:
            seen.add(c)
            unique_keep.append(c)

    out_df = raw_df[unique_keep].rename(columns=rename_map)
    return out_df.to_csv(index=False)


# ---------------------------------------------------------------------------
# cBioPortal Format
# ---------------------------------------------------------------------------

async def export_cbioportal(
    db: AsyncSession, study_id: str, raw_df: pd.DataFrame
) -> str:
    """
    Produce a cBioPortal-format clinical sample data file.

    Follows the official cBioPortal file format specification:
    https://docs.cbioportal.org/file-formats/#clinical-data

    cBioPortal clinical data files require:
      Row 1: #Display names
      Row 2: #Descriptions (longer description of each attribute)
      Row 3: #Data types (STRING, NUMBER, or BOOLEAN)
      Row 4: #Priority (numeric; higher = more prominent in UI)
      Row 5: Column attribute IDs (UPPER_CASE, no # prefix)
      Row 6+: Data rows (tab-separated)

    Required columns for sample-level data:
      - PATIENT_ID: unique patient identifier
      - SAMPLE_ID: unique sample identifier
    """
    mappings = await mappings_repo.get_mappings(db, study_id)

    # Build column list from accepted / mapped
    cols: list[dict[str, Any]] = []
    seen_targets: set[str] = set()

    for m in mappings:
        target = m.get("curator_field") or m.get("matched_field")
        if not target:
            continue
        if m["status"] not in ("accepted", "pending"):
            continue
        raw = m["raw_column"]
        if raw not in raw_df.columns:
            continue

        target_id = target.upper().replace(" ", "_")

        # Skip banned (auto-populated) attributes
        if target_id in BANNED_ATTRS:
            continue

        # Skip duplicate target columns
        if target_id in seen_targets:
            continue
        seen_targets.add(target_id)

        # Determine data type
        dtype = "STRING"
        try:
            pd.to_numeric(raw_df[raw].dropna())
            dtype = "NUMBER"
        except (ValueError, TypeError):
            # Check for boolean-like columns
            unique_vals = set(raw_df[raw].dropna().str.lower().unique())
            if unique_vals and unique_vals <= {"true", "false", "yes", "no", "0", "1"}:
                dtype = "BOOLEAN"

        # Priority: well-known cBioPortal attributes get higher priority
        priority = 1
        high_priority_attrs = {
            "PATIENT_ID", "SAMPLE_ID", "CANCER_TYPE", "CANCER_TYPE_DETAILED",
            "GENDER", "SEX", "AGE", "OS_STATUS", "OS_MONTHS", "TUMOR_SITE",
        }
        if target_id in high_priority_attrs:
            priority = 10

        cols.append(
            {
                "raw": raw,
                "target": target_id,
                "display": target.replace("_", " ").title(),
                "description": target.replace("_", " ").capitalize(),
                "dtype": dtype,
                "priority": priority,
            }
        )

    if not cols:
        return "# No mappings available for export\n"

    # ---------------------------------------------------------------
    # Ensure required columns PATIENT_ID and SAMPLE_ID are present.
    # cBioPortal sample clinical data REQUIRES both.
    # If the schema mapper matched subject_id or sample_id, they'll
    # already be in `cols`.  Otherwise, we synthesize them from
    # available data.
    # ---------------------------------------------------------------
    target_ids = {c["target"] for c in cols}

    if "PATIENT_ID" not in target_ids:
        # Try to find a suitable source column in the raw data
        patient_src = _find_id_column(raw_df, ["subject_id", "patient_id", "participant_id", "case_id"])
        cols.insert(0, {
            "raw": patient_src,
            "target": "PATIENT_ID",
            "display": "Patient Identifier",
            "description": "Unique patient identifier",
            "dtype": "STRING",
            "priority": 10,
        })
    else:
        # Move PATIENT_ID to front
        idx = next(i for i, c in enumerate(cols) if c["target"] == "PATIENT_ID")
        cols.insert(0, cols.pop(idx))

    if "SAMPLE_ID" not in target_ids:
        # Try to find a suitable source column in the raw data
        sample_src = _find_id_column(raw_df, ["sample_id", "run_id", "sampleid", "accession"])
        pos = 1  # right after PATIENT_ID
        cols.insert(pos, {
            "raw": sample_src,
            "target": "SAMPLE_ID",
            "display": "Sample Identifier",
            "description": "Unique sample identifier",
            "dtype": "STRING",
            "priority": 10,
        })
    else:
        # Move SAMPLE_ID to position 1 (right after PATIENT_ID)
        idx = next(i for i, c in enumerate(cols) if c["target"] == "SAMPLE_ID")
        if idx != 1:
            cols.insert(1, cols.pop(idx))

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter="\t", lineterminator="\n")

    def _header_row(values: list[str]) -> None:
        # Per spec, only the FIRST field of each metadata row carries the '#'.
        row = list(values)
        if row:
            row[0] = "#" + row[0]
        writer.writerow(row)

    # Row 1: Display names
    _header_row([c["display"] for c in cols])
    # Row 2: Descriptions (distinct from display names per spec)
    _header_row([c["description"] for c in cols])
    # Row 3: Data types
    _header_row([c["dtype"] for c in cols])
    # Row 4: Priority
    _header_row([str(c["priority"]) for c in cols])

    # Row 5: Column attribute IDs (no # prefix, UPPER_CASE)
    writer.writerow([c["target"] for c in cols])

    # Row 6+: Data rows, with per-column value normalization
    for _, row in raw_df.iterrows():
        out_row: list[str] = []
        for c in cols:
            raw_val = row.get(c["raw"], "")
            target_id = c["target"]
            if target_id in ("PATIENT_ID", "SAMPLE_ID"):
                out_row.append(_sanitize_id(raw_val))
            elif target_id.endswith("_STATUS") and f"{target_id[:-7]}_MONTHS" in seen_targets:
                out_row.append(_normalize_survival(raw_val))
            else:
                out_row.append("" if raw_val is None else str(raw_val))
        writer.writerow(out_row)

    return buf.getvalue()


# ---------------------------------------------------------------------------
# cBioPortal study folder (validateData.py-ready)
# ---------------------------------------------------------------------------

def _meta_study(cancer_study_identifier: str, name: str, description: str) -> str:
    return (
        f"type_of_cancer: mixed\n"
        f"cancer_study_identifier: {cancer_study_identifier}\n"
        f"name: {name}\n"
        f"description: {description}\n"
        f"add_global_case_list: true\n"
    )


def _meta_clinical_sample(cancer_study_identifier: str) -> str:
    return (
        f"cancer_study_identifier: {cancer_study_identifier}\n"
        f"genetic_alteration_type: CLINICAL\n"
        f"datatype: SAMPLE_ATTRIBUTES\n"
        f"data_filename: data_clinical_sample.txt\n"
    )


async def export_cbioportal_study(
    db: AsyncSession,
    study_id: str,
    raw_df: pd.DataFrame,
    cancer_study_identifier: str | None = None,
) -> bytes:
    """
    Produce a cBioPortal study folder as a zip, ready for ``validateData.py``:

        meta_study.txt
        meta_clinical_sample.txt
        data_clinical_sample.txt

    ``validateData.py`` validates a study directory with meta files, not a lone
    TSV, so this is the artifact a curator actually runs the validator against.
    """
    study = await studies_repo.get_study(db, study_id) or {}
    identifier = cancer_study_identifier or _sanitize_id(
        study.get("name") or study_id
    ).lower()
    name = study.get("name") or study_id
    description = study.get("description") or f"Harmonized clinical data for {name}."

    data_clinical_sample = await export_cbioportal(db, study_id, raw_df)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("meta_study.txt", _meta_study(identifier, name, description))
        zf.writestr("meta_clinical_sample.txt", _meta_clinical_sample(identifier))
        zf.writestr("data_clinical_sample.txt", data_clinical_sample)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# JSON Mapping Report
# ---------------------------------------------------------------------------

async def export_mapping_report(db: AsyncSession, study_id: str) -> str:
    """
    Produce a JSON audit report of all mapping decisions.
    """
    study = await studies_repo.get_study(db, study_id)
    mappings = await mappings_repo.get_mappings(db, study_id)
    onto = await ontology_repo.get_ontology_mappings(db, study_id)
    audit = await audit_repo.get_audit_log(db, study_id)

    report = {
        "study": study,
        "schema_mappings": mappings,
        "ontology_mappings": onto,
        "audit_log": audit,
        "summary": {
            "total_columns": len(mappings),
            "accepted": sum(1 for m in mappings if m["status"] == "accepted"),
            "rejected": sum(1 for m in mappings if m["status"] == "rejected"),
            "pending": sum(1 for m in mappings if m["status"] == "pending"),
        },
    }
    return json.dumps(report, indent=2, default=str)
