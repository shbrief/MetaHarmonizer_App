# MetaHarmonizer — TODO

> Working list of follow-ups, evaluations, and decisions to come back to.
> Keep this file local-only / gitignored if it's personal.

---

## Engineering follow-ups

### Consolidate domain data: SQLite → Postgres (planned, PROJECT_PLAN Sprint 2)

**Status:** Tracked. Curation data still lives in prototype SQLite; target is a single Postgres datastore.

- Today there are **two datastores**: Postgres holds auth/ops (`users`, `sessions`, `api_tokens`, `job_runs`, `job_failures`) while a prototype **SQLite** file (`backend/data/metaharmonizer.db`, via `app/database.py`) holds the domain data (`studies`, `mappings`, `ontology_mappings`, `audit_log`).
- **Target:** move `studies` / `mappings` / `mapping_versions` / `ontology_mappings` / `audit_events` into Postgres (ORM models + Alembic migrations already scoped in PROJECT_PLAN.md line 225), so there's one datastore with migrations, nightly dumps, and backups.
- **Work:** port `app/database.py` SQL to SQLAlchemy repositories; one-shot migration of existing SQLite rows → Postgres; switch routers/services to the new repos; delete the SQLite layer.
- **Note:** the *other* SQLite — upstream `metaharmonizer`'s `KnowledgeDb` (FAISS + SQLite) — stays; that's the engine's internal ontology store, not app data.

---

## Mentor follow-ups

### PEPhub evaluation (asked by Sehyun)

**Status:** Investigated — recommend *not* adopting as backend; keep `eido` on the radar.

