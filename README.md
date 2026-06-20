# 🔬 MetaHarmonizer

**Automated biomedical metadata harmonization platform for cBioPortal-compatible clinical datasets.**

MetaHarmonizer bridges the gap between raw, inconsistent clinical metadata and standardized, ontology-annotated schemas. It combines a multi-stage ML pipeline with an interactive curator review dashboard, enabling researchers to harmonize metadata at scale while maintaining expert oversight.

> **GSoC 2026 project** — [Automated Clinical Metadata Harmonization Dashboard](https://github.com/cBioPortal/GSoC/issues/136)

---

## The Problem

cBioPortal hosts 400+ cancer genomics studies with clinical metadata from diverse sources. Cross-study metadata heterogeneity severely limits analysis:

| Issue                     | Examples                                                             |
| ------------------------- | -------------------------------------------------------------------- |
| **Attribute naming**      | `AGE`, `AGE_AT_DIAGNOSIS`, `DIAGNOSIS_AGE` — all mean the same thing |
| **Value encoding**        | Sex recorded as `male`, `M`, `1`, `Male`, `MALE`                     |
| **Treatment synonyms**    | 24+ variants: `RADIO_THERAPY`, `Rad`, `XRT`, `Radiation`, `RT`       |
| **Staging inconsistency** | `TUMOR_STAGE_2009`, `AJCC_STAGE`, `STAGE`, `PATHOLOGIC_STAGE`        |

Manual harmonization does not scale. MetaHarmonizer automates this using a **4-stage cascade pipeline** backed by dictionary matching, ontology resolution, semantic embeddings, and optional LLM inference — then presents results in a curator-friendly dashboard for review and correction.

---

## Dashboard Pages

### 1. Upload

Upload a CSV or TSV file containing raw clinical metadata. The pipeline automatically processes all columns through the 4-stage cascade and returns results in seconds.

![Upload Page](pics/upload_page.png)

---

### 2. Schema Mapping Review

The core curator workspace. Each column mapping displays the suggested standardized field name, confidence score (color-coded), the pipeline stage that produced the match, and up to 4 alternative candidates. Curators can accept, reject, or manually edit any mapping — individually or in batch.

![Schema Mapping Review](pics/schema_mapping.png)

---

### 3. Ontology Value Mapping

View how raw cell values within mapped columns are resolved to standard ontology terms from NCIT, UBERON, and OHMI. Curators can search and browse terms with fuzzy matching to verify or override automated assignments.

![Ontology Mapping](pics/ontlogy_mapping.png)

---

### 4. Quality Dashboard

Monitor harmonization quality at a glance — KPI cards for overall coverage and confidence, a confidence score histogram showing score distribution, stage breakdown charts revealing which pipeline stages contribute most matches, and review progress tracking.

![Quality Dashboard](pics/quality_dashboard.png)

---

### 5. Export

Download results in three formats: harmonized CSV with standardized column names, cBioPortal-compatible TSV with the proper 4-line header format for direct ingestion, and a JSON audit report capturing every mapping decision and curator action.

![Export](pics/export.png)

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│  Upload → Review → Ontology → Quality → Export       │
│  (TypeScript, Tailwind CSS, Recharts)                │
└──────────────────────┬──────────────────────────────┘
                       │ REST API (JSON)
┌──────────────────────▼──────────────────────────────┐
│                 FastAPI Backend                       │
│  Routers: auth, harmonize, mappings, ontology,       │
│           quality, export, admin, audit, tokens, ws  │
│  Services: harmonizer (engine wrapper), analytics,   │
│            exporter                                  │
│  Auth: JWT access/refresh, RBAC, email verification  │
│  Data: PostgreSQL (SQLAlchemy async) · Redis (jobs)  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│         engine_adapter (EngineProtocol)              │
│  Selectable impl via ENGINE_IMPL env var:            │
│   - metaharmonizer  (default, pip-installed upstream)│
│   - mock            (deterministic, used in tests)   │
│  Single seam: only this dir may import upstream      │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│        upstream metaharmonizer package                │
│  SchemaMapEngine (4-stage cascade)                   │
│  SentenceTransformer (all-MiniLM-L6-v2) embeddings   │
│  NCI EVS API integration, dictionary + fuzzy match   │
└─────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer         | Technology                                                       |
| ------------- | ---------------------------------------------------------------- |
| **Frontend**  | React 18, TypeScript, Tailwind CSS, TanStack Query, Recharts     |
| **Backend**   | FastAPI, Pydantic v2, SQLAlchemy (async), Alembic, Uvicorn       |
| **Data**      | PostgreSQL 16 · Redis 7 (job queue / arq, rate limiting, WS)     |
| **Auth**      | JWT access/refresh, Argon2id, RBAC, email verification (Resend)  |
| **ML Engine** | SentenceTransformer (`all-MiniLM-L6-v2`), RapidFuzz, NCI EVS API |

---

## Pipeline Stages

Provided by the upstream `metaharmonizer` package, wrapped behind `EngineProtocol`.

| Stage       | Method                              | Description                                                                                          |
| ----------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Stage 1** | Exact dictionary match              | Direct case-insensitive match against the curated standard-field list.                               |
| **Stage 2** | Alias match                         | Looks up known synonyms in `curated_fields_source_latest_with_flags.csv`.                            |
| **Stage 3** | Semantic match                      | SentenceTransformer (`all-MiniLM-L6-v2`) cosine similarity over field names and value samples.       |
| **Stage 4** | LLM query rewrite + FAISS re-search | Optional Gemini call to rewrite ambiguous queries, then re-rank. Off unless `GOOGLE_API_KEY` is set. |

Columns flow through stages sequentially. A high-confidence match at any stage skips later stages. Unmapped columns surface in the curator review for manual override or on-demand LLM rematch.

---

## Quick Start

The stack is **FastAPI + Postgres 16 + Redis 7** (backend) and **React + Vite** (frontend), with JWT auth.

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 16 and Redis 7 running locally
  _(Windows without admin/Docker? see the **portable services** tip below — it sets both up for you.)_

### 1. Clone + configure

```bash
git clone https://github.com/AhmedOsamaAli/metaHarmonizer.git
cd metaHarmonizer
cp .env.example .env
```

The defaults in `.env.example` are wired for local dev, so **no edits are
required** if you use the portable services in step 2. The values you'd only
change for your own setup:

```bash
DATABASE_URL=...     # already points at the portable Postgres (:5433)
REDIS_URL=...        # already points at the portable Redis (:6380)
ALLOWED_EMAIL_DOMAINS=example.com   # who may register; empty = signup closed
```

> Register with any `@example.com` email. The **first** account becomes the
> **admin**; everyone after is a curator (an admin can promote them later).

### 2. Start Postgres + Redis

Windows, no install or admin rights needed:

```powershell
scripts/dev_services.ps1 start    # portable Postgres (:5433) + Redis (:6380)
```

Already run your own Postgres 16 / Redis 7? Point `DATABASE_URL` / `REDIS_URL`
in `.env` at them (the standard `:5432` / `:6379` DSNs are noted in the file).

### 3. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate                # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

alembic upgrade head                  # create the DB schema (one-off after schema changes)
uvicorn app.main:app --reload --port 8000
```

The upstream `metaharmonizer` engine installs from a pre-built wheel under
[backend/vendor/](backend/vendor/README.md), so it works on Windows, Linux and
macOS with no special steps. First boot warms an ML model (~1–2 min); set
`ENGINE_IMPL=mock` in `.env` for instant, ML-free startup during development.

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server proxies `/api` to `http://localhost:8000`, so no frontend config
is needed.

### First run

1. Open the frontend → **Create an account** (email must match `ALLOWED_EMAIL_DOMAINS`).
2. The **first** user becomes **admin**; later users are curators.
3. Sign in and upload a study.

| Service            | URL                        |
| ------------------ | -------------------------- |
| Frontend           | http://localhost:5173      |
| Backend API        | http://localhost:8000      |
| API Docs (Swagger) | http://localhost:8000/docs |
| Health / Readiness | http://localhost:8000/healthz · http://localhost:8000/readyz |

---

## Environment Variables

`.env.example` is the canonical, commented catalogue — copy it to `.env`. The
most important variables:

| Variable                | Required | Default          | Description                                                                 |
| ----------------------- | :------: | ---------------- | --------------------------------------------------------------------------- |
| `JWT_SECRET`            | ✅       | —                | Signs access/refresh tokens. **Boot fails if < 32 bytes.**                  |
| `DATABASE_URL`          | ✅       | local Postgres   | `postgresql+asyncpg://…` DSN.                                               |
| `REDIS_URL`             | ✅       | local Redis      | Job queue + rate-limit + WS ticket store.                                   |
| `ALLOWED_EMAIL_DOMAINS` | ✅       | _(empty)_        | Comma-separated signup allow-list. Empty → registration closed.            |
| `ENGINE_IMPL`           |          | `metaharmonizer` | `mock` switches to the deterministic, ML-free engine (tests/fast dev).      |
| `JOB_MODE`              |          | `inline`         | `inline` (just uvicorn) or `queue` (arq workers via Redis).                 |
| `GEMINI_API_KEY`        |          | —                | Enables the engine's optional Stage-4 LLM rematch.                          |
| `CORS_ORIGINS`          |          | localhost        | Allowed web origins (no wildcards in prod).                                 |

Migrations are managed by **Alembic** and are **not** auto-applied — run
`alembic upgrade head` after pulling changes that touch the schema.


---

## API Reference

**Schema Mapping**

| Endpoint                                  | Method | Description                                               |
| ----------------------------------------- | ------ | --------------------------------------------------------- |
| `/api/v1/harmonize`                       | POST   | Upload file and run harmonization pipeline                |
| `/api/v1/harmonize/{job_id}`              | GET    | Poll job status and results                               |
| `/api/v1/studies`                         | GET    | List all studies                                          |
| `/api/v1/mappings/{study_id}`             | GET    | Get all column mappings for a study                       |
| `/api/v1/mappings/{study_id}/suggestions` | GET    | Low-confidence/unmapped columns with alternatives         |
| `/api/v1/mappings/{id}/accept`            | POST   | Accept a mapping                                          |
| `/api/v1/mappings/{id}/reject`            | POST   | Reject a mapping                                          |
| `/api/v1/mappings/{id}/edit`              | POST   | Manually override a mapping                               |
| `/api/v1/mappings/{id}/llm`               | POST   | Trigger on-demand LLM rematch (requires `GEMINI_API_KEY`) |
| `/api/v1/mappings/batch`                  | POST   | Batch accept/reject mappings                              |

**Ontology Value Mapping**

| Endpoint                                | Method | Description                                |
| --------------------------------------- | ------ | ------------------------------------------ |
| `/api/v1/ontology/search`               | GET    | Fuzzy search across NCIT/UBERON/OHMI terms |
| `/api/v1/ontology/mappings/{study_id}`  | GET    | Get all value-level ontology mappings      |
| `/api/v1/ontology/mappings/{id}/accept` | POST   | Accept an ontology assignment              |
| `/api/v1/ontology/mappings/{id}/reject` | POST   | Reject an ontology assignment              |
| `/api/v1/ontology/mappings/{id}`        | PATCH  | Curator override with custom term/ID       |

**Quality & Export**

| Endpoint                               | Method | Description                                   |
| -------------------------------------- | ------ | --------------------------------------------- |
| `/api/v1/quality/{study_id}`           | GET    | Coverage, confidence, stage breakdown         |
| `/api/v1/quality/{study_id}/evaluate`  | POST   | F1/precision/recall vs ground-truth CSV       |
| `/api/v1/export/{study_id}/harmonized` | GET    | Harmonized CSV with standardized column names |
| `/api/v1/export/{study_id}/cbioportal` | GET    | cBioPortal-compatible TSV (4-line header)     |
| `/api/v1/export/{study_id}/report`     | GET    | JSON audit report                             |

---

## Project Structure

```
metaHarmonizer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── models.py            # Pydantic request/response schemas
│   │   ├── core/                # settings, security, email, deps, jobs
│   │   ├── db/                  # SQLAlchemy models, session, base
│   │   ├── repositories/        # async data access (studies, mappings, …)
│   │   ├── routers/             # API route handlers
│   │   ├── services/            # Dashboard-owned helpers (ontology, IDs)
│   │   └── engine_adapter/      # ONLY layer allowed to import upstream
│   │       ├── protocol.py      # EngineProtocol contract
│   │       ├── metaharmonizer_impl.py  # Wraps pip-installed upstream pkg
│   │       └── mock_impl.py     # Deterministic engine for tests
│   ├── alembic/                 # Database migrations
│   ├── data/
│   │   ├── schema/              # Curated dicts shipped to the engine
│   │   └── uploads/             # User-uploaded CSVs (gitignored)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Main app with routing
│   │   ├── pages/               # Upload, Review, Ontology, Quality, Export
│   │   ├── components/          # Reusable UI components
│   │   └── api/                 # Typed HTTP client
│   └── package.json
├── pics/                        # Dashboard screenshots
├── metadata_samples/            # Reference & sample data
└── README.md
```

---

## Sample Data

| File                                | Description                                                       |
| ----------------------------------- | ----------------------------------------------------------------- |
| `metadata_samples/curated_meta.csv` | Reference schema — 37 standardized columns with ontology term IDs |
| `metadata_samples/new_meta.csv`     | Raw metadata — 131 heterogeneous columns from multiple studies    |

---

## Performance

| Metric                                      | Value                                                             |
| ------------------------------------------- | ----------------------------------------------------------------- |
| Upload-to-results (141 columns)             | **< 2 second**                                                    |
| Cold start (original, incl. model download) | ~235 seconds                                                      |
| Cold start (model cached, NCI enabled)      | ~120 seconds                                                      |
| Optimization                                | 99%+ latency reduction via engine caching, background pre-warming |

---

## Acknowledgments

- [MetaHarmonizer Engine](https://github.com/shbrief/MetaHarmonizer) — Core ML pipeline for schema mapping
- [cBioPortal](https://www.cbioportal.org/) — Target schema standard for cancer genomics
- [NCI Thesaurus (NCIt)](https://ncithesaurus.nci.nih.gov/) — Biomedical ontology for value normalization
