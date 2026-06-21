<#
.SYNOPSIS
  Add the testing-strategy cards to the existing MetaHarmonizer SA3.1 Trello board.
.DESCRIPTION
  Adds two cards:
    1. Load / stress / soak capacity testing (capacity report at p95 SLO).
    2. End-to-end + full test suite (all user journeys + every useful test type).
  Reads $env:TRELLO_KEY / $env:TRELLO_TOKEN.
#>
$ErrorActionPreference = "Stop"
$key=$env:TRELLO_KEY; $token=$env:TRELLO_TOKEN
if (-not $key -or -not $token) { throw "Set `$env:TRELLO_KEY and `$env:TRELLO_TOKEN first." }
$base="https://api.trello.com/1"
function Esc($s){ [uri]::EscapeDataString($s) }
function T-Get($path){ Invoke-RestMethod "$base/$path`?key=$key&token=$token" }
function T-Post($path,$params){ $qs=($params.GetEnumerator()|%{"$($_.Key)=$(Esc([string]$_.Value))"}) -join "&"; Invoke-RestMethod -Method Post -Uri "$base/$path`?$qs&key=$key&token=$token" }

# locate the board
$boards = T-Get "members/me/boards"
$board = $boards | Where-Object { $_.name -eq "MetaHarmonizer SA3.1" } | Select-Object -First 1
if (-not $board) { throw "Board 'MetaHarmonizer SA3.1' not found." }
$bid = $board.id
Write-Host "Board: $($board.url)" -ForegroundColor Green

# map lists + labels by name
$lists = @{}; (T-Get "boards/$bid/lists") | ForEach-Object { $lists[$_.name]=$_.id }
$labels = @{}; (T-Get "boards/$bid/labels") | ForEach-Object { if($_.name){ $labels[$_.name]=$_.id } }
$backlog = $lists["Backlog"]
if (-not $backlog) { $backlog = ($lists.GetEnumerator() | Select-Object -First 1).Value }

$cards = @()

$cards += @{ phase="Phase C"; title="Load / stress / soak testing — capacity report";
  goal="Measure the system's full capacity: how many concurrent curators and parallel harmonize jobs it sustains before p95 latency breaks the SLO. Best run AFTER Sprint 4 (arq job pipeline) so the real concurrency bottleneck is exercised. Uses the golden-signal /metrics already in place.";
  acc="docs/benchmark/load-<date>.md committed with: max concurrent users and parallel jobs at p95 SLO, the breakpoint where p95 degrades, soak-test memory/connection stability over 30+ min, and the tuned knob values (worker count, DB pool size, Redis limits).";
  trace="D-B latency, D-C resources (extends Sprint 12 benchmark)";
  tasks=@(
    "Pick tool: k6 (preferred) or Locust; scenario scripts in tests/load/",
    "Smoke load: ramp 1->N virtual users through login -> /me -> list studies",
    "Spike + breakpoint: ramp until p95 SLO breaks; record capacity ceiling",
    "Soak/endurance: sustained load 30-60 min -> watch memory leak + pool exhaustion",
    "Concurrent harmonize jobs: queue depth vs worker count vs p95 completion",
    "Tune + record knobs: arq worker count, DB connection pool, Redis limits",
    "Read results from admin /metrics (golden signals + job_queue_depth + ws_connections)",
    "Write docs/benchmark/load-<date>.md: capacity numbers + SLO breakpoint + recommendations"
  )}

$cards += @{ phase="Phase C"; title="End-to-end test suite — all user journeys + every useful test type";
  goal="Comprehensive automated coverage so every user journey and every cross-cutting concern is verified on each change. Layers: unit -> contract/integration -> E2E (Playwright) -> accessibility -> security -> performance, all wired into CI.";
  acc="CI green on: full Playwright E2E for every user journey below; unit + contract suites; axe-core zero serious violations on the four main pages; an authz/security matrix; coverage gate enforced. A fresh clone runs `make test` (or CI) end-to-end without manual setup.";
  trace="Sprint 11 test suite + CI/CD; RBAC matrix; U18";
  tasks=@(
    "E2E: first-user bootstrap admin -> register/login/logout -> session restore on reload",
    "E2E: domain-gated signup rejected; breached password (HIBP) rejected; lockout after N fails",
    "E2E: upload -> harmonize -> mapping review (accept/reject/edit/batch) -> ontology review -> quality -> export round-trip",
    "E2E: RBAC matrix — viewer denied writes (403/hidden), curator allowed, admin allowed",
    "E2E: profile — sessions list + revoke; API token create/use/revoke",
    "E2E: admin — change role, disable account, force sign-out (victim's next request 401)",
    "E2E: multi-browser — revoke session-A from session-B; A's next request 401",
    "Unit: services + helpers (analytics, security, hibp, pagination, uploads)",
    "Contract/integration: every /api/v1 route against real Postgres + Redis",
    "Accessibility: axe-core scan on Dashboard/Mapping/Quality/Export — zero serious",
    "Security: authz matrix, rate-limit 429, lockout, injection probes, error-envelope shape",
    "Resilience: worker kill mid-job leaves no orphaned 'running' row (post Sprint 4)",
    "CI: GitHub Actions runs unit+contract+E2E+axe on PR; coverage gate; services via compose",
    "Optional: visual-regression snapshots on key pages"
  )}

Write-Host "Adding $($cards.Count) testing cards..." -ForegroundColor Cyan
$n=0
foreach ($c in $cards) {
  $desc = "## Goal`n$($c.goal)`n`n## Acceptance`n$($c.acc)"
  if ($c.trace) { $desc += "`n`n**Traceability:** $($c.trace)" }
  $idLabels = $labels[$c.phase]
  $card = T-Post "cards" @{ idList=$backlog; name=$c.title; desc=$desc; idLabels=$idLabels }
  $chk = T-Post "checklists" @{ idCard=$card.id; name="Tasks" }
  foreach ($t in $c.tasks) { T-Post "checklists/$($chk.id)/checkItems" @{ name=$t } | Out-Null }
  $n++; Write-Host "  [$n/$($cards.Count)] $($c.title) -> $($card.shortUrl)" -ForegroundColor DarkGray
}
Write-Host "`nDone. Board: $($board.url)" -ForegroundColor Green