#### Summary
PEPhub (https://github.com/pepkit/pephub) is a FastAPI + Postgres + Qdrant **registry** for sample metadata already in PEP format (`project_config.yaml + sample_table.csv`). It's a *publish/discover* system. MetaHarmonizer is a *transform/curate* system that turns messy CSVs into cBioPortal-formatted metadata. Different domain, different data model, different UX — same building blocks underneath (FastAPI, Postgres, sentence transformers).

#### Reject (backend pieces)
- **`pepdbagent`** — Postgres layer modeled around `namespace / project / sample / view`; wrong shape for our `study / mapping / ontology_mapping / audit_event` domain. Wedging our model in would break the per-mapping audit trail.
- **PEPhub's Qdrant deployment** — Their index contains PEP project-description embeddings (unrelated content); can't share it. We may eventually need a vector index for value-level NCIT/MONDO/UBERON resolution and cross-study similarity (NCIT alone is ~170K terms; upstream `metaharmonizer` already uses FAISS for some of this). If/when we outgrow FAISS, evaluate Qdrant / Milvus / pgvector on their own merits, independently of PEPhub.
- **`pephubclient` as primary output target** — Pushes PEPs to a PEPhub instance, but the GSoC deliverable is cBioPortal-format export, and cBioPortal's data loader doesn't consume PEPs.

#### Keep / consider
- **`eido` for final-output schema validation (Phase 2 polish).** Today the adapter validates accepted mappings against `curated_fields_source_latest_with_flags.csv` in custom code. Express the cBioPortal clinical-sample schema as a JSON Schema and run `eido` over the harmonized table before export. Wins: standard error messages, pluggable filters, schema reusable across R/Python/CLI. Small dep, BSD-2, low risk.
- **Optional long-term:** PEPhub as a *secondary* publishing destination alongside cBioPortal — only if outputs landing in PEPhub is something the mentor team would want. Additive, no impact on core pipeline.

#### Where the "37 fields = numpy is fine" claim does and doesn't hold
- True for **column → canonical-field** matching (37 targets, ~57 KB total — numpy beats a vector DB).
- False at **value-level ontology resolution** (NCIT ~170K, MONDO ~25K, UBERON ~17K) and **cross-study similarity** — those are real vector-search problems and warrant a proper index.

#### Mentor reply (draft to send)
> Subject: Re: PEPhub for the MetaHarmonizer backend
>
> Hi Sehyun,
>
> Spent time digging into `pepkit/pephub` and the surrounding libraries (`peppy`, `pepdbagent`, `eido`, `pephubclient`). Short version: PEPhub solves a different problem than the harmonization dashboard, so I wouldn't adopt it as the backend, but `eido` is worth keeping on the list for schema validation. Reasoning below.
>
> **What PEPhub is.** A FastAPI + Postgres + Qdrant **registry** where users upload, version, validate, and share sample metadata that's *already in PEP format* (`project_config.yaml + sample_table.csv`). Its "semantic search" indexes PEP descriptions so you can find existing projects in the registry — it doesn't match column names to a canonical schema or resolve values to ontology terms.
>
> **What we're building.** A pipeline + curator workflow that turns *messy* CSVs into harmonized, cBioPortal-formatted metadata: multi-stage column mapping with confidence scores, per-mapping accept/reject/edit with an audit trail, value-level NCIT ontology resolution, and export to cBioPortal's clinical-sample TSV.
>
> **Where they overlap.** Both use FastAPI + Postgres + sentence transformers. None of those choices would change either way — same building blocks, different domain logic on top.
>
> **What I'd reject from pepkit and why (backend pieces).**
> - `pepdbagent` (Postgres layer). Its tables model `namespace / project / sample / view`, which is the wrong shape for our `study / mapping / ontology_mapping / audit_event` domain. Wedging our model into it would break the per-mapping audit trail that auditors need.
> - PEPhub's Qdrant deployment. We may eventually need a vector index — value-level ontology resolution against NCIT (~170K terms), MONDO, UBERON, and cross-study similarity search are all real vector-search problems, and the upstream engine already uses FAISS for some of them. But PEPhub's Qdrant is loaded with PEP project-description embeddings, which is unrelated content; we can't share their index. If/when we outgrow FAISS, we'd evaluate Qdrant/Milvus/pgvector on their own merits, independently of PEPhub.
> - `pephubclient` as a primary output target. Pushes PEPs to a PEPhub instance, but the GSoC deliverable is cBioPortal-format export, and cBioPortal's data loader doesn't consume PEPs.
>
> **What I'd consider keeping.**
> - `eido` for final-output schema validation. Today the adapter validates accepted mappings against `curated_fields_source_latest_with_flags.csv` in custom code. Expressing the cBioPortal clinical-sample schema as a JSON Schema and running `eido` over the harmonized table before export would give us standard error messages, pluggable filters, and a schema that's reusable across R/Python/CLI. Small dep, BSD-2, low risk. Phase 2 polish, not Phase 1 work.
> - Optional, long-term: PEPhub as a secondary publishing destination alongside cBioPortal — after a study is harmonized and exported as cBioPortal TSV, also push a PEP-formatted copy to a PEPhub instance for the broader pepkit ecosystem. Pure-additive, doesn't touch the core pipeline. Worth it only if you'd actually want our outputs landing in PEPhub.
>
> **Bottom line.** PEPhub is a *publish/discover* system for clean PEPs; our project is a *transform/curate* system that produces cBioPortal-formatted metadata from messy CSVs. The data models and operational shape don't line up, so adopting it as the backend would mean fighting an abstraction built for a different domain. I'd keep our FastAPI + SQLite→Postgres stack, leave room for FAISS (or eventually a real vector DB) for value-level ontology search, and optionally pull in `eido` for validation. Happy to dig further if there's a specific PEPhub capability you had in mind that I might have missed.
>
> Ahmed

#### Action items
- [ ] Send the reply above to Sehyun.
- [ ] If they approve, add `eido`-based validation as a Phase 2 task (after the cBioPortal clinical-sample schema is expressed as JSON Schema).
- [ ] Confirm whether PEPhub-as-publishing-destination is in or out of scope before committing to it.
