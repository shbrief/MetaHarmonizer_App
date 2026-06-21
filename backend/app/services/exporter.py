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

# Patient-level clinical attributes (cBioPortal convention). When a study is
# exported as a folder, these go to data_clinical_patient.txt and everything
# else (that isn't an ID) goes to data_clinical_sample.txt. Survival columns
# (``*_STATUS`` / ``*_MONTHS``) are always patient-level.
PATIENT_LEVEL_ATTRS: set[str] = {
    "SEX",
    "GENDER",
    "AGE",
    "AGE_AT_DIAGNOSIS",
    "RACE",
    "ETHNICITY",
    "ANCESTRY",
    "VITAL_STATUS",
    "OS_STATUS",
    "OS_MONTHS",
    "DFS_STATUS",
    "DFS_MONTHS",
    "PFS_STATUS",
    "PFS_MONTHS",
    "DSS_STATUS",
    "DSS_MONTHS",
}


def _is_patient_level(target_id: str) -> bool:
    """True if a cBioPortal attribute belongs in the patient clinical file."""
    if target_id in PATIENT_LEVEL_ATTRS:
        return True
    # Survival pairs use a free PREFIX (e.g. ``OS_STATUS`` / ``RFS_MONTHS``).
    return target_id.endswith("_STATUS") or target_id.endswith("_MONTHS")


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
    text = "" if pd.isna(value) else str(value)
    return _ID_INVALID.sub("_", text)


def _normalize_survival(value: Any) -> str:
    """Prefix a survival-status value with 0:/1: if it isn't already."""
    text = "" if pd.isna(value) else str(value).strip()
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
    mappings, drop unmapped columns, rewrite accepted cell values to their
    confirmed ontology terms (U5), and return CSV text.
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

    # Value-level rewrite (U5): for each output column, replace accepted raw
    # values with their confirmed ontology term so the table carries resolved
    # cell values — not just renamed columns. Unmatched values pass through.
    value_rewrites = await _build_value_rewrites(db, study_id)
    for col, lookup in value_rewrites.items():
        if col in out_df.columns:
            out_df[col] = out_df[col].map(
                lambda v, _m=lookup: _m.get(str(v), v) if pd.notna(v) else v
            )

    return out_df.to_csv(index=False)


async def _build_value_rewrites(
    db: AsyncSession, study_id: str
) -> dict[str, dict[str, str]]:
    """Map each harmonized field to its accepted ``raw_value -> term`` rewrites."""
    rewrites: dict[str, dict[str, str]] = {}
    for o in await ontology_repo.get_ontology_mappings(db, study_id):
        if o["status"] != "accepted":
            continue
        term = o.get("curator_term") or o.get("ontology_term")
        if not term:
            continue
        rewrites.setdefault(o["field_name"], {})[str(o["raw_value"])] = str(term)
    return rewrites


# ---------------------------------------------------------------------------
# cBioPortal Format
# ---------------------------------------------------------------------------

_HIGH_PRIORITY_ATTRS: set[str] = {
    "PATIENT_ID", "SAMPLE_ID", "CANCER_TYPE", "CANCER_TYPE_DETAILED",
    "GENDER", "SEX", "AGE", "OS_STATUS", "OS_MONTHS", "TUMOR_SITE",
}


def _infer_dtype(series: pd.Series) -> str:
    """Infer a cBioPortal data type (NUMBER / BOOLEAN / STRING) for a column."""
    non_null = series.dropna()
    try:
        pd.to_numeric(non_null)
        return "NUMBER"
    except (ValueError, TypeError):
        pass
    try:
        unique_vals = set(non_null.astype(str).str.lower().unique())
    except (AttributeError, TypeError):
        unique_vals = set()
    if unique_vals and unique_vals <= {"true", "false", "yes", "no", "0", "1"}:
        return "BOOLEAN"
    return "STRING"


def _clinical_column_specs(
    mappings: list[dict[str, Any]], raw_df: pd.DataFrame
) -> list[dict[str, Any]]:
    """Build cBioPortal column specs from accepted/pending mappings.

    Excludes PATIENT_ID / SAMPLE_ID (injected per-file by the caller) and
    banned auto-populated attributes; dedupes by target column.
    """
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
        if target_id in BANNED_ATTRS or target_id in {"PATIENT_ID", "SAMPLE_ID"}:
            continue
        if target_id in seen_targets:
            continue
        seen_targets.add(target_id)
        cols.append(
            {
                "raw": raw,
                "target": target_id,
                "display": target.replace("_", " ").title(),
                "description": target.replace("_", " ").capitalize(),
                "dtype": _infer_dtype(raw_df[raw]),
                "priority": 10 if target_id in _HIGH_PRIORITY_ATTRS else 1,
            }
        )
    return cols


def _id_spec(
    target_id: str, raw_src: str, display: str, description: str
) -> dict[str, Any]:
    return {
        "raw": raw_src,
        "target": target_id,
        "display": display,
        "description": description,
        "dtype": "STRING",
        "priority": 10,
    }


def _id_raw_source(
    mappings: list[dict[str, Any]],
    raw_df: pd.DataFrame,
    target_id: str,
    fallback_candidates: list[str],
) -> str:
    """Find the raw column feeding an ID attribute: a matched mapping or a heuristic."""
    for m in mappings:
        target = m.get("curator_field") or m.get("matched_field")
        if not target:
            continue
        if target.upper().replace(" ", "_") == target_id and m.get("raw_column") in raw_df.columns:
            return m["raw_column"]
    return _find_id_column(raw_df, fallback_candidates)


