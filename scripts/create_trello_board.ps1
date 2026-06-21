<#
.SYNOPSIS
  Build the MetaHarmonizer SA3.1 Trello board (Jira-like kanban).
.DESCRIPTION
  Creates a board, columns, phase labels, and one card per deliverable with its
  tasks as a checklist. Build-first order; no coordination/engine-team cards.
  Reads credentials from environment variables so secrets never appear in code/chat:
      $env:TRELLO_KEY   = "<api key>"
      $env:TRELLO_TOKEN = "<token>"
  Get them at https://trello.com/power-ups/admin  (create a Power-Up -> API key + Token).
.EXAMPLE
  ./scripts/create_trello_board.ps1
#>
param(
  [string]$BoardName = "MetaHarmonizer SA3.1"
)
$ErrorActionPreference = "Stop"

$key   = $env:TRELLO_KEY
$token = $env:TRELLO_TOKEN
if (-not $key -or -not $token) {
  throw "Set `$env:TRELLO_KEY and `$env:TRELLO_TOKEN first (see script header)."
}

$base = "https://api.trello.com/1"
function Esc($s){ [uri]::EscapeDataString($s) }
function T-Post($path, $params) {
  $qs = ($params.GetEnumerator() | ForEach-Object { "$($_.Key)=$(Esc([string]$_.Value))" }) -join "&"
  $uri = "$base/$path`?$qs&key=$key&token=$token"
  Invoke-RestMethod -Method Post -Uri $uri
}

Write-Host "Creating board '$BoardName'..." -ForegroundColor Cyan
$board = T-Post "boards" @{ name=$BoardName; defaultLists="false"; prefs_permissionLevel="org" }
$bid = $board.id
Write-Host "  board id $bid" -ForegroundColor DarkGray
Write-Host "  URL: $($board.url)" -ForegroundColor Green

# ---- columns (lists), left to right ----
$listNames = @("Backlog","Todo","In Progress","Blocked","In Review","Done")
$lists = @{}
$pos = 1
foreach ($n in $listNames) {
  $l = T-Post "lists" @{ name=$n; idBoard=$bid; pos=($pos*1000) }
  $lists[$n] = $l.id
  $pos++
}
$backlog = $lists["Backlog"]
Write-Host "  columns: $($listNames -join ' | ')" -ForegroundColor DarkGray

# ---- phase labels ----
$labelDefs = @{
  "Phase A" = "blue"; "Phase B" = "green"; "Phase C" = "purple";
  "Phase D" = "orange"; "Phase E" = "black"
}
$labels = @{}
foreach ($k in $labelDefs.Keys) {
  $lab = T-Post "labels" @{ name=$k; color=$labelDefs[$k]; idBoard=$bid }
  $labels[$k] = $lab.id
}

# ---- deliverables (build-first; no coordination/engine cards) ----
$cards = @()
$cards += @{ phase="Phase A"; title="Sprint 2 — Persistence + audit foundation + operational contracts (G4)";
  goal="Every accept/reject/edit writes an append-only audit row; all operational contracts wired into the foundation.";
  acc="Audit rows queryable; contract tests prove envelope/pagination/idempotency/409/limits; healthz+readyz green; settings-check fails on missing env.";
  trace="G4";
  tasks=@(
    "Postgres schema (users/studies/mappings/mapping_versions/audit_events/versions/sessions/tokens/job_runs/idempotency_keys)",
    "Alembic migrations from clean state",
    "Append-only enforcement on audit_events (no DELETE; revoke on role)",
    "Two-axis pin (schema_version_id, ontology_snapshot_id) through harmonize flow",
    "Optimistic-locking version column + 409 on stale UPDATE",
    "Migrate prototype SQLite -> Postgres",
    "Pydantic Settings + fail-fast on missing env; JWT_SECRET >= 32 bytes",
    "Unified error envelope + request_id in logs",
    "Cursor pagination + Idempotency-Key middleware + boundary limits",
    "Structured logs + healthz/readyz + admin metrics + Sentry init + retention cron stub"
  )}
$cards += @{ phase="Phase A"; title="Sprint 3 — Auth + RBAC + session model";
  goal="Real login + three roles enforced in REST+UI with the S1-S7 session defaults.";
  acc="E2E covers all RBAC rows; cross-browser session revoke -> next request 401.";
  trace="U10, U18";
  tasks=@(
    "Email/password + JWT access/refresh (15min / 30d sliding)",
    "Refresh cookie (httpOnly/Secure/SameSite) + in-memory access token + silent refresh",
    "WS ticket endpoint (30s Redis nonce)",
    "Frontend state: zustand + react-query",
    "CSRF double-submit on cookie-authed routes",
    "sessions table + profile session list/revoke + admin force-logout",
    "Email verification + password reset (Resend)",
    "Domain-restricted signup (ALLOWED_EMAIL_DOMAINS; reject gmail; empty -> invite-only; verification confirms address)",
    "Three roles + multiple admins (shared work; no-last-admin-demote guardrail; attributed audit)",
    "API tokens (read/write) + HIBP + lockout + Argon2id + AUTH_MODE=none"
  )}
