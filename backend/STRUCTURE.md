# Backend project structure

> The target layout for the FastAPI backend. Folders marked **(scaffold)** exist as empty
> packages now and fill in during the sprint noted. Architecture rationale: [docs/adr/0002-system-architecture.md](../docs/adr/0002-system-architecture.md).

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory, middleware, router mounting
│   ├── core/                # (scaffold) settings, security, logging, errors, pagination — S2/S3
│   ├── db/                  # (scaffold) SQLAlchemy base, session, models/ — S2
│   ├── repositories/        # (scaffold) data-access layer, one repo per aggregate — S2
│   ├── schemas/             # (scaffold) Pydantic request/response DTOs — S2+
│   ├── workers/             # (scaffold) arq tasks + job lifecycle — S4
│   ├── routers/             # HTTP only — no engine, no direct DB
│   │   ├── harmonize.py  mappings.py  ontology.py  quality.py  export.py
│   ├── services/            # business logic — no engine imports, no raw SQL
│   │   ├── harmonizer.py  exporter.py  analytics.py
│   ├── engine_adapter/      # ★ ONLY place that imports `metaharmonizer` (ADR 0001)
│   │   ├── protocol.py  types.py  metaharmonizer_impl.py  mock_impl.py  __init__.py
│   ├── database.py          # LEGACY prototype SQLite — replaced by db/ in Sprint 2
│   └── models.py            # LEGACY prototype models — replaced by db/models/ + schemas/
├── alembic/                 # (added S2) migrations; alembic.ini at backend/
├── data/                    # METAHARMONIZER_DATA_DIR target (schema/value dicts, uploads)
├── tests/
│   ├── unit/                # MockEngineAdapter — fast, no torch/network
│   ├── contract/            # error envelope, pagination, idempotency, 409, limits (S2)
│   └── integration/         # real engine + real Postgres (opt-in)
├── vendor/                  # pinned metaharmonizer wheel
└── requirements.txt
```

## Layering rules (enforced by review + the engine-boundary CI check)

```
routers  →  services  →  repositories  →  db
   │            │                            
   └────────────┴──────────►  engine_adapter  (only services/workers call it)
```

- **routers**: parse/validate (schemas), call services, shape responses. No SQL, no engine.
- **services**: business logic. No raw SQL (use repositories), no `metaharmonizer` import.
- **repositories**: all SQL/ORM. No engine.
- **workers**: run the engine via the adapter; write results via repositories.
- **engine_adapter**: the only importer of the upstream wheel (ADR 0001).
- **core**: depended on by everyone; depends on nothing app-specific.

## Running locally

**With Docker** (any machine that has it): `make up` → stack on `:8000` (API) / `:8080` (Caddy).

**Without Docker** (this dev machine — no WSL2/admin, see [ADR 0002](../docs/adr/0002-system-architecture.md)):
portable Postgres + Redis run from `%LOCALAPPDATA%\mh-dev` via the helper script — no admin needed.

```powershell
./scripts/dev_services.ps1 start     # start portable Postgres (5433) + Redis (6380)
./scripts/dev_services.ps1 status    # check
# .env already points DATABASE_URL -> :5433 and REDIS_URL -> :6380
cd backend; .\.venv\Scripts\uvicorn.exe app.main:app --reload
./scripts/dev_services.ps1 stop      # when done
```

Both paths serve the same app and pass `/healthz` + `/readyz`.

## Migration note (prototype → target)

`app/database.py` (SQLite) and `app/models.py` are the current prototype. Sprint 2 introduces
`db/` (async SQLAlchemy + Postgres) + `repositories/` and migrates data across, then the legacy
files are removed. Until then both coexist; new code targets the new layout.
