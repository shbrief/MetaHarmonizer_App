# Engine Adapter Architecture

**Goal:** Let the ML engine (`shbrief/MetaHarmonizer`) evolve independently of our dashboard, so an engine upgrade is a one-line dependency bump — not a 200-file rewrite.

**Audience:** Anyone joining the dashboard project. No ML background required.

**Status:** Design doc. Not yet implemented. See [§7 Migration Plan](#7-migration-plan-applied-to-our-current-repo) for the steps.

---

## Table of contents

1. [Why this doc exists — what went wrong](#1-why-this-doc-exists--what-went-wrong)
2. [The core idea in one picture](#2-the-core-idea-in-one-picture)
3. [The contract: `EngineProtocol`](#3-the-contract-engineprotocol)
4. [How we get the engine into our project (4 options)](#4-how-we-get-the-engine-into-our-project-4-options)
5. [Repository layout](#5-repository-layout)
6. [Common questions](#6-common-questions)
7. [Migration plan applied to our current repo](#7-migration-plan-applied-to-our-current-repo)
8. [Glossary](#8-glossary)

---

## 1. Why this doc exists — what went wrong

### 1.1 The situation today

Our repo (`AhmedOsamaAli/metaHarmonizer`) contains a **copy** of the ML engine at [backend/engine/](../backend/engine/). Files there look like `backend/engine/src/models/schema_mapper/engine.py`.

Our FastAPI app imports it like this:

```python
# backend/app/services/harmonizer.py — TODAY
from src.utils.ncit_match_utils import NCIClientSync
from engine.src.models.schema_mapper.engine import SchemaMapEngine
```

### 1.2 What changed upstream

Between late March and May 6, 2026, the upstream repo `shbrief/MetaHarmonizer`:

- Restructured into a pip-installable package named `metaharmonizer/` (no more `src/`)
- Added a whole `KnowledgeDb/` module (FAISS + SQLite + NCI/OLS/UMLS DB clients)
- Added `OntoMapEngine` with multi-ontology support (NCIT, MONDO, UBERON)
- Added Stage-4 LLM query rewriting + FAISS re-search
- Added content-hash isolation for user-uploaded corpora
- Added `_paths.py` so data files resolve from `METAHARMONIZER_DATA_DIR`
- Moved model identifiers into a `method_model.yaml` registry

### 1.3 Why we can't just `git pull` the changes

Because our app imports from `src.*` (the **old** path), every upstream rename breaks us:

| Upstream change | Effect on us |
|---|---|
| `src/` → `metaharmonizer/` | All our imports break |
| `src.utils.ncit_match_utils` → `metaharmonizer.KnowledgeDb.db_clients.nci_db` | Import error |
| Hard-coded `FIELD_MODEL = "all-MiniLM-L6-v2"` → YAML registry | Code that reads `config.FIELD_MODEL` works, but anything that grepped for the string breaks |

**Concrete cost of our current shape:** to pull all upstream changes today we would need to:

1. Delete `backend/engine/`
2. Rewrite ~15 import lines across `backend/app/`
3. Add a `METAHARMONIZER_DATA_DIR` env var and move data files
4. Add `pyyaml`, `faiss-cpu`, `python-dotenv`, `google-generativeai` to requirements
5. Pray nothing else broke

We get this pain **every time upstream releases**. The architecture below fixes it so future upgrades cost ~5 minutes.

### 1.4 The principle

> Depend on a **contract**, not on a **file tree**.

A contract is a Python interface (a `Protocol` or `ABC`) with method names, argument types, and return types. As long as the engine honours the contract, we don't care how its internal files are organised.

---

## 2. The core idea in one picture

### 2.1 Today (broken — path-coupled)

```
  ┌──────────────────────┐   from src.*    ┌──────────────────────────────┐
  │  backend/app routers │ ──────────────► │ backend/engine/src/          │
  │  + services          │   hard import   │ (vendored copy, frozen Apr)  │
  └──────────────────────┘                 └──────────────────────────────┘
                                                          ▲
                                                          ┊ no link
                                                          ┊ (manual copy only)
                                            ┌─────────────┴────────────────┐
                                            │ shbrief/MetaHarmonizer  main │
                                            │ (6+ weeks ahead, evolving)   │
                                            └──────────────────────────────┘
```

The dotted line means: **upstream improvements don't reach us automatically**. Someone has to manually copy files and fix imports.

### 2.2 Target (contract-coupled)

```
        ┌──────────────────────────┐
        │  backend/app/routers     │
        └────────────┬─────────────┘
                     │
                     ▼
        ┌──────────────────────────┐
        │  backend/app/services    │
        └────────────┬─────────────┘
                     │  depends on
                     ▼
        ┌──────────────────────────────────────┐
        │   EngineProtocol                     │
        │   (stable Python interface — the     │
        │    only thing app code knows about)  │
        └─────┬───────────────┬───────────────┬┘
     implements    implements        implements
              │               │               │
              ▼               ▼               ▼
   ┌──────────────────┐ ┌──────────────┐ ┌────────────────────┐
   │ MetaHarmonizer   │ │ MockEngine   │ │ FutureAdapter      │
   │ Adapter          │ │ Adapter      │ │ (different engine, │
   │ (wraps pip pkg)  │ │ (fast tests) │ │  fork, v2 …)       │
   └────────┬─────────┘ └──────────────┘ └────────────────────┘
            │
            ▼
   ┌────────────────────────────────┐         tracks
   │ pip install                    │ ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄►  shbrief/MetaHarmonizer
   │ metaharmonizer==X.Y.Z          │            (pinned, upgrade on purpose)
   └────────────────────────────────┘
```

Key shift: routers/services point at the **interface**, not at any concrete engine. Multiple implementations can plug in.

### 2.3 The rule we will enforce in CI

```
✗ from metaharmonizer.* may NOT appear in:
    backend/app/routers/
    backend/app/services/
    backend/app/repositories/
    backend/app/workers/

✓ from metaharmonizer.* may ONLY appear in:
    backend/app/engine_adapter/
```

That single grep rule keeps the architecture honest forever. Add it as a `pre-commit` hook and a CI step.

---

## 3. The contract: `EngineProtocol`

### 3.1 What goes in it

The contract lists the things **our dashboard actually needs from any engine**. Not what the engine happens to offer.

Today our dashboard needs four things:

1. Run harmonization on a DataFrame
2. Ask for the top-N alternatives for one column
3. Look up an ontology term
4. Tell us if the engine is healthy (loaded models, reachable APIs)

So the contract is small:

```python
# backend/app/engine_adapter/protocol.py
from typing import Protocol, Literal
import pandas as pd
from .types import MappingRow, Alternative, EngineHealth


class EngineProtocol(Protocol):
    """The dashboard's view of any ML engine.

    Implementations live in backend/app/engine_adapter/.
    The rest of the app depends ONLY on this protocol.
    """

    def harmonize(
        self,
        df: pd.DataFrame,
        *,
        mode: Literal["auto", "manual"] = "manual",
        top_k: int = 5,
    ) -> list[MappingRow]:
        """Map every column in `df` to a curated schema field."""
        ...

    def get_alternatives(self, column: str, n: int = 5) -> list[Alternative]:
        """Return ranked alternative matches for one column name."""
        ...

    def ontology_lookup(
        self,
        term: str,
        source: Literal["ncit", "mondo", "uberon"] = "ncit",
    ) -> list[Alternative]:
        """Look up a term in an ontology."""
        ...

    def health(self) -> EngineHealth:
        """Report engine readiness and warm caches."""
        ...
```

### 3.2 Our own DTOs (Pydantic v2)

The DTOs are **ours**. They are stable even if the underlying engine renames its fields.

```python
# backend/app/engine_adapter/types.py
from typing import Literal
from pydantic import BaseModel


class Alternative(BaseModel):
    field: str
    score: float
    source: str          # e.g. "std_exact", "semantic", "llm"


class MappingRow(BaseModel):
    query: str                          # original column name
    stage: Literal["stage1", "stage2", "stage3", "stage4", "no_match"]
    method: str                         # e.g. "std_exact", "bert", "llm"
    top_match: Alternative | None
    alternatives: list[Alternative]     # length up to top_k


class EngineHealth(BaseModel):
    ok: bool
    version: str
    loaded_models: list[str]
    warnings: list[str] = []
```

If upstream renames `match1_score` → `score_top1` tomorrow, we update **one** translation function (§3.4). The 50 places in our codebase that read `row.top_match.score` keep working.

### 3.3 The real implementation

```python
# backend/app/engine_adapter/metaharmonizer_impl.py
from functools import lru_cache
from metaharmonizer import SchemaMapEngine          # ← only file allowed to do this
from .protocol import EngineProtocol
from .types import MappingRow, Alternative, EngineHealth


class MetaHarmonizerAdapter(EngineProtocol):
    """Wraps the upstream `metaharmonizer` pip package."""

    def __init__(self, *, mode: str = "manual", top_k: int = 5):
        self._mode = mode
        self._top_k = top_k

    @lru_cache(maxsize=8)
    def _engine_for(self, csv_path: str) -> SchemaMapEngine:
        return SchemaMapEngine(
            clinical_data_path=csv_path,
            mode=self._mode,
            top_k=self._top_k,
        )

    def harmonize(self, df, *, mode="manual", top_k=5):
        # The upstream engine wants a file path. Our adapter hides that.
        tmp = _write_temp_csv(df)
        engine = self._engine_for(tmp)
        raw = engine.run_schema_mapping()
        return [self._to_dto(r) for r in raw.to_dict(orient="records")]

    def get_alternatives(self, column, n=5):
        # ... thin wrapper, returns list[Alternative]
        ...

    def ontology_lookup(self, term, source="ncit"):
        from metaharmonizer.Engine import get_ontology_engine   # lazy
        OntoMapEngine = get_ontology_engine()
        engine = OntoMapEngine(category="disease", query=[term],
                               cura_map={}, s2_method="sap-bert",
                               s2_strategy="st", test_or_prod="prod",
                               ontology_source=source)
        return [self._alt_from(r) for r in engine.run().to_dict("records")]

    def health(self):
        return EngineHealth(ok=True, version=_pkg_version(),
                            loaded_models=["all-MiniLM-L6-v2"])

    # ---- translation: ONE place to fix when upstream renames things ----
    @staticmethod
    def _to_dto(raw: dict) -> MappingRow:
        alts = [
            Alternative(field=raw[f"match{i}"],
                        score=raw[f"match{i}_score"],
                        source=raw[f"match{i}_source"])
            for i in range(1, 6)
            if raw.get(f"match{i}")
        ]
        return MappingRow(
            query=raw["query"],
            stage=raw["stage"],
            method=raw["method"],
            top_match=alts[0] if alts else None,
            alternatives=alts,
        )
```

### 3.4 The mock implementation (for fast tests)

```python
# backend/app/engine_adapter/mock_impl.py
from .protocol import EngineProtocol
from .types import MappingRow, Alternative, EngineHealth


class MockEngineAdapter(EngineProtocol):
    """Deterministic fake. No torch, no internet, no models. <1ms per call."""

    def harmonize(self, df, *, mode="manual", top_k=5):
        return [
            MappingRow(
                query=col,
                stage="stage1",
                method="mock",
                top_match=Alternative(field=col.lower(), score=0.99, source="mock"),
                alternatives=[Alternative(field=col.lower(), score=0.99, source="mock")],
            )
            for col in df.columns
        ]

    def get_alternatives(self, column, n=5):
        return [Alternative(field=f"alt_{i}", score=1 - i*0.1, source="mock")
                for i in range(n)]

    def ontology_lookup(self, term, source="ncit"):
        return [Alternative(field=f"NCIT:{abs(hash(term)) % 1000}",
                            score=0.9, source="mock")]

    def health(self):
        return EngineHealth(ok=True, version="mock-1.0", loaded_models=[])
```

### 3.5 Wiring it up (FastAPI dependency injection)

```python
# backend/app/engine_adapter/__init__.py
import os
from .protocol import EngineProtocol
from .metaharmonizer_impl import MetaHarmonizerAdapter
from .mock_impl import MockEngineAdapter


def get_engine() -> EngineProtocol:
    impl = os.getenv("ENGINE_IMPL", "metaharmonizer")
    if impl == "mock":
        return MockEngineAdapter()
    return MetaHarmonizerAdapter()
```

```python
# backend/app/routers/harmonize.py
from fastapi import APIRouter, Depends
from app.engine_adapter import get_engine, EngineProtocol

router = APIRouter()

@router.post("/harmonize")
async def harmonize(file_id: str, engine: EngineProtocol = Depends(get_engine)):
    df = load_uploaded(file_id)
    rows = engine.harmonize(df)
    return {"rows": [r.model_dump() for r in rows]}
```

Notice: **`harmonize.py` does not import `metaharmonizer` anywhere**. That's the entire point.

---

## 4. How we get the engine into our project (4 options)

| Option | One-liner | When to pick it |
|---|---|---|
| A. Pinned pip dep | `pip install "metaharmonizer @ git+https://github.com/shbrief/MetaHarmonizer@v0.4.0"` | **Default.** Upstream releases or tags exist. |
| B. Git submodule | `git submodule add https://github.com/shbrief/MetaHarmonizer vendor/MetaHarmonizer` then `pip install -e vendor/MetaHarmonizer` | Upstream rarely tags; we need to carry small patches. |
| C. Hard fork | Fork to `cbioportal/MetaHarmonizer-engine`; we maintain it | Upstream stalls or refuses needed changes. |
| D. Vendored copy | Copy files into our repo | Emergency hotfix only. This is what we have now and it's the problem. |

### 4.1 Option A in detail (recommended)

`backend/pyproject.toml`:

```toml
[project]
name = "metaharmonizer-dashboard-backend"
dependencies = [
    "fastapi>=0.110",
    "pydantic>=2.6",
    "sqlalchemy>=2.0",
    # The engine, pinned to a specific upstream commit:
    "metaharmonizer @ git+https://github.com/shbrief/MetaHarmonizer@792eb75d4d81cb90b6480bf4e6226b781f402b11",
]
```

Pin to a **commit SHA** (not just `main`). Why?

- A SHA is immutable. The build is reproducible forever.
- A branch (`main`) is mutable. CI passes today, fails tomorrow with no code change on our side.

Upgrade procedure:

```powershell
# 1. Find the new commit (e.g. release tag)
# 2. Bump SHA in pyproject.toml
# 3. Run integration tests
pytest backend/tests/integration -k engine
# 4. Open PR, review diff, merge
```

### 4.2 Option B in detail (submodule)

```powershell
git submodule add https://github.com/shbrief/MetaHarmonizer vendor/MetaHarmonizer
cd vendor/MetaHarmonizer
git checkout v0.4.0
cd ../..
git add .gitmodules vendor/MetaHarmonizer
```

`pyproject.toml`:

```toml
dependencies = [ "metaharmonizer @ file://./vendor/MetaHarmonizer" ]
```

Use this if we need to patch upstream locally (`git apply our-patches/*.patch` after submodule update).

### 4.3 Option D — what we must stop doing

Do **not** copy upstream files into `backend/engine/`. That's the trap we are in.

---

## 5. Repository layout

```
metaHarmonizer/                              # this dashboard repo
│
├── backend/
│   ├── pyproject.toml                       # ONE place for deps incl. engine pin
│   ├── app/
│   │   ├── main.py                          # FastAPI app
│   │   ├── routers/                         # HTTP only — no engine imports
│   │   │   ├── harmonize.py
│   │   │   ├── mappings.py
│   │   │   ├── ontology.py
│   │   │   ├── quality.py
│   │   │   └── export.py
│   │   ├── services/                        # business logic — no engine imports
│   │   │   ├── harmonizer.py
│   │   │   ├── exporter.py
│   │   │   └── analytics.py
│   │   ├── engine_adapter/                  # ★ THE ONLY PLACE THAT IMPORTS metaharmonizer
│   │   │   ├── __init__.py                  # get_engine() factory
│   │   │   ├── protocol.py                  # EngineProtocol (stable)
│   │   │   ├── types.py                     # Our DTOs
│   │   │   ├── metaharmonizer_impl.py       # Real adapter
│   │   │   ├── mock_impl.py                 # Test double
│   │   │   └── cache.py                     # Singleton + Redis cache
│   │   ├── repositories/                    # SQLAlchemy data access
│   │   ├── db/                              # ORM models, Alembic migrations
│   │   └── workers/                         # arq/Celery background tasks
│   ├── tests/
│   │   ├── unit/                            # use MockEngineAdapter — fast
│   │   └── integration/                     # opt-in; uses real engine
│   └── data/                                # METAHARMONIZER_DATA_DIR target
│
├── frontend/                                # React SPA (unchanged)
│
├── docs/
│   ├── adr/                                 # Architecture Decision Records
│   │   ├── 0001-engine-as-pinned-dependency.md
│   │   └── 0002-engine-adapter-pattern.md
│   ├── engine-adapter-architecture.md       # THIS FILE
│   └── engine-contract.md                   # Versioning rules for EngineProtocol
│
├── .github/workflows/
│   ├── ci.yml                               # unit tests (mocked) — fast, every PR
│   ├── engine-integration.yml               # real engine, current pin — on PR
│   ├── engine-compat.yml                    # nightly: real engine @ main — informational
│   └── engine-bump.yml                      # weekly bot: open PR when upstream tags
│
├── compose.yml                              # postgres + redis + api + worker
├── .pre-commit-config.yaml                  # enforces import-boundary rule
└── README.md
```

### 5.1 The boundary-enforcement hook

`.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: no-engine-leaks
      name: forbid metaharmonizer imports outside engine_adapter
      entry: scripts/check_engine_boundary.py
      language: python
      files: ^backend/app/(routers|services|repositories|workers)/
```

`scripts/check_engine_boundary.py`:

```python
#!/usr/bin/env python3
import sys, re, pathlib
bad = re.compile(r"^\s*(from|import)\s+metaharmonizer")
errors = []
for path in map(pathlib.Path, sys.argv[1:]):
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if bad.match(line):
            errors.append(f"{path}:{i}: {line.strip()}")
if errors:
    print("Engine boundary violation — only engine_adapter/ may import metaharmonizer:")
    print("\n".join(errors))
    sys.exit(1)
```

Now nobody can accidentally re-couple us to engine internals.

### 5.2 The three CI workflows in one minute

| Workflow | When | What it does | Why |
|---|---|---|---|
| `ci.yml` | Every PR | Unit tests with `MockEngineAdapter` | Fast feedback (~30 s), no torch download |
| `engine-integration.yml` | Every PR | Integration tests with the pinned engine version | Confirms our adapter still maps upstream output correctly |
| `engine-compat.yml` | Nightly | Same integration tests against `metaharmonizer @ main` | Early warning if upstream changes the contract |
| `engine-bump.yml` | Weekly | Bot opens PR bumping the engine SHA to latest tag | Keeps us current without manual chore |

---

## 6. Common questions

### Q1. "Isn't this over-engineering for a small project?"

No, because we already paid the price for **not** having it. Today's situation — upstream is 6 weeks ahead and we can't pull — is exactly the failure mode this design prevents. The adapter is ~150 lines of Python.

### Q2. "What if I need a feature that isn't in `EngineProtocol`?"

Add it. The contract is ours to evolve. Process:

1. Open a PR that adds the method to `protocol.py` and implements it in **both** `MetaHarmonizerAdapter` and `MockEngineAdapter`.
2. Document the change in `docs/engine-contract.md` (semver: minor for additions, major for breaks).
3. Then use it in services/routers.

### Q3. "What if upstream removes a feature we use?"

The adapter shields the rest of the codebase. We have three responses:

1. **Polyfill in the adapter** — reimplement the missing piece in `metaharmonizer_impl.py` (or a sibling helper).
2. **Pin to the last good version** in `pyproject.toml` until we either polyfill or drop the feature.
3. **Negotiate upstream** — open an issue on `shbrief/MetaHarmonizer` since we are a known consumer.

In all three cases, **routers and services don't change**.

### Q4. "How do I test code that uses the engine?"

Inject the mock:

```python
# backend/tests/unit/test_harmonize_router.py
from fastapi.testclient import TestClient
from app.main import app
from app.engine_adapter import get_engine
from app.engine_adapter.mock_impl import MockEngineAdapter

app.dependency_overrides[get_engine] = lambda: MockEngineAdapter()
client = TestClient(app)

def test_harmonize_returns_one_row_per_column():
    r = client.post("/harmonize", json={"file_id": "fake"})
    assert r.status_code == 200
    assert len(r.json()["rows"]) == 3   # because our test CSV has 3 columns
```

No torch, no model download, no network. Runs in milliseconds.

### Q5. "How does the engine get its data files (curated schema, corpus, NCI cache)?"

Upstream resolves them via the `METAHARMONIZER_DATA_DIR` env var. We set it in our compose file:

```yaml
# compose.yml
services:
  api:
    environment:
      METAHARMONIZER_DATA_DIR: /app/backend/data
    volumes:
      - ./backend/data:/app/backend/data
```

Our data dir contains exactly what upstream expects: `schema/curated_fields.csv`, `schema/field_value_dict.json`, `corpus/...`, etc. No code changes needed when upstream relocates files inside the package.

### Q6. "What about the LLM (Stage 4)?"

Same model — gate by env var, not by code path:

```python
# backend/app/engine_adapter/metaharmonizer_impl.py
def __init__(self, *, enable_llm: bool | None = None, ...):
    self._mode = "auto" if (enable_llm ?? bool(os.getenv("GEMINI_API_KEY"))) else "manual"
```

Production sets `GEMINI_API_KEY`; CI doesn't. The mock doesn't care.

### Q7. "Should the adapter live in a separate package?"

Not yet. Keep it inside `backend/app/engine_adapter/` for now. Extract to a separate package (`metaharmonizer-dashboard-engine-adapter`) only if:

- The frontend ever needs to embed engine logic (it shouldn't)
- A second backend (e.g. a CLI tool) reuses the same adapter
- The team explicitly votes to do so

YAGNI applies.

### Q8. "How is this different from what we have at `backend/engine/`?"

| | Today (`backend/engine/`) | Target (`engine_adapter/`) |
|---|---|---|
| What lives there | Copied engine source files | ~150 lines of glue code we wrote |
| Imports of `from src.*` outside it | Many (routers, services) | Zero |
| Upgrade upstream | Manual file copy + import rewrites | Bump one SHA in `pyproject.toml` |
| Swap engine implementation | Impossible without rewriting routers | Set `ENGINE_IMPL=other` env var |
| Test without torch | Impossible | `MockEngineAdapter` |

### Q9. "Does this slow down development?"

Initial cost: ~1 day to write the adapter and rewrite imports. Recurring cost: near zero — upgrades become trivial, tests get faster, onboarding gets clearer. Net positive after the first upgrade cycle.

### Q10. "What if I want to debug into the engine?"

Two paths:

- **Option A users:** `pip install -e ./vendor/MetaHarmonizer` instead of the git URL, set breakpoints in upstream files.
- **Anyone:** stick a `print()` or `logger.debug()` in the adapter and read the raw upstream output before translation.

The adapter is also the obvious place to log every engine call for replay/debugging.

### Q11. "How do I handle breaking changes in upstream's output schema?"

Three layers protect us:

1. **The translation function** (`_to_dto` in `metaharmonizer_impl.py`) is the only place that touches raw upstream dicts. Update it and you're done.
2. **Integration tests** snapshot the translated output. If upstream changes a field name and we forget to update the translation, the test fails loudly.
3. **`engine-compat.yml`** runs nightly against `main` so we catch breaks within ~24 hours.

### Q12. "When should I bypass the adapter?"

Almost never. Two legitimate cases:

- One-off evaluation scripts in `scripts/` or `notebooks/` — these are not production code.
- The benchmarking work in Phase 1 of the proposal — comparing engine versions side-by-side may temporarily need to import both directly.

Even then, prefer wrapping each version behind its own adapter and comparing through the protocol.

---

## 7. Migration plan applied to our current repo

> **Status (2026-05-22):** All six steps below are complete. The dashboard
> now runs against the pip-installed upstream `metaharmonizer` package via
> `MetaHarmonizerAdapter`; `backend/engine/`, `backend/engine_upstream/`
> and `VendoredAdapter` have been removed. The checklist is preserved here
> as a record of the migration sequence — future engine swaps follow the
> same shape.

Each step was **independently mergeable**. None broke the running app.

### Step 1 — Create the seam (no behaviour change)

- [x] Add `backend/app/engine_adapter/{__init__.py,protocol.py,types.py}`.
- [x] Add `VendoredAdapter` in `engine_adapter/vendored_impl.py` that wraps today's `backend/engine/` exactly as it is today.
- [x] Add `get_engine()` returning `VendoredAdapter()`.
- [x] Rewrite [backend/app/services/harmonizer.py](../backend/app/services/harmonizer.py) and the routers to depend on `EngineProtocol` via `Depends(get_engine)`.
- [x] App behaviour is identical. CI green.

### Step 2 — Add the mock

- [x] Add `MockEngineAdapter`.
- [x] Switch `backend/tests/` to use it via `app.dependency_overrides`.
- [x] CI gets faster.

### Step 3 — Add the upstream adapter behind a flag

- [x] Add `metaharmonizer @ git+...@<sha>` to `backend/requirements.txt` (commented at first).
- [x] Implement `MetaHarmonizerAdapter`.
- [x] `get_engine()` returns it when `ENGINE_IMPL=metaharmonizer`; defaulted to `vendored` for the rollout window.
- [x] Run both adapters against [metadata_samples/new_meta.csv](../metadata_samples/new_meta.csv); diff the outputs (Phase-1 benchmarking deliverable E1).

### Step 4 — Flip the default

- [x] Default `ENGINE_IMPL=metaharmonizer`.
- [x] Smoke test passes (`schema_rows: 141`, semantic matching, health green).
- [x] Auto-point `METAHARMONIZER_DATA_DIR` at `backend/data/` when the host doesn't set it.

### Step 5 — Delete the vendored copy

- [x] Move schema files from `backend/engine/data/schema/` → `backend/data/schema/`.
- [x] Slim `backend/app/services/harmonizer.py` down to the ontology / NCI / `generate_study_id` helpers.
- [x] Delete `backend/engine/`.
- [x] Delete `backend/engine_upstream/` (the staging clone).
- [x] Delete `backend/app/engine_adapter/vendored_impl.py` and the `vendored` branch in `__init__.py`.

### Step 6 — Lock the door

- [x] Add `scripts/check_engine_boundary.py`.
- [x] Add `.pre-commit-config.yaml` hook.
- [x] Add `.github/workflows/engine-boundary.yml`.
- [x] Add ADR document at `docs/adr/0001-engine-adapter-pattern.md`.

---

## 8. Glossary

| Term | Meaning |
|---|---|
| Adapter | A small object that translates between two interfaces. Here: between our `EngineProtocol` and the upstream `metaharmonizer` API. |
| ADR | Architecture Decision Record. A short markdown file explaining *why* we made a structural choice. Lives in `docs/adr/`. |
| Contract | The set of method names, types, and behaviour an interface promises. Our contract is `EngineProtocol`. |
| Dependency injection | Passing collaborators in from outside instead of constructing them inline. FastAPI's `Depends(get_engine)` is DI. |
| DTO | Data Transfer Object. A typed payload our app passes around. Pydantic models here. |
| Pin | Lock a dependency to an exact version (or commit SHA) so builds are reproducible. |
| Protocol | A Python typing feature describing what methods an object must have, without inheritance. Like a TypeScript `interface`. |
| Seam | A place in the code where you can substitute one implementation for another without changing callers. The adapter is our seam. |
| Vendoring | Copying a library's source into your repo. Easy to do, painful to maintain. What we're moving away from. |

---

## See also

- [GSoC proposal §1.4.5 — ML Engine Adapter](../GSoC_Proposal.md) (if present locally)
- Upstream engine: <https://github.com/shbrief/MetaHarmonizer>
- Our prototype repo: <https://github.com/AhmedOsamaAli/metaHarmonizer>
