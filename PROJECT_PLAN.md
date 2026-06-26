# MetaHarmonizerApp — Project Plan & Checklist

> Single-file living plan from now until the end of the maintained-instance window.
> Spec is [docs/metaharmonizerapp-requirements.tex](docs/metaharmonizerapp-requirements.tex). This file is the _what's done / what's next_ tracker.
> Tick boxes as work lands. Each sprint = 1 week.

> **Document map (where each thing lives — no duplication):**
> - **Spec / decisions / scope (the _what & why_):** [docs/metaharmonizerapp-requirements.tex](docs/metaharmonizerapp-requirements.tex). Authoritative for G/U-numbers, F-decisions, NFRs, deliverables.
> - **Status / sprints (the _when & done_):** this file. References the spec; does not restate it.
> - **Engine adapter + verified upstream contract:** [docs/engine-adapter-architecture.md](docs/engine-adapter-architecture.md) (§3.1.1).
> - **Engine↔app collaboration explainer + reply:** [docs/engine-team-collaboration.md](docs/engine-team-collaboration.md).

---

## 1. Scope — features and stories we will deliver

### 1.1 Grant items (G-numbers)

| ID     | Item                           | Shape we ship                                                                                                                                                                                                                                                                                                         | Status                        |
| ------ | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| ✅ G1   | Federation of two-tier KB      | **Federation-lite**: Ed25519-signed `/federation/export` + `/federation/import` REST, trusted-peer registry, two-stage approval (Q10), per-source dedup. No live multi-master.                                                                                                                                       | Done                          |
| — G2   | Unified `POST /harmonize`      | **Out** (Sehyun confirmed). Existing per-route REST stays.                                                                                                                                                                                                                                                            | Out of scope                  |
| ✅ G3   | MCP tools                      | Standalone `metaharmonizer-mcp` PyPI package, three tools, stdio + SSE.                                                                                                                                                                                                                                               | Done (`mcp/`)               |
| ☐ G4   | Versioned audit-record layer   | `audit_events` + `mapping_versions` tables, append-only, queryable JSON.                                                                                                                                                                                                                                              | Designed, not built           |
| ✅ G5  | Accept / reject / edit + batch | Already in prototype Mapping Review page.                                                                                                                                                                                                                                                                             | Done                          |
| ✅ G6   | Side-by-side schema diff       | **Layer A (schema-vs-schema) Done**: `GET /admin/schema-versions/diff` + admin Compare UI — fields added/removed + changed allowed-values. **(B) study-impact re-score + curator-initiated adopt** remain **stretch / build only if curators ask**.                                                                  | Done (A) / Stretch (B)        |
| ✅ G7   | Active-learning ranking        | **Smart review order**: risky-first + group look-alikes adjacent (chosen over diversity/scatter — humans batch similar items). Per-curator/per-study; ordering only. `GET /mappings/{study}/review-queue` + UI toggle.                                                                                          | Done                          |
| ✅ G8  | Quality KPI panel              | Already in prototype.                                                                                                                                                                                                                                                                                                 | Done                          |
| ☐ G9   | Labeled-data export            | Nightly job + endpoint dumping confirmed mappings as CSV/JSONL.                                                                                                                                                                                                                                                       | Not started                   |
| ✅ G10 | Engine packaging (Python)      | Vendored wheel via engine adapter. R packages out of scope (Abhilash).                                                                                                                                                                                                                                                | Done                          |

### 1.2 User stories (U-numbers)

| ID     | Story                                                                                                                                                                                                                                 | Status          |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| ☐ U1   | Upload CSV/TSV → mapping in minutes                                                                                                                                                                                                   | Prototyped      |
| ☐ U2   | Review every mapping w/ confidence + alternatives + override                                                                                                                                                                          | Prototyped      |
| ☐ U3   | Batch accept/reject low-confidence rows                                                                                                                                                                                               | Partial         |
| ☐ U4   | In-app alert on long-job completion — **LinkML validator only**                                                                                                                                                                       | Not started     |
| ☐ U5   | Resolve cell values to ontology terms (NCIt/EFO/UBERON) — select column → confirm terms for each unique value → download table rewritten into ontology terms (engine maps unique values; app re-applies labels across the full table) | Partial         |
| ✅ U6   | Compare a study against a new schema: target-dictionary diff (A) done; study-impact re-score (B) gated (G6)                                                                                                                          | Done (A) / Stretch (B) |
| ✅ U7   | Low-confidence-first ranking, grouped look-alikes (G7)                                                                                                                                                                                | Done            |
| ☐ U8   | Three exports per study (harmonized CSV with value-level rewrite, cBioPortal TSV, audit JSON)                                                                                                                                         | Partial         |
| ☐ U9   | Admin uploads new curated-fields CSV (schema version)                                                                                                                                                                                 | Not started     |
| ☐ U10  | Admin manages users (promote/demote/disable, revoke tokens)                                                                                                                                                                           | Not started     |
| ☐ U11  | Auditor query "who accepted this mapping / state on date X"                                                                                                                                                                           | Not started     |
| ☐ U12  | Batch consumer `POST /harmonize` w/ scoped API token                                                                                                                                                                                  | Partial         |
| — U13  | PEPhub side of inverse-mode                                                                                                                                                                                                           | **Out**         |
| ✅ U14  | AI assistant uses MCP tool                                                                                                                                                                                                            | Done (verified via stdio MCP client) |
| ☐ U15  | Self-hosting org `docker compose up` in <30 min                                                                                                                                                                                       | Not started     |
| ☐ U16  | Pull nightly export of confirmed mappings                                                                                                                                                                                             | Not started     |
| ✅ U17 | Engine adapter swap via `ENGINE_IMPL` env var                                                                                                                                                                                         | Done            |
| — U18  | Viewer read-only across all pages                                                                                                                                                                                                     | **Dropped** (viewer role removed; curator is the read/baseline tier) |
| — U19  | Side-by-side raw vs harmonized comparison view                                                                                                                                                                                        | **Dropped** (redundant with Mapping Review before/after) |
| ☐ U20  | Mapping edit history (who/what/when/note)                                                                                                                                                                                             | Ships with G4 audit |
| ☐ U21  | Download full cBioPortal study folder (multi-file ZIP)                                                                                                                                                                                | Not started     |

### 1.3 Personas served

In: **P1** curator, **P2** admin, **P5** AI assistant user, **P6** third-party org curator, **P7** auditor, **P8** engine-team developer. (**P2.5** viewer collapsed into curator — the role was dropped; curator is the read/baseline tier.)
Out: **P4** PEPhub authoring (Sehyun: ignore for now). SA3.4 inverse endpoint stays as contract, not a delivery target.

### 1.4 Hard "No"s — locked decisions