def _write_clinical_tsv(cols: list[dict[str, Any]], raw_df: pd.DataFrame) -> str:
    """Write a cBioPortal 5-row-header clinical TSV for the given column specs."""
    targets = {c["target"] for c in cols}
    survival_status_with_months = {
        c["target"]
        for c in cols
        if c["target"].endswith("_STATUS") and f"{c['target'][:-7]}_MONTHS" in targets
    }
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter="\t", lineterminator="\n")

    def _header_row(values: list[str]) -> None:
        # Per spec, only the FIRST field of each metadata row carries the '#'.
        row = list(values)
        if row:
            row[0] = "#" + row[0]
        writer.writerow(row)

    _header_row([c["display"] for c in cols])
    _header_row([c["description"] for c in cols])
    _header_row([c["dtype"] for c in cols])
    _header_row([str(c["priority"]) for c in cols])
    writer.writerow([c["target"] for c in cols])  # attribute IDs (no '#')

    for _, row in raw_df.iterrows():
        out_row: list[str] = []
        for c in cols:
            raw_val = row.get(c["raw"], "")
            target_id = c["target"]
            if target_id in ("PATIENT_ID", "SAMPLE_ID"):
                out_row.append(_sanitize_id(raw_val))
            elif target_id in survival_status_with_months:
                out_row.append(_normalize_survival(raw_val))
            else:
                # pandas NaN is not None; guard with isna so a missing value is
                # an empty cell, not the literal string "nan".
                out_row.append("" if pd.isna(raw_val) else str(raw_val))
        writer.writerow(out_row)

    return buf.getvalue()


async def export_cbioportal(
    db: AsyncSession, study_id: str, raw_df: pd.DataFrame
) -> str:
    """
    Produce a single cBioPortal-format clinical data file (all attributes in
    one sample-level file), per the official spec:
    https://docs.cbioportal.org/file-formats/#clinical-data

    Header rows: display names, descriptions, data types, priority, then the
    UPPER_CASE attribute IDs. PATIENT_ID and SAMPLE_ID are always present.
    """
    mappings = await mappings_repo.get_mappings(db, study_id)
    specs = _clinical_column_specs(mappings, raw_df)

    patient_src = _id_raw_source(
        mappings, raw_df, "PATIENT_ID",
        ["subject_id", "patient_id", "participant_id", "case_id"],
    )
    sample_src = _id_raw_source(
        mappings, raw_df, "SAMPLE_ID",
        ["sample_id", "run_id", "sampleid", "accession"],
    )

    if not specs and raw_df.columns.empty:
        return "# No mappings available for export\n"

    cols = [
        _id_spec("PATIENT_ID", patient_src, "Patient Identifier", "Unique patient identifier"),
        _id_spec("SAMPLE_ID", sample_src, "Sample Identifier", "Unique sample identifier"),
        *specs,
    ]
    return _write_clinical_tsv(cols, raw_df)


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


def _meta_clinical(cancer_study_identifier: str, datatype: str, data_filename: str) -> str:
    return (
        f"cancer_study_identifier: {cancer_study_identifier}\n"
        f"genetic_alteration_type: CLINICAL\n"
        f"datatype: {datatype}\n"
        f"data_filename: {data_filename}\n"
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
        meta_clinical_patient.txt
        data_clinical_patient.txt
        meta_clinical_sample.txt
        data_clinical_sample.txt

    The clinical attributes are split per the curation checklist ("the clinical
    file should be split to patient and sample level attribute files"):
    patient-level attributes (sex, survival, age, ancestry, ...) go to the
    patient file with one row per unique patient; everything else goes to the
    sample file with one row per sample. PATIENT_ID appears in both so samples
    link to patients.
    """
    study = await studies_repo.get_study(db, study_id) or {}
    identifier = cancer_study_identifier or _sanitize_id(
        study.get("name") or study_id
    ).lower()
    name = study.get("name") or study_id
    description = study.get("description") or f"Harmonized clinical data for {name}."

    mappings = await mappings_repo.get_mappings(db, study_id)
    specs = _clinical_column_specs(mappings, raw_df)

    patient_src = _id_raw_source(
        mappings, raw_df, "PATIENT_ID",
        ["subject_id", "patient_id", "participant_id", "case_id"],
    )
    sample_src = _id_raw_source(
        mappings, raw_df, "SAMPLE_ID",
        ["sample_id", "run_id", "sampleid", "accession"],
    )

    patient_id_spec = _id_spec(
        "PATIENT_ID", patient_src, "Patient Identifier", "Unique patient identifier"
    )
    sample_id_spec = _id_spec(
        "SAMPLE_ID", sample_src, "Sample Identifier", "Unique sample identifier"
    )

    patient_attr_specs = [s for s in specs if _is_patient_level(s["target"])]
    sample_attr_specs = [s for s in specs if not _is_patient_level(s["target"])]

    # Patient file: one row per unique patient (cBioPortal requires unique
    # PATIENT_ID rows). Sample file: one row per sample, PATIENT_ID links back.
    patient_cols = [patient_id_spec, *patient_attr_specs]
    sample_cols = [patient_id_spec, sample_id_spec, *sample_attr_specs]

    patient_df = raw_df.drop_duplicates(subset=[patient_src]) if patient_src in raw_df.columns else raw_df

    data_clinical_patient = _write_clinical_tsv(patient_cols, patient_df)
    data_clinical_sample = _write_clinical_tsv(sample_cols, raw_df)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("meta_study.txt", _meta_study(identifier, name, description))
        zf.writestr(
            "meta_clinical_patient.txt",
            _meta_clinical(identifier, "PATIENT_ATTRIBUTES", "data_clinical_patient.txt"),
        )
        zf.writestr("data_clinical_patient.txt", data_clinical_patient)
        zf.writestr(
            "meta_clinical_sample.txt",
            _meta_clinical(identifier, "SAMPLE_ATTRIBUTES", "data_clinical_sample.txt"),
        )
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