$cards += @{ phase="Phase B"; title="Sprint 4 — WebSocket + job pipeline (U4)";
  goal="Live stage-by-stage progress + completion notification, no polling.";
  acc="200-col study p95 <= 60s warm; live stage progress + toast; worker kill leaves job re-queued (no orphaned running rows).";
  trace="U4";
  tasks=@(
    "arq workers in-process engine (one job per worker process)",
    "Job lifecycle -> job_runs + retry/backoff + soft/hard timeouts + dead-letter",
    "Cancellation flag checked at stage boundaries",
    "Redis pub/sub -> WS bridge; WS endpoints (jobs/{study}, notify/{user})",
    "Frontend WS client (reconnect + typed messages) + stage pills",
    "Bell-icon unread badge + opt-in desktop notification"
  )}
$cards += @{ phase="Phase B"; title="Sprint 5 — MCP server (G3)";
  goal="Any MCP-aware LLM client calls the engine without our website.";
  acc="pip install on a clean machine, configure a client, harmonize a CSV, get a result.";
  trace="G3, U14";
  tasks=@(
    "Package skeleton + pyproject.toml",
    "Three tools (harmonize_table/columns/values)",
    "stdio + SSE transports",
    "Tool schemas/descriptions/examples + API-token auth",
    "Per-client setup guides (Claude/Cursor/Copilot/Cline)",
    "Publish TestPyPI -> smoke test -> PyPI"
  )}
$cards += @{ phase="Phase B"; title="Sprint 6 — Active learning (G7)";
  goal="Review queue surfaces items that need a human and re-orders as curator works. Scope: per-study/cross-curator.";
  acc="Simulated session converges on diverse mappings vs random order.";
  trace="G7, U7";
  tasks=@(
    "Confidence-ascending default sort",
    "Margin-sampling re-rank on each accept/reject",
    "Re-rank instrumentation in audit log",
    "Unit tests with synthetic curator sessions"
  )}
$cards += @{ phase="Phase B"; title="Sprint 7 — Schema versioning (U9) + schema diff (G6)";
  goal="Admins publish a new curated_fields CSV as a new version; existing studies stay pinned. Diff UI is lower-priority.";
  acc="Admin promotes a new schema and sees layer-A diff; pinned study doesn't shift.";
  trace="G6, U9";
  tasks=@(
    "POST /admin/schema-versions (new version, never overwrite)",
    "Admin promote-version flow + audit row",
    "Per-study pin/un-pin endpoints + UI",
    "Schema-diff layer A (schema-vs-schema column diff)",
    "(Stretch) layer B study-impact re-score — only if curators ask"
  )}
$cards += @{ phase="Phase C"; title="Sprint 8 — Federation-lite (G1)";
  goal="Two installs swap a federation file and import each other's confirmed mappings.";
  acc="Round-trip shows mappings tagged with source institution; neither auto-merged.";
  trace="G1";
  tasks=@(
    "GET /federation/export (signed JSON + provenance)",
    "POST /federation/import (attribute source; pending local approval)",
    "Ed25519 signing + key rotation doc",
    "Import dedup + provenance tables + reject suspicious imports",
    "E2E round-trip between two staging instances"
  )}
$cards += @{ phase="Phase C"; title="Sprint 9 — Labeled export (G9) + study folder (U21) + value rewrite (U5)";
  goal="Produce validateData-passing study folders + labeled dataset, and rewrite confirmed ontology values across the full table on export.";
  acc="Folder accepted by validateData.py on a real datahub study; LinkML catches every checklist rule.";
  trace="G9, U5, U8, U21";
  tasks=@(
    "Nightly labeled-mappings dump + GET /export/{study}/labeled",
    "Value-level rewrite on export (confirmed value->term across all rows; app-side join)",
    "Multi-file ZIP packer (data_clinical_sample + meta files + case lists + LICENSE)",
    "Required-column injection + survival prefixing + banned-columns blocklist",
    "LinkML schema (verbatim QC checklist + survival vocab) + validator gate",
    "Final gate: invoke validateData.py on generated ZIP (+ CI E2E)",
    "OncoTree -> CANCER_TYPE/_DETAILED + UTF-8/LF/no-smart-quotes"
  )}