- No multi-tenancy (self-host is the substitute).
- No live multi-master federation.
- No SSO/SAML/OIDC in v1.
- No PEP YAML export, no eido validation (LinkML only).
- No always-on GPU / self-hosted LLM.
- No PEPhub-side UI work; no PEPhub PR commitment.
- **No re-implementation of the existing curation tools.** We integrate their _rules_ (see §1.5), call `validateData.py` as the export gate, and leave study-by-study utilities (TMB, GENIE imports, gene-panel updates, hugo-symbol-corrector) where they live in [`cBioPortal/datahub-study-curation-tools`](https://github.com/cBioPortal/datahub-study-curation-tools).

### 1.5 Curation rules we inherit (Study-checklist + datahub-study-curation-tools)

Every rule below comes from `docs/Study-checklist.docx.pdf` or the curation-tools repo. They are the **acceptance criteria** for our exporter and the **enum source** for our LinkML schema — we transcribe, we don't invent.

**Header rules** (engine schema-mapping target)

- `Person Gender` → `SEX`.
- Required columns: `OncoTree`, `CANCER_TYPE`, `CANCER_TYPE_DETAILED` (the last two derived from OncoTree code via `oncotree-code-converter` rules).
- Survival columns must use `[PREFIX]_STATUS` / `[PREFIX]_MONTHS`.
- Banned columns to strip: `Part-A consent`, `Part-C consent`, `MSI comments`, `IMPACT CVR TMB`, `IMPACT TMB`, `Collaboration ID`, `PatientCurrentAge`, `Religion` (extensible blocklist).
- Proper-case headers.

**Value enums** (engine value-mapping target + LinkML enums)

| Column             | Allowed values                                                                 |
| ------------------ | ------------------------------------------------------------------------------ |
| `SEX`              | `Female`, `Male`                                                               |
| `SAMPLE_CLASS`     | `Tumor`, `CellLine`, `Xenograft`, `Organoid`                                   |
| `SAMPLE_TYPE`      | `Primary`, `Metastasis`, `Recurrence`                                          |
| `SOMATIC_STATUS`   | `Matched`, `Unmatched`                                                         |
| Survival `_STATUS` | per `Survival_Data_Migration/survivalStatusVocabularies.txt` (lifted verbatim) |

**File / folder rules** (exporter + ZIP packer)

- UTF-8 + LF line endings.
- No smart quotes (`“ ”`) in fields.
- `data_cna_hg19.seg` (no study stable ID in seg filename).
- Reference-genome field present for hg38 studies.
- `LICENSE` file in the study folder.
- `0:` / `1:` prefixing on survival-status fields.
- Study folder must pass `validation/validateData.py` from the curation-tools repo, as-is.

**Study-name hint** (UI nudge, not enforced)

- Format: `TumorType (Institute, Journal Year)`.
- Add keyword `pediatric` in name + description if any pediatric samples.

**Tools whose _rules_ we integrate (not their code):**

- `add-clinical-header` — 5-row meta-header rules.
- `oncotree-code-converter` — OncoTree → `CANCER_TYPE` / `CANCER_TYPE_DETAILED`.
- `Survival_Data_Migration` — survival vocab.
- `generate-meta-files`, `generate-case-lists` — side files in the study folder.

**Tools we leave alone (out of our workflow):**

- `tmb/calculate_tmb`, `hugo-symbol-corrector`, `GN-annotation-wrapper`, `genie_import_dag`, `update-keycloak`, `internal_data_curation_automation`.

**One small UX add we propose:** detect Excel-corrupted gene symbols at upload (`SEPT2` → `2-Sep`) and warn before harmonize.

---

## 2. Architecture skeleton

### 2.1 Components

```
[ Browser SPA (React/Vite/TS) ]
            │  HTTPS + WS
            ▼
[ Caddy reverse proxy ] ──► [ FastAPI app ] ──► [ Postgres (container) ]
                                │                 [ Redis (container)   ]
                                ▼
                       [ arq workers ]
                                │ in-process
                                ▼
                  [ engine_adapter / EngineProtocol ]
                                │
                                ▼
              [ metaharmonizer (vendored wheel) ]
                                │
                                ▼
                       [ ~/.metaharmonizer/   ]   ◄── restored from R2
                       [   FAISS + KB caches  ]       at deploy time
```

### 2.2 Boundary rules

- Only `backend/app/engine_adapter/` may import the upstream `metaharmonizer` package.
- Enforced by [scripts/check_engine_boundary.py](scripts/check_engine_boundary.py) in pre-commit + GitHub Actions.
- Tests run against `ENGINE_IMPL=mock`.

### 2.2.1 Verified engine contract

- The source-checked upstream surface (entry points + exact output columns + gotchas) is recorded once, in [docs/engine-adapter-architecture.md](docs/engine-adapter-architecture.md) §3.1.1 — the authoritative home. Not duplicated here.
- Execution reminders: pin a **commit SHA** (upstream has no tagged releases); imports target `metaharmonizer.*`; only `engine_adapter/` may import it (boundary rule above).

### 2.3 Persistence schema (high-level)

| Table                                      | Owns                                              |
| ------------------------------------------ | ------------------------------------------------- |
| `users`, `sessions`, `api_tokens`          | auth + RBAC                                       |
| `studies`                                  | per-study metadata + schema/ontology version pins |
| `mappings`, `mapping_versions`             | per-mapping current state + history               |
| `ontology_mappings`                        | value-level resolved terms                        |
| `audit_events`                             | append-only decision log (G4)                     |
| `schema_versions`, `ontology_snapshots`    | versioning + reproducibility                      |
| `federation_exports`, `federation_imports` | G1 federation-lite provenance                     |
| `jobs`                                     | arq queue mirror for admin visibility             |

### 2.4 Deploy model

- **Hosted instance**: ours, end of GSoC through the maintained-instance window.
- **Production handover**: cBioPortal infra runs the same Kamal config on their accounts whenever ready.
- **Self-host**: identical compose, `AUTH_MODE=none` allowed for internal-network deployments.

### 2.5 KB / FAISS handling

- KB **pre-built offline** on a fat machine → snapshot `~/.metaharmonizer/` → upload to R2.
- VM cold start = R2 restore + uvicorn. **Never** build KB live on the 2-vCPU VM.
- Per-category strategy: **synonym on every launch tuple** (Sehyun: "we need synonyms"). Launch tuples (Sehyun, pending cBioPortal-team double-check): **NCIt-disease, EFO-disease, UBERON-body-site/tissue, HANCESTRO-ancestry**. Budget the synonym-index RAM for all four (synonym ≈ 25× ST per vocab — see [MEETING_PREP.md §3](MEETING_PREP.md)); revisit ST-only fallback only if RAM forces it.
- **Feasibility — all 4 fit one CX32/8 GB worker (decided 2026-06-21, proceed).** Using the doc's own ~3 MB/1k-terms constant and the one measured point (NCIt-disease synonym = 54k terms → 160 MB), the synonym-index union for all four is **~0.3–0.4 GB** (NCIt-disease ~160 MB, EFO-disease ~100–150 MB, UBERON-body-site ~30–60 MB, HANCESTRO-ancestry ~6 MB — tiny vocab, effectively free). Ontology-worker RSS = SapBERT (~1.6 GB) + PubMedBERT (~0.4 GB) + FAISS union (~0.35 GB) + runtime/embedding spikes (~0.8–1.0 GB) ≈ **3.2–3.5 GB**, ~4.5 GB headroom. **No drop needed; headroom for ~1–2 more categories** (avoid stacking a second *disease-sized* synonym vocab). Driver is **strategy (synonym), not ontology count**. Safe rule (no LRU eviction upstream): **one ontology category per worker process** so a worker never holds the union of every vocab. Real ceiling ≈ keep synonym-union < ~1.5 GB (we're at ~0.35). Confirm per-tuple RAM empirically during the offline build (W4 task).

