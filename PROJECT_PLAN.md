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
| ☐ G1   | Federation of two-tier KB      | **Federation-lite**: signed JSON `/federation/export` + `/federation/import` REST. No live multi-master.                                                                                                                                                                                                              | Not started                   |
| — G2   | Unified `POST /harmonize`      | **Out** (Sehyun confirmed). Existing per-route REST stays.                                                                                                                                                                                                                                                            | Out of scope                  |
| ☐ G3   | MCP tools                      | Standalone `metaharmonizer-mcp` PyPI package, three tools, stdio + SSE.                                                                                                                                                                                                                                               | Not started                   |
| ☐ G4   | Versioned audit-record layer   | `audit_events` + `mapping_versions` tables, append-only, queryable JSON.                                                                                                                                                                                                                                              | Designed, not built           |
| ✅ G5  | Accept / reject / edit + batch | Already in prototype Mapping Review page.                                                                                                                                                                                                                                                                             | Done                          |
| ☐ G6   | Side-by-side schema diff       | **Low priority.** (A) schema-vs-schema diff — what changed in the target `curated_fields` CSV (cheap, ships with versioning) is the committed part; (B) study-impact re-score and curator-initiated "adopt new schema" UX are **stretch / build only if curators ask**. Versioning + admin promotion ship regardless. | Not started (A) / Stretch (B) |
| ☐ G7   | Active-learning ranking        | Confidence-asc sort + margin-sampling re-rank. Scope: **per-study / cross-curator** (Sehyun confirmed Q6; all three scopes share one code path, this is the default).                                                                                                                                                 | Partial                       |
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
| ☐ U6   | Compare a study against a new schema: target-dictionary diff (A) + study-impact re-score (B) (G6)                                                                                                                                     | Not started     |
| ☐ U7   | Low-confidence-first ranking, dynamic re-rank (G7)                                                                                                                                                                                    | Partial         |
| ☐ U8   | Three exports per study (harmonized CSV with value-level rewrite, cBioPortal TSV, audit JSON)                                                                                                                                         | Partial         |
| ☐ U9   | Admin uploads new curated-fields CSV (schema version)                                                                                                                                                                                 | Not started     |
| ☐ U10  | Admin manages users (promote/demote/disable, revoke tokens)                                                                                                                                                                           | Not started     |
| ☐ U11  | Auditor query "who accepted this mapping / state on date X"                                                                                                                                                                           | Not started     |
| ☐ U12  | Batch consumer `POST /harmonize` w/ scoped API token                                                                                                                                                                                  | Partial         |
| — U13  | PEPhub side of inverse-mode                                                                                                                                                                                                           | **Out**         |
| ☐ U14  | AI assistant uses MCP tool                                                                                                                                                                                                            | Not started     |
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
- ☑ **Decided by us (Q9 retention — no history):** curators don't need historical copies of raw uploads or generated exports. **Keep no history of files.** A re-curation = a fresh re-upload (faster the second time because the prior decisions are already in the KB + audit log). The valuable data — confirmed mappings + append-only audit — is **always kept** in Postgres. **Sequencing:** raw upload is retained only while a study is being worked; once Sprint 9 persists the harmonized output table, the raw upload is purged right after a successful harmonize (export then regenerates from the stored output, not the raw file). **Session safety:** because all accept/reject/edit work is persisted server-side as the curator goes, closing/reopening a tab never loses progress — no browser-held state. Supersedes the age-based purge stub.
- ☐ **Still pending:** confirm the four FAISS tuples with the cBioPortal team (Sehyun to check); Web-UI-bolded items.
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
- ☐ Multi-file ZIP packer producing `data_clinical_sample.txt` + `meta_study.txt` + `meta_clinical_sample.txt` + case-list files + `LICENSE`.
- ☐ Required column injection (`PATIENT_ID`/`SAMPLE_ID` rules), `0:`/`1:` survival prefixing, banned-columns blocklist applied (per §1.5).
- ☐ LinkML schema authored as a verbatim transcription of the QC checklist + `survivalStatusVocabularies.txt` (no new rules).
- ☐ LinkML validator gate before export — fail fast with actionable errors mapping back to checklist line.
- ☐ Final gate: invoke `validation/validateData.py` from `cBioPortal/datahub-study-curation-tools` as the source of truth on our generated ZIP.
- ☐ OncoTree → `CANCER_TYPE` / `CANCER_TYPE_DETAILED` derivation in the exporter (rules from `oncotree-code-converter`).
- ☐ UTF-8/LF + no-smart-quotes enforcement; `data_cna_hg19.seg` filename rule; hg38 reference-genome field.
- ☐ E2E: feed the ZIP to actual `validateData.py` on CI against a representative datahub study.

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

- ☐ **D3/D9 — Production Readiness Benchmark** on the agreed 5–10 datahub studies (deferred here per the sequencing principle): label ground truth (we draft, Sehyun verifies), then capture D-A accuracy/calibration, D-B latency, D-C resources, D-D failure modes, D-E edge cases, D-F threshold sweep on the **final shipped system**.
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

- ☐ Implement `adapter.map_values()` wrapping `OntoMapEngine(category, query, …).run()`; verify ontology output columns from source; normalize to our DTOs.
- ☐ Retire the dashboard-side `_STATIC_NCIT` + `nci_cache.json` + `ONTOLOGY_MAP` fallback chain.
- ☐ Provision `UMLS_API_KEY` for first-run KB build (hosted); `pre_warm()` wired so the first call isn't cold.
- ☐ FieldSuggester read-only panel from `suggest_from_schema_mapper` output (F-12).

### W3 — Frontend integration: wire prototype pages to the real backend (U1/U2) (Phase A→B)

- ☐ Typed API client against the `/api/v1` surface + auth headers; replace prototype/mock state with react-query server state.
- ☐ Wire Upload / MappingReview / Ontology / Quality / Export pages to live endpoints; auth-gated routing + RBAC-aware hiding (admin-only areas hidden from curators).
- ☐ Upload guardrails: file/type/size validation + Excel gene-symbol warning (`SEPT2` → `2-Sep`) before harmonize.

### W4 — Deployment & self-host kit (U15) + first live deploy (Phase D)

- ☐ Caddy reverse proxy + auto Let's Encrypt TLS + HSTS; Kamal deploy config (zero-downtime + one-line rollback).
- ☐ KB pre-built offline → snapshot `~/.metaharmonizer/` → R2; restore at deploy by snapshot id (never build on the VM).
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
- Open spec questions blocking final scope: **1** — Web-UI bolded items. _(FAISS tuples pending Sehyun's cBioPortal-team double-check, not blocking.) Resolved: Q6, Q8(iii), F-11 ownership + the two F-11 follow-ups (engine-bundle versioning + customization scope, now F-14), FAISS launch tuples, LinkML-as-checklist-transcription, datahub-as-D3-source, Q9 retention (no history; re-upload to re-curate)._
- Hosted-instance URL: _not yet provisioned_.
- Latest D3 / D9 report: _not yet run_.
- Federation peers: _0_.