$cards += @{ phase="Phase D"; title="Sprint 10 — Hardening + observability";
  goal="Failures known in minutes; one dependency blip degrades one feature.";
  acc="Kill a worker -> alerts within 5 min, auto-recovery; resilience suite proves graceful degradation.";
  trace="";
  tasks=@(
    "Sentry backend+frontend + healthz/readyz + UptimeRobot 5 monitors",
    "Structured logs + nightly Postgres dump to R2 + weekly restore test",
    "Admin System Health page (queue/workers/backup/latency)",
    "Graceful degradation per dependency (PG/Redis/object-store/Gemini)",
    "Queue backpressure (429 + Retry-After) + crash recovery (heartbeat + reaper)",
    "Resilience tests simulating each outage -> degraded not 500"
  )}
$cards += @{ phase="Phase D"; title="Sprint 10.5 — Analytics dashboard + UI/UX polish (G8)";
  goal="Answer 'is this study ready?' and 'how is the effort going?', and bring the UI to a consistent accessible bar.";
  acc="Glance-readiness + blockers; viewer self-serve cross-study; axe-core zero serious violations; chart clicks navigate to filtered view.";
  trace="G8";
  tasks=@(
    "Readiness banner + KPI strip + confidence histogram with threshold bands",
    "Stage-contribution bar + review-status donut + ontology-resolution panel",
    "Progress sparkline + 'what's blocking export' checklist (links to fix)",
    "Cross-study dashboard (throughput/quality-trend/AL-payoff/KB-growth/team activity)",
    "Design tokens + Mapping Review density pass + optimistic UI + keyboard shortcuts",
    "WCAG 2.1 AA + designed empty/error states + reduced-motion"
  )}
$cards += @{ phase="Phase D"; title="Sprint 11 — Test suite + CI/CD";
  goal="Every commit ships through a green pipeline; rollback is one command.";
  acc="Clean clone -> CI -> green deploy <= 15 min; rollback <= 60s.";
  trace="";
  tasks=@(
    "pytest backend >= 80% + Vitest frontend >= 75%",
    "Playwright 3 happy-path E2E (upload->export; admin; viewer)",
    "GH Actions: lint->typecheck->tests->engine-boundary->build->push->deploy",
    "One-command rollback verified + branch protection"
  )}
$cards += @{ phase="Phase D"; title="Sprint 12 — Benchmark (D3 + D9) + docs + hand-in";
  goal="Now the product is solid — run the Production Readiness Benchmark end-to-end (first + final), complete docs, hand in.";
  acc="Benchmark committed on the final system; reviewer lands on README -> live URL -> harmonize+export -> finds every doc within two clicks.";
  trace="D3, D9";
  tasks=@(
    "Benchmark on agreed studies: label ground truth + capture all six dimensions on final system",
    "Publish the single authoritative benchmark report",
    "Curator User Guide + API Reference + MCP setup",
    "Deployment Guide + cBioPortal Integration Guide + Runbook",
    "README front page + hand-in package to mentors"
  )}
$cards += @{ phase="Phase E"; title="Maintained-instance window (M-1...M-6)";
  goal="Prove the instance is healthy under real use, fix top feedback, prep + execute handover or clean wind-down.";
  acc="Either handover executed (DNS cutover + runbook) or documented per-sprint extension with end-date.";
  trace="";
  tasks=@(
    "M-1 triage weekly + 99% SLO + apply patch releases + collect feedback",
    "M-2 fix top-3 real-world issues + update user guide",
    "M-3 handover prep (walkthrough + side-by-side deploy + accounts + restore dry-run)",
    "M-4 execute handover (DNS cutover + runbook) or extend",
    "M-5/M-6 OSS-maintainer mode or documented extension + closing note"
  )}

Write-Host "Creating $($cards.Count) deliverable cards..." -ForegroundColor Cyan
$n = 0
foreach ($c in $cards) {
  $desc = "## Goal`n$($c.goal)`n`n## Acceptance`n$($c.acc)"
  if ($c.trace) { $desc += "`n`n**Traceability:** $($c.trace)" }
  $card = T-Post "cards" @{ idList=$backlog; name=$c.title; desc=$desc; idLabels=$labels[$c.phase]; pos=(($n+1)*1000) }
  $chk = T-Post "checklists" @{ idCard=$card.id; name="Tasks" }
  foreach ($t in $c.tasks) { T-Post "checklists/$($chk.id)/checkItems" @{ name=$t } | Out-Null }
  $n++
  Write-Host "  [$n/$($cards.Count)] $($c.title)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Done. Board ready:" -ForegroundColor Green
Write-Host "  $($board.url)" -ForegroundColor Green
Write-Host "Share: open the board -> Share -> invite Sehyun or 'Create link' for view access." -ForegroundColor Yellow