---

## 3. Sprint plan — week-by-week to the end

> Sprint = 1 week. Today: 2026-06-11.
> Each sprint has: **goal · tasks · acceptance**. A sprint counts done only when its acceptance line is true on the live URL, not just merged.

> **Sequencing principle (decided 2026-06-17): build first, benchmark later.**
> We implement the backend + frontend features to a solid, working product **before** investing in the Production Readiness Benchmark. Sprint 1 keeps only the **scope sign-off** (cheap, unblocks everything); the engine/accuracy benchmark (D3) is **deferred to Phase D (Sprint 12)** once there is a real product to measure end-to-end. Rationale: benchmarking a moving prototype wastes effort; one rigorous benchmark on the near-final system is more credible and cheaper than re-running it every sprint.

---

### Phase A — Foundation (Sprints 1–3)

#### Sprint 1 — Scope sign-off

**Goal:** lock final scope with Sehyun so every later sprint builds against a settled spec. (Benchmarking is deferred — see the sequencing principle above.)

**Tasks:**

- ☐ Send the consolidated reply ([MEETING_PREP.md §6](MEETING_PREP.md)).
- ☑ **Resolved by Sehyun:** Q6 active-learning scope = **per-study / cross-curator**; Q8(iii) ground truth = **public datahub studies, we draft + she verifies, engine not tuned on the picked studies**; FAISS launch tuples = **NCIt-disease, EFO-disease, UBERON-tissue, HANCESTRO-ancestry** (synonym indexes, pending her cBioPortal-team double-check); F-11 ownership = **engine owns vector-DB build/refresh + encoder choice + corpus versioning; dashboard owns curator UI + audit + thresholds**; export gate = **LinkML (QC checklist + survivalStatusVocabularies.txt, no invented rules) + validateData.py**, additional ontologies added later only if the cBioPortal team asks.
- ☑ **Decided by us (F-14, answering Sehyun's F-11 follow-ups):**
  - **Engine-update propagation → pinned, never silent "latest".** The pinned unit is an **engine bundle** = `(engine_sha, model_registry_hash, kb_snapshot_id)` — i.e. the `metaharmonizer` wheel SHA + the `method_model.yaml` encoder/LLM registry + the FAISS/SQLite KB snapshot restored from R2. Container image embeds wheel + registry; KB snapshot restored at deploy by ID, so there are many container tags per (engine × encoder × KB) combo and we pin the bundle as one unit. Hosted **and** self-host pin a bundle; neither is force-upgraded. Updates = deliberate bundle-bump PR → CI + re-run benchmark → deploy if pass → one-line rollback (F-13 cadence). Recorded per study/decision for reproducibility (extends the two-axis pin + G4 audit "engine version").
  - **Customization scope (per-instance, admin/env-tunable):** confidence thresholds (`LLM_THRESHOLD`, auto-accept / flag-for-review bands, fuzzy threshold), LLM on/off + model per hop (`GEMINI_API_KEY`, `METHOD_MODEL_YAML`), per-study version pins, active-learning on/off, FAISS launch tuples + per-category strategy, limits/quotas, auth mode, retention. **Not customizable** (engine-team-owned): encoder architecture + embedding pipeline, the four-stage cascade, KB build + corpus versioning — each a YAML-registry config swap, never a fork.
- ☑ **Decided by us (Q9 retention — no history) — PROVISIONAL, pending curation-team confirm (Sehyun said "double-check with the curation team" on Q9-ii/iii/iv):** curators don't need historical copies of raw uploads or generated exports. **Keep no history of files.** A re-curation = a fresh re-upload (faster the second time because the prior decisions are already in the KB + audit log). The valuable data — confirmed mappings + append-only audit — is **always kept** in Postgres. **Sequencing:** raw upload is retained only while a study is being worked; once Sprint 9 persists the harmonized output table, the raw upload is purged right after a successful harmonize (export then regenerates from the stored output, not the raw file). **Session safety:** because all accept/reject/edit work is persisted server-side as the curator goes, closing/reopening a tab never loses progress — no browser-held state. Supersedes the age-based purge stub.
- ☐ **Still pending (curation team, not Sehyun):** confirm the four FAISS tuples with the cBioPortal team (Sehyun to check); confirm Q9 retention (no-history) + Q9-iv admin-only deletion. _Web-UI-bolded items are now resolved (see §5)._
- ☐ **Open items from the Sehyun↔Ritika (cBioPortal curation team) Slack thread (2026-06):**
  - **(a) Treat the cBioPortal data dictionary as a _subset_, not a closed set.** Ritika: "This is a subset of the clinical data we have. There is definitely more in the public database." So the attached `docs/my sequence/cbioportal_data_dictionary.csv` (and any LinkML schema derived from it) must stay **open/extensible** — never hard-code the attribute set as final. Already covered structurally by **G6** (schema-version diff) + **U9** (admin uploads new curated-fields CSV); keep this constraint visible so neither regresses to a fixed schema.
  - **(b) Get the curators' answer on _which_ extra attributes should be ontology-backed before extending `FIELD_ONTOLOGY`.** Sehyun's open follow-up: which `allowedvalues` enums / free-text fields should resolve against an ontology (e.g. `PRIMARY_SITE` → UBERON; the `recurrence|…|primary` enum → ontology terms). Today [backend/app/engine_adapter/_ontology.py](backend/app/engine_adapter/_ontology.py) routes only `disease→ncit`, `body_site→uberon`, `treatment→ncit`. **Constraint:** any ontology beyond NCIt/UBERON/OncoTree (e.g. EFO, HANCESTRO) is an **engine dependency** (registry root / new category), not just an app-config change — see §5 engine-team questions. Confirms Ritika's note that survival elements (`OS_*`, `PFS`, `DFS`) are in-scope (already in §1.5).
  - **(c) (experimental) "suggest new attributes" module** for fields not confidently covered by the suggested schema (Sehyun mentioned it as early-stage). Not yet built; closest backlog is U5/G6 + the FieldSuggester panel (F-12). Track as a distinct experimental feature **only if curators ask**.
- ☐ **Sehyun's app-capability questions (2026-06 follow-up) — answers + status:**
  - **(1) Select the target schema (cBioPortal default).** Partially built: [backend/app/routers/admin.py](backend/app/routers/admin.py) `upload_schema_version` + `schema_versions` repo + active seed `CURATED_PATH`. **Gap:** per-upload _user_ choice of which registered schema to map against (today one active version). Folds into **U9** (admin uploads curated-fields CSV) + **G6** (schema diff). Sehyun checking cBioPortal team for per-attribute preferred ontology → feeds item (b) above.
  - **(2)/(3) MetaHarmonizer:SchemaRegistry delivery (engine-side build, app-side ingest).** Sehyun is building a prebuilt registry of public target schemas (target columns + LLM-generated alias dict). **Delivery mechanism into the app = the schema-version upload path**, but note: today the app's `curated_df` carries only **columns**; the **alias dictionary lives engine-side** (`schema_mapper` `FIELD_MODEL` config). Delivering a "schema + alias" bundle needs the upload to also carry/forward the alias dict to the engine — **new contract item, confirm with engine team** (boundary: aliases are engine config, not app data).
  - **(4) Alias-generation tool for a user's own schema.** Agree it can live **outside the app** as a standalone util; the app just consumes its output via (3). No app work unless we choose to surface it.
  - **(5) Show context for term selection.** The Mapping Review UI already shows alternatives + confidence; "context" (other linked columns/row values to disambiguate) is a **UI enhancement** — feasible, not yet built. New item for the review page.
  - **(6) Run mode: SchemaMapper-only / OntologyMapper-only / both.** **Not built** — `_run_pipeline` ([backend/app/workers/tasks.py](backend/app/workers/tasks.py)) always runs `harmonize_schema` → `map_values` in sequence. Add a `mode` param on the harmonize request → conditionally skip a stage. New feature (small, app-side).
  - **(7) Run OntologyMapper on specified column(s) only.** Overlaps **U5** (select column → confirm terms). Engine `OntoMapEngine(category, query)` already supports per-column scoping; needs a column-scoped request path + UI. New feature, builds on U5.
  - **(8) Two deployments (cBioPortal + public-facing) with input-size cap on the public one.** **Already supported via env** — `max_upload_mb` (default 50, [backend/app/core/settings.py](backend/app/core/settings.py)) + `AUTH_MODE=none`. A public instance = same image, lower `MAX_UPLOAD_MB` + tighter rate limits ([backend/app/core/limits.py](backend/app/core/limits.py), anon budget). No code change; document as a deploy profile (ties to U15 self-host kit). Confirm: public-facing also wants row-count cap, not just byte size?
- ☐ Pre-pick (with Sehyun) the 5–10 datahub studies we'll benchmark later in Phase D — just the list now, no labeling yet.
- ☐ Cut spec v2 of `metaharmonizerapp-requirements.tex` absorbing v1 confirmations + curation-tool/checklist takeaways.

**Acceptance:** spec v2 in repo · zero open Q-numbers in §7 of the spec · benchmark study-list agreed with Sehyun (labeling + run happen in Phase D).

---

#### Sprint 2 — Persistence + audit foundation + operational contracts (G4)

**Goal:** every accept/reject/edit currently in the prototype writes a real append-only audit row in Postgres, and every cross-cutting contract from spec §6 (Operational contracts) is wired into the foundation so every later sprint inherits them for free.

**Tasks (persistence):**

- ☐ Postgres schema: `users`, `studies`, `mappings`, `mapping_versions`, `audit_events`, `schema_versions`, `ontology_snapshots`, `sessions`, `api_tokens`, `job_runs`, `job_failures`, `idempotency_keys`.
- ☐ Alembic migrations from clean state.
- ☐ Append-only enforcement on `audit_events` (no DELETE path; revoke on the role).
- ☐ Two-axis pin (`schema_version_id`, `ontology_snapshot_id`) wired through the harmonize flow.
- ☐ `version INT NOT NULL DEFAULT 1` on `mappings`, `studies`, `schema_versions` for optimistic locking (spec §6.2).
- ☐ Migrate prototype SQLite contents → Postgres.
- ☐ `pytest` cases that prove DELETE on `audit_events` raises and that a stale-version `UPDATE` returns 409.

**Tasks (operational contracts — foundation, before any router grows):**

- ☐ Pydantic `Settings` in `backend/app/settings.py` loading the full env-var catalogue (spec §6.5); boot fails on missing required vars; `JWT_SECRET < 32 bytes` rejected.
- ☐ `/api/v1/...` URL prefix on every JSON route; WebSocket paths follow same prefix.
- ☐ Unified error envelope middleware (`{ error: { code, message, details, request_id } }`, spec §6.1); `request_id` injected into structured-log context for the request's lifetime.
- ☐ Cursor-based pagination helper (`{ items, next_cursor }`, default 50 / cap 500).
- ☐ `Idempotency-Key` middleware backed by Redis with 24h TTL; covers `POST /studies`, `POST /harmonize`, `POST /federation/import`.
- ☐ Optimistic-locking helper used by every `PATCH`/`PUT` that touches a versioned table; emits `ETag: W/"<version>"` on `GET`.
- ☐ Limits enforced at boundary (spec §6.4): upload size, columns/rows per study, rate limits via Redis sliding window, MCP tool-call wall-clock cap.
- ☐ Structured JSON logs on stdout with request_id; `/healthz` (liveness) and `/readyz` (DB + Redis + object-store ping) endpoints; Prometheus `/metrics` (admin-scoped) exposing the four golden signals + queue depth + WS connections + auth-failure counter.
- ☐ Sentry init (no-op when `SENTRY_DSN` unset); release tag = git short SHA.
- ☐ Data-retention scaffolding: nightly cron job stub that purges uploads >90d, exports >30d, revoked sessions >90d (jobs added; no-op until volumes exist).

**Acceptance:** every UI accept/reject/edit on the harmonize page writes one row in `audit_events`, queryable via `GET /api/v1/audit/...`; a contract-test suite (`pytest tests/contract/`) proves the error envelope, pagination cursor, idempotency replay, optimistic-locking 409, and all eight limits; `/healthz` and `/readyz` green in CI; `make settings-check` fails when a required env var is missing.

---

#### Sprint 3 — Auth + RBAC + session model

**Goal:** real login + the three roles enforced in REST + UI, with the seven session-state defaults (S1–S7) wired end-to-end.

**Tasks:**

- ☐ Email/password + JWT access/refresh (S2: 15 min / 30 d sliding).
- ☐ Refresh JWT in `httpOnly; Secure; SameSite=Lax` cookie at `/auth/refresh`; access JWT in-memory only (S1).
- ☐ Single-flight silent-refresh fetch wrapper on the frontend (S3).
- ☐ WebSocket ticket endpoint `POST /ws/ticket` returning 30-second Redis-backed nonce (S4).
- ☐ Frontend state libraries: `zustand` (client UI) + `@tanstack/react-query` (server state) (S5).
- ☐ Double-submit CSRF middleware on cookie-authed mutating routes; exempt `Authorization: Bearer` paths (S6).
- ☐ `sessions` table with `(user_id, refresh_jti, ip, user_agent, created_at, last_seen, revoked_at)`; profile-page session list + revoke; admin force-logout (S7).
- ☐ Email verification + password reset flow (Resend).
- ☐ Domain-restricted signup: `ALLOWED_EMAIL_DOMAINS` allow-list (e.g. institutional domain); reject personal-domain (gmail, etc.) registrations at the API boundary; empty list → admin-invite-only. Verification email confirms the address.
- ☐ Two roles wired (`curator` / `admin`) per the RBAC matrix in the spec (the `viewer` role was dropped — curator is the read/baseline tier). **Multiple admins** sharing operational work (not a single super-user); concurrent-admin-safe via attributed audit + no-last-admin-demote guardrail.
- ☐ API tokens (`read` / `write` scopes) + revocation.
- ☐ **Admin-only "delete study" endpoint + UI (Q9-iv)** — cascade across mappings/exports/audit-provenance; admin-attributed audit row; **provisional pending curation-team confirm**. Curators cannot delete; only admins.
- ☐ HIBP check on signup; lockout after N failed logins.
- ☐ `AUTH_MODE=none` flag for self-host (with explicit warning in logs).
- ☐ Argon2id password hashing.

**Acceptance:** Playwright E2E covers all RBAC matrix rows (unauthenticated denied write, curator allowed, admin allowed) — green on CI; second test logs in on two browsers, revokes session-A from session-B, verifies session-A's next request is 401.

---

### Phase B — Grant deliverables (Sprints 4–7)

#### Sprint 4 — WebSocket + job pipeline

**Goal:** the harmonize page shows live stage-by-stage progress and a completion notification — no polling.

**Tasks:**

- ☐ arq workers in-process engine, one job per worker process.
- ☐ Job-lifecycle state machine `queued → running → {succeeded | failed | cancelled}` written to `job_runs` (spec §6.3).
- ☐ Retry policy: 3 attempts with backoff (5s/30s/3min) for transient errors only; logical errors fail-fast.
- ☐ Soft timeout 5 min, hard timeout 15 min (worker killed on hard); `error_code = TIMEOUT`.
- ☐ Dead-letter table `job_failures`; admin surface to re-queue or discard.
- ☐ Cancellation: worker checks `cancelled` flag at every stage boundary inside `harmonize_columns` / `harmonize_values`.
- ☐ Redis pub/sub bridge from worker → WS.
- ☐ WS endpoints: `/api/v1/ws/jobs/{study_id}` (per-study progress) and `/api/v1/ws/notify/{user_id}` (per-user) — auth via `/ws/ticket` nonce (S4).
- ☐ Frontend: WS client with reconnection-on-close and typed messages.
- ☐ Live stage progress on Mapping Review (Stage 1/2/3/4 status pills).
- ☐ Bell-icon unread-badge in header (server-counted).
- ☐ Opt-in browser desktop notification on job completion (U4).
- ☐ Worker-restart resilience: pub/sub means no in-memory state lost.

**Acceptance:** harmonize a 200-col study, p95 ≤ 60 s warm; the curator sees stage progress live and a toast on done; killing a worker mid-job leaves the job in `queued` for the next worker to pick up (no orphaned `running` rows).

---

#### Sprint 5 — MCP server (G3)

**Goal:** any MCP-aware LLM client can call the engine without going through our website.

**Tasks:**

- ☐ `metaharmonizer-mcp` package skeleton + `pyproject.toml`.
- ☐ Three tools: `harmonize_table`, `harmonize_columns`, `harmonize_values`.
- ☐ stdio transport.
- ☐ SSE transport.
- ☐ Tool schemas + descriptions + examples in JSON.
- ☐ Auth via API token from the user's hosted-instance account.
- ☐ One-page setup guide per client (Claude Desktop, Cursor, GitHub Copilot, Cline).
- ☐ Publish to TestPyPI → smoke test → publish to PyPI proper.

**Acceptance:** `pip install metaharmonizer-mcp` from a clean machine, configure Claude Desktop, ask "harmonize this CSV", get a result back.

---

#### Sprint 6 — Active learning (G7)

**Goal:** the review queue surfaces the items that actually need a human, and re-orders as the curator works.

**Tasks:**

- ☐ Confidence-ascending default sort on Mapping Review.
- ☐ Margin-sampling re-rank: on every accept/reject, recompute scores combining `(1 - confidence)` + small penalty when a candidate resembles a recent acceptance.
- ☐ Scope: **per-study / cross-curator** (Sehyun confirmed Q6).
- ☐ Document the AL ↔ tiered-KB interaction: AL re-ranks the _review queue_ only; tiered-KB membership is governed by Q10's two-stage approval, independent of AL ranking.
- ☐ Add re-rank instrumentation to the audit log so we can later measure "did AL save curator time?"
- ☐ Unit tests with synthetic curator sessions (3 acceptances of "diabetes…" → next 5 rows are not duplicates).

**Acceptance:** simulated curator session shows the queue converging on diverse mappings vs random order, measurable in the audit metrics.

---

#### Sprint 7 — Schema versioning (U9) + schema diff (G6, low priority)

**Goal:** admins can publish a new `curated_fields` CSV as a new version with confidence; existing studies stay pinned and never shift on their own. The diff UI is the lower-priority part of this sprint.

**Tasks (committed — versioning is the backbone):**

- ☐ `POST /admin/schema-versions` upload endpoint (admin-only) — new schema is a **new version**, never an overwrite.
- ☐ Admin "promote schema version" flow + audit row (explicit admin action; new studies use current, existing studies stay pinned).
- ☐ Per-study pin / un-pin endpoints + UI.
- ☐ Schema-diff page — **layer A (schema-vs-schema):** column-by-column added/removed/modified between old and new `curated_fields` CSV, with sample-value diff for changed rows. (Cheap; ships with versioning.)

**Tasks (low priority / stretch — build only if curators ask in the meeting):**

- ☐ Schema-diff **layer B (study-impact):** re-compare a pinned study's source columns against the new schema and highlight which mappings would shift if adopted. (Engine re-score on affected columns.)
- ☐ Curator-initiated "adopt new schema for this study" UX (vs. admin-only) — pin the decision with the curation team first.
- ☐ Comparison view (U19) — dropped from v1 (redundant with Mapping Review before/after).
- ☐ Mapping history (U20) — ships with the G4 audit work.

**Acceptance:** admin can promote a new schema and see what changed (layer A); an existing study pinned to v1 doesn't shift on its own. Layer B + curator re-pin UX are explicitly out unless curator demand surfaces.

---

### Phase C — Federation + exports (Sprints 8–9)

#### Sprint 8 — Federation-lite (G1)

**Goal:** two installs swap a `.federation.json` file and import each other's curator-confirmed mappings.

**Tasks:**

- ☐ `GET /federation/export` (admin token): emits signed JSON of confirmed mappings + provenance.
- ☐ `POST /federation/import` (admin token): ingests a remote export, attributes to source instance, marks "pending local approval" (per Q10).
- ☐ Signing: Ed25519 keypair per instance; key rotation documented.
- ☐ Import dedup: same mapping arriving twice from different instances should not double-count.
- ☐ Provenance tables: `federation_exports`, `federation_imports`.
- ☐ Reject suspicious imports (signature mismatch, schema mismatch).
- ☐ E2E with two staging instances doing a round-trip.

**Acceptance:** two instances exchange a `.federation.json`, mappings show up in each other's UI tagged with the source institution, neither is auto-merged.

---

#### Sprint 9 — Labeled export (G9) + cBioPortal study folder (U21)

**Goal:** the engine produces clean, validateData-passing cBioPortal study folders, plus a labeled-mappings dataset for retraining.

**Tasks:**

- ☐ Nightly job dumping `(raw_column, raw_sample_values, accepted_target, ontology_id, schema_version, ontology_version)` (G9).
- ☐ `GET /export/{study}/labeled` endpoint serving the latest dump.
- ☐ **Value-level rewrite on export (U5):** apply each curator-confirmed `value → ontology term` back across every row of the harmonized column (deterministic dictionary join, app-side), so the downloaded table carries resolved cell values — not just renamed columns. (Today `export_harmonized_csv` only renames columns.)
- ☑ Multi-file ZIP packer producing **both** clinical levels — `data_clinical_patient.txt` + `meta_clinical_patient.txt` **and** `data_clinical_sample.txt` + `meta_clinical_sample.txt` — plus `meta_study.txt`. (Done: patient/sample split, one row per unique patient / per sample, PATIENT_ID links them. Case-list files + `LICENSE` still to add.)
- ☑ Required column injection (`PATIENT_ID`/`SAMPLE_ID` rules), `0:`/`1:` survival prefixing, banned-columns blocklist applied (per §1.5). (Banned: Part-A/Part-C consent, MSI comments, IMPACT CVR TMB, IMPACT TMB, Collaboration ID, PatientCurrentAge, Religion — matched by target id or raw name.)
- ☐ LinkML schema authored as a verbatim transcription of the QC checklist + `survivalStatusVocabularies.txt` (no new rules).
- ☐ LinkML validator gate before export — fail fast with actionable errors mapping back to checklist line.
- ☑ Final gate: invoke `validation/validateData.py` from `cBioPortal/datahub-study-curation-tools` as the source of truth on our generated ZIP. (Done: integration test invokes the **real** validator offline via `CBIO_VALIDATE_DATA`; verified our patient+sample folder passes — "Validation of data succeeded", 0 error lines. Skips when validator unconfigured → wire into CI.)
- ☐ OncoTree → `CANCER_TYPE` / `CANCER_TYPE_DETAILED` derivation in the exporter (rules from `oncotree-code-converter`). **Blocked on the converter's OncoTree data — won't fabricate the mapping (§1.5: transcribe, don't invent).**
- ☑ UTF-8/LF + no-smart-quotes enforcement. (`data_cna_hg19.seg` / hg38 reference-genome are genomic-file rules — N/A for the clinical-only export.)
- ☐ E2E: feed the ZIP to actual `validateData.py` on CI against a representative datahub study. (Local gate proven against the real validator; CI wiring — install validator deps incl. mysqlclient, set `CBIO_VALIDATE_DATA` — still to do.)

**Acceptance:** exported folder accepted by `validateData.py` as-is on a real datahub study · LinkML validator catches every rule in §1.5.

---

### Phase D — Production-ready (Sprints 10–12)

#### Sprint 10 — Hardening + observability

**Goal:** when something goes wrong, we know about it in minutes, not days — and one dependency blip degrades one feature, never the whole app.

**Tasks:**

- ☐ Sentry backend (FastAPI middleware) + frontend (React error boundary + breadcrumbs).
- ☐ `/healthz` (process alive) + `/readyz` (Postgres + Redis + R2 reachable + free-disk check).
- ☐ UptimeRobot 5 monitors: landing page, `/healthz`, `/readyz`, harmonize round-trip, WS round-trip.
- ☐ Structured JSON logs to stdout (request id, user id, study id).
- ☐ Nightly Postgres dump → R2 with 30-day retention.
- ☐ Weekly restore-test job in CI (restores last night's dump into a throwaway DB, runs migrations, asserts schema sane).
- ☐ Admin System Health page: queue depth, worker count, last successful backup, p50/p95 job latency.

**Tasks (graceful degradation — spec §6.9):**

- ☐ Per-dependency failure behaviour wired: Postgres down → 503 on writes, reads keep rendering; Redis down → jobs refused cleanly + UI falls back from WS to 5s poll + rate-limit fails _closed_; object store down → uploads/exports disabled with banner, review unaffected; Gemini down → engine falls back to deterministic result + `llm_unavailable` audit flag.
- ☐ Queue backpressure: bounded depth → `429` + `Retry-After` + "N ahead of you" instead of OOM.
- ☐ Crash recovery: `job_runs` heartbeat + reaper re-queues stale `running` jobs; no orphaned rows.
- ☐ Contract tests in `tests/resilience/` that simulate each dependency outage and assert the degraded behaviour (not a 500).

**Acceptance:** kill a worker in production — Sentry pings within 5 min, UptimeRobot pings within 5 min, system recovers without manual intervention; the resilience test suite proves each of the five dependencies degrades gracefully rather than 500-ing.

---

#### Sprint 10.5 — Analytics dashboard + UI/UX polish

**Goal:** turn the prototype's KPI-cards-plus-three-charts into a dashboard that answers "is this study ready?" and "how is the effort going?", and bring the whole UI to a consistent, accessible, polished bar — per spec §3.5 and §3.6.

**Tasks (per-study dashboard — spec §3.5.1):**

- ☐ Readiness banner (Ready / Needs review / Blocked) from confirmed % + required-column coverage + would-pass-validation.
- ☐ KPI strip with required-column coverage as a distinct metric; every KPI deep-links into a filtered Mapping Review.
- ☐ Confidence histogram with auto-accept / flag-for-review threshold bands drawn on it.
- ☐ Stage-contribution bar (Stage 1/2/3/4 + unmapped) and review-status donut.
- ☐ Ontology-resolution panel: % distinct values resolved per column + top unresolved values.
- ☐ Progress-over-time sparkline from the audit timeline.
- ☐ "What's blocking export" checklist drawn from §1.5 rules, each row linking to the fix.

**Tasks (cross-study dashboard — spec §3.5.2):**

- ☐ Throughput (studies/week, columns/week, median upload→export time — feeds D3).
- ☐ Engine-quality trend (avg top-1 confidence, % auto-accepted) segmented by schema version.
- ☐ Active-learning payoff + KB-growth charts.
- ☐ Team activity (per-curator counts, framed as activity not ranking) + health strip.

**Tasks (UI/UX polish — spec §3.6):**

- ☐ Consolidate Tailwind design tokens (color, spacing, radius, shadow, type scale); audit every page onto them.
- ☐ Mapping Review density pass: sticky headers, zebra rows, monospace IDs, right-aligned numerics, confidence color-scale, progressive-disclosure expandable row.
- ☐ Optimistic UI on accept/reject with conflict rollback toast (ties to §6.2); skeleton loaders replace spinners.
- ☐ Keyboard shortcuts (`j/k` move, `a/r` accept/reject, `/` search) on Mapping Review.
- ☐ Accessibility pass to WCAG 2.1 AA: focus rings, ARIA labels, contrast ≥ 4.5:1, never-color-alone for state.
- ☐ Designed empty + error states everywhere (error state shows `request_id`).
- ☐ Dashboard view export to PNG/PDF; whole dashboard visible to every signed-in user (curator + admin).
- ☐ `prefers-reduced-motion` respected; transitions ≤ 200ms.

**Acceptance:** a curator can tell at a glance whether a study is export-ready and what's blocking it; any signed-in user (e.g. a PI as curator) can self-serve cross-study status; an automated axe-core accessibility scan passes with zero serious violations on the four main pages; every chart click navigates to the matching filtered view.

---

#### Sprint 11 — Test suite + CI/CD

**Goal:** every commit ships through a green pipeline; rollback is one command.

**Tasks:**

- ☐ pytest backend ≥ 80 % coverage (excluding generated code + migrations).
- ☐ Vitest frontend ≥ 75 % coverage.
- ☐ Playwright 3 happy-path E2E scenarios: upload → harmonize → review → export; admin flow; unauthenticated-denied flow.
- ☐ GitHub Actions stages: lint → typecheck → tests → engine-boundary check → build images → push to ghcr.io → Kamal zero-downtime deploy.
- ☐ One-command rollback (`kamal rollback`) verified.
- ☐ Branch protection: no merge to `main` without all green.

**Acceptance:** clean clone → CI run → green deploy in ≤ 15 min · `kamal rollback` from the latest deploy back to the previous in ≤ 60 s.

---

#### Sprint 12 — Benchmark (D3 + D9), docs, hand-in

**Goal:** now that the product is solid, run the Production Readiness Benchmark end-to-end for the first time and again as the final measure; complete the SA3.1 final-report package; URL live; reviewer can verify.

**Tasks:**

- ☐ **D3/D9 — Production Readiness Benchmark** on the agreed 5–10 datahub studies (deferred here per the sequencing principle): label ground truth (we draft, Sehyun verifies), then capture D-A accuracy/calibration, D-B latency, D-C resources, D-D failure modes, D-E edge cases, D-F threshold sweep on the **final shipped system**. **Gold target (Q8-iii) — self-serve, no hand-labeling:** the curation team's *already-published* `curated_meta` for the picked public datahub studies IS the gold target. We do **not** draft labels from scratch or need a hand-verified slice — accuracy = engine output vs their existing curated metadata. Sehyun already confirmed the engine was **not tuned** on these studies ("Sure"), so the only remaining courtesy item is agreeing the specific 5–10 study list (non-blocking; any public datahub study works).
- ☐ Publish `docs/benchmark/<date>-sa3.1.md` (single authoritative report — no separate early baseline since we build-first).
- ☐ Curator User Guide (D6) with annotated screenshots.
- ☐ API Reference (D7) autogen from OpenAPI + MCP setup guide pages.
- ☐ Deployment Guide (D5): one-command self-host, env vars, scale knobs, backup procedure.
- ☐ cBioPortal Integration Guide (D4): how to ingest an exported study folder.
- ☐ Operational Runbook (D8): what to run when, recovery flows, secret locations, handover checklist for cBioPortal infra.
- ☐ Performance Evaluation Report (D9 prose, sitting on top of the benchmark CSVs/PNGs).
- ☐ README front page: project description, screenshots, hosted-instance URL, links to D5–D9.
- ☐ Hand-in: file the SA3.1 final-report package with cBioPortal mentors.

**Acceptance:** benchmark report committed on the final system · a fresh reviewer can land on the README, click through to the live URL, complete a harmonize+export round-trip, find every D-number doc within two clicks.

---

### Phase E — Maintained-instance window (post-GSoC, 3–6 months)

#### Sprint M-1 — first month after hand-in

**Goal:** prove the instance is operationally healthy under real curator use.

**Tasks:**

- ☐ Triage Sentry weekly; close out anything user-visible.
- ☐ Track hosted-instance availability against the 99 % monthly SLO.
- ☐ Apply patch releases as upstream `metaharmonizer` ships them — single-file engine-adapter update only.
- ☐ Collect first round of curator feedback; file issues with `feedback-v1` label.

#### Sprint M-2 — second month

**Goal:** fix the top three real-world issues from M-1 feedback.

**Tasks:**

- ☐ Pick top-3 by curator-impact / fix-effort ratio.
- ☐ Ship behind feature flags if non-trivial.
- ☐ Update D6 user guide for any UX change.

#### Sprint M-3 — third month

**Goal:** start the cBioPortal-infra handover prep.

**Tasks:**

- ☐ Walk-through call with cBioPortal infra team.
- ☐ Side-by-side first deploy onto their infra (us shadowing).
- ☐ Confirm their Sentry/Resend/R2 accounts work.
- ☐ Dry-run a full backup-restore on their VM.

#### Sprint M-4 — fourth month

**Goal:** execute handover or extend.

**Tasks:**

- ☐ If cBioPortal infra is ready: DNS-cutover the URL; sunset our hosted instance; hand them the runbook + on-call rotation.
- ☐ If not ready: extend our window by one sprint at a time, record reason in the runbook.

#### Sprint M-5 / M-6 — wind-down or extended operation

**Goal:** clean exit.

**Tasks:**

- ☐ Either: post-handover OSS-maintainer mode (no pager, code patches only).
- ☐ Or: per-sprint extension with a documented end-date.
- ☐ Final closing note in the README when the maintained-instance window ends.

---

## 3.1 Cross-cutting workstreams (not a single sprint — tracked on the board)

These span multiple sprints or fill gaps the sprint list left implicit. They are tracked as their own board cards so nothing is lost between feature sprints.

### W1 — Dev infra: local docker-compose stack (Phase A, enables Sprint 2+)

- ☐ `docker-compose.yml`: Postgres + Redis + api + worker (+ Caddy stub).
- ☐ Dev `.env.example` with the full env-var catalogue; `METAHARMONIZER_DATA_DIR` mounted with schema/value dicts.
- ☐ Make/just shortcuts (up/down/migrate/test); local `/healthz` + `/readyz` reachable.

### W2 — Engine-adapter ontology wiring (F-11) + FieldSuggester panel (F-12) (Phase B)

> **Engine capability check (2026-06-22, against installed wheel 0.3.0 = matches upstream structure):** `OntoMapEngine` + full `KnowledgeDb` (FAISS+SQLite, NCI/OLS/UMLS clients) ship and import. Engine `_CORPUS_REGISTRY` first-class tuples: **NCIt-disease (NCIT:C3262), NCIt-bodysite, NCIt-treatment, UBERON-bodysite (UBERON:0001062), MONDO-disease**. Of Sehyun's 4 launch tuples: **NCIt-disease ✅ and UBERON-bodysite ✅ are ready today**; **EFO-disease ⚠️ buildable (OLS client knows EFO) but has no registry root — needs an engine-side config or a `corpus_df`**; **HANCESTRO-ancestry ❌ not implemented (no `ancestry` category, no HANCESTRO in OLS client) — engine-team work.** No ontology corpus cached locally yet (`~/.metaharmonizer` empty) → a real run needs the offline KB build (`UMLS_API_KEY` / OLS).

- ☑ **App-side `map_values()` wiring (F-11) — DONE for the engine-ready tuples.** `engine_adapter/_ontology.py` routes NCIt-disease / UBERON-bodysite / NCIt-treatment through `OntoMapEngine` when `ONTOLOGY_ENGINE=1`, normalizes its result frame to our DTOs, and **falls back to the curated dictionary** for every other field and on any engine error / missing corpus (default behaviour unchanged). Boundary-clean (inside `engine_adapter/`, public API, no fork; passes `check_engine_boundary.py`). 5 unit tests (routing, normalize, fallback). **EFO / HANCESTRO deliberately NOT wired — engine-team scope.**
- ☑ **Engine output-column contract test (F-11 safeguard)** — done earlier (`test_engine_output_contract.py`).
- ☑ **Real offline build attempted (2026-06-22) — two findings:**
  - **No UMLS key needed for the *corpus fetch*.** UBERON built via public OLS4 (17,160 terms, zero auth); NCI uses the public **EVSREST** endpoint (`api-evsrest.nci.nih.gov`) — the `UMLSDb(api_key)` object is *instantiated but unused* in the descendants/corpus path. So the launch-tuple corpora fetch **key-free** (UMLS only gates a narrower synonym-enrichment feature). This kills the "needs Sehyun's key" blocker for the build.
  - **⚠️ ENGINE BUG (engine-team, F-11): UBERON-bodysite crashes end-to-end on a fresh build.** After fetching, `OntoMapEngine._partition_codes` raises `ValueError: Unknown ontology prefix in codes: ['COB_0000021','NCBITaxon_10045',…]`. UBERON legitimately imports cross-ontology terms (COB, NCBITaxon); the engine's own corpus builder pulls them in, but the concept-table partitioner only accepts `['BFO','CHEBI','CL','DOID','EFO','GO','HP','MONDO','OBI','Orphanet','PATO','UBERON']` + bare NCI codes and **hard-crashes instead of skipping** the rest. So UBERON-bodysite is registry-listed but **not actually buildable** on wheel 0.3.0. **We must NOT patch the engine (boundary) or hand-filter the corpus (curation gray area) — report to engine team.** NCIt-disease uses bare `C####` codes (partitioner-supported) so it likely avoids this — verifying separately.
- ☐ Retire the dashboard-side `_STATIC_NCIT` + `nci_cache.json` + `ONTOLOGY_MAP` fallback chain — **only after** the engine path is verified for the launch tuples (keep as fallback meanwhile).
- ☐ Provision `UMLS_API_KEY` only if synonym enrichment is wanted (not needed for the base corpus build); `pre_warm()` wired so the first call isn't cold.
- ☐ **Mentor/engine-team question (UPDATED):** (1) **UBERON-bodysite crashes on fresh build** — `_partition_codes` should skip foreign prefixes (COB/NCBITaxon) instead of raising; can the engine team fix? (2) EFO-disease needs a registry root (I can PR it); HANCESTRO-ancestry needs a new `ancestry` category. Are these on the roadmap before launch, or do we trim launch tuples to what builds cleanly?
- ☐ FieldSuggester read-only panel from `suggest_from_schema_mapper` output (F-12).

### W2.5 — Reference-data versioning gap (production-readiness, found 2026-06-22)

> **Gap:** only the **curated schema** (`curated_fields_*.csv`) has a real, audited update path (U9 versioning + G6 diff). The other reference/gold datasets the system curates + benchmarks **against** have no versioning and no refresh — they drift from upstream silently:
> - `data/schema/field_value_dict.json` (allowed values / LinkML enum source) — static file, edit + redeploy only.
> - `data/schema/ncit_descendants.json` (category membership) — frozen one-time snapshot.
> - `data/linkml/cbioportal_clinical.yaml` (export-gate vocab) — manual checklist transcription.
> - `data/nci_cache.json` (term→code cache) — **append-only, never expires** → serves stale codes if NCIt renames upstream.
> - Benchmark gold = cBioPortal datahub (external, pulled fresh at benchmark time — correct as-is).
> There is **no background job** refreshing any of these; the design is deliberate "pull-once then frozen until a human acts" (F-13/F-14), but these files sit **outside** the versioned bundle.

- ☐ Fold `field_value_dict.json` + `ncit_descendants.json` + `cbioportal_clinical.yaml` into the **versioned KB snapshot** (`ontology_snapshots` table + `kb_snapshot_id`), so "update reference data" = "build a new bundle, bump the pin" — same deliberate, audited, reproducible path as the engine. (`ontology_snapshots` exists but isn't wired to these files yet.)
- ☐ Add a **TTL / rebuild-on-bundle-bump** policy to `nci_cache.json` so it can't serve stale NCIt codes forever (today it only appends).
- ☐ Document the reference-data refresh procedure in the operational runbook (D8): which files, how to rebuild, how to re-snapshot.


### W3 — Frontend integration: wire prototype pages to the real backend (U1/U2) (Phase A→B)

- ☐ Typed API client against the `/api/v1` surface + auth headers; replace prototype/mock state with react-query server state.
- ☐ Wire Upload / MappingReview / Ontology / Quality / Export pages to live endpoints; auth-gated routing + RBAC-aware hiding (admin-only areas hidden from curators).
- ☐ Upload guardrails: file/type/size validation + Excel gene-symbol warning (`SEPT2` → `2-Sep`) before harmonize.

### W4 — Deployment & self-host kit (U15) + first live deploy (Phase D)

- ☐ Caddy reverse proxy + auto Let's Encrypt TLS + HSTS; Kamal deploy config (zero-downtime + one-line rollback).
- ☐ KB pre-built offline → snapshot `~/.metaharmonizer/` → R2; restore at deploy by snapshot id (never build on the VM).
- ☐ **Measure synonym-index RAM for all four launch tuples** (NCIt-disease, EFO-disease, UBERON-body-site, HANCESTRO-ancestry) before locking the CX32/8 GB floor — only NCIt-disease (~160 MB synonym) is measured today; the union of all four synonym indexes must fit one ontology worker. Record per-tuple RAM in the runbook.
- ☐ R2 bucket + domain + Resend + Sentry wired; self-host `docker-compose` + `.env.example` + `AUTH_MODE=none` path.
- ☐ First live deploy on the hosted URL; `git clone && cp .env.example .env && docker compose up` working in <30 min (U15).

### W5 — Spec v2 cleanup + scope finalize (Phase A)

- ☐ Fold confirmed decisions (active-learning scope, FAISS tuples, F-11 ownership, export gate, engine-bundle versioning) into the spec; remove resolved open-question wording; confirm Web-UI scope items reflected.

---

## 4. Definition of Done (per sprint)

A sprint counts done only when _all_ are true:

- ☐ Code merged to `main`.
- ☐ CI green (lint, typecheck, tests, engine-boundary).
- ☐ Deployed to the hosted instance URL.
- ☐ Acceptance criterion verified manually or by E2E test.
- ☐ One-line entry added to the sprint row above (date + commit SHA).

---

## 5. Live counters (update as we go)

- Current sprint: **Sprint 1** (scope sign-off). _Build-first: benchmarking deferred to Sprint 12._
- Open spec questions blocking final scope: **0**. _Web-UI bolded items resolved (Mapping history + Admin = v1; Comparison view U19 dropped as redundant; Schema Diff G6 gated on curator need; SA3.4 contract-only). FAISS tuples pending Sehyun's cBioPortal-team double-check — non-blocking. Resolved: Q6, Q8(iii), F-11 ownership + the two F-11 follow-ups (engine-bundle versioning + customization scope, now F-14), FAISS launch tuples, LinkML-as-checklist-transcription, datahub-as-D3-source._
- **Nothing blocks the build — proceed with our approach.** (1) All 4 FAISS tuples are feasibility-proven to fit one CX32 worker (§2.5) → build all 4. (2) Benchmark gold = the team's existing published `curated_meta` (self-serve, no hand-labeling; engine not tuned on them — Sehyun confirmed). The only outstanding *courtesy* items, both non-blocking: agree the 5–10 benchmark study list, and the curation-team FAISS-tuple double-check.
- **Provisional (pending curation-team confirm, not Sehyun):** Q9 retention (no-history / purge raw after harmonize) and Q9-iv admin-only study deletion. Keep these flagged until the curation-team meeting closes them.
- **Spec v2 debt:** `docs/metaharmonizerapp-requirements.tex` still carries dropped items (viewer role / P2.5, Comparison view U19, G2 unified endpoint). W5 / Sprint-1 spec v2 cut must remove them — the originally-sent contract PDF is superseded by this plan.
- Hosted-instance URL: _not yet provisioned_.
- Latest D3 / D9 report: _not yet run_.
- Federation peers: _0_.
