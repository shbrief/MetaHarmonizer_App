<#  Move/seed cards to reflect real state. Reads $env:TRELLO_KEY / $env:TRELLO_TOKEN. #>
$ErrorActionPreference="Stop"
$key=$env:TRELLO_KEY; $token=$env:TRELLO_TOKEN
if(-not $key -or -not $token){ throw "Set TRELLO_KEY/TRELLO_TOKEN." }
$base="https://api.trello.com/1"
function Esc($s){ [uri]::EscapeDataString($s) }
function G($p){ Invoke-RestMethod "$base/$p`?key=$key&token=$token" }
function P($p,$h){ $qs=($h.GetEnumerator()|%{"$($_.Key)=$(Esc([string]$_.Value))"}) -join "&"; Invoke-RestMethod -Method Post -Uri "$base/$p`?$qs&key=$key&token=$token" }
function PUT($p,$h){ $qs=($h.GetEnumerator()|%{"$($_.Key)=$(Esc([string]$_.Value))"}) -join "&"; Invoke-RestMethod -Method Put -Uri "$base/$p`?$qs&key=$key&token=$token" }

$board=(G "members/me/boards") | ?{ $_.name -eq "MetaHarmonizer SA3.1" } | Select -First 1
$bid=$board.id
$lists=@{}; (G "boards/$bid/lists") | %{ $lists[$_.name]=$_.id }
$labels=@{}; (G "boards/$bid/labels") | %{ if($_.name){ $labels[$_.name]=$_.id } }
$cards=(G "boards/$bid/cards")

function Move($titleLike,$listName){
  $c=$cards | ?{ $_.name -like $titleLike } | Select -First 1
  if($c){ PUT "cards/$($c.id)" @{ idList=$lists[$listName] } | Out-Null; Write-Host "  -> [$listName] $($c.name)" -ForegroundColor DarkGray }
  else { Write-Host "  (not found) $titleLike" -ForegroundColor Yellow }
}

# 1. Seed a Done card capturing the completed foundation (prototype + engine-adapter migration)
$doneTitle="Foundation already shipped — prototype + engine-adapter migration"
if(-not ($cards | ?{ $_.name -eq $doneTitle })){
  $desc="## Done before sprint plan`nWhat already works in the repo and underpins everything else.`n`n## Covers`nG5 (accept/reject/edit + batch), G8 (Quality KPI panel), G10 (engine packaging via adapter), U3, U17."
  $card=P "cards" @{ idList=$lists["Done"]; name=$doneTitle; desc=$desc; idLabels=$labels["Phase A"] }
  $chk=P "checklists" @{ idCard=$card.id; name="Shipped" }
  @(
    "React/Vite prototype: Upload/MappingReview/Ontology/Quality/Export pages",
    "Engine-adapter pattern complete (EngineProtocol + metaharmonizer + mock impls)",
    "Engine boundary CI check (only engine_adapter imports the wheel)",
    "Vendored metaharmonizer 0.3.0 wheel wired via ENGINE_IMPL",
    "Accept/reject/edit + batch (G5), Quality KPI panel (G8)"
  ) | %{ P "checklists/$($chk.id)/checkItems" @{ name=$_ } | Out-Null }
  # mark all items complete
  (G "checklists/$($chk.id)/checkItems") | %{ PUT "cards/$($card.id)/checkItem/$($_.id)" @{ state="complete" } | Out-Null }
  Write-Host "  -> [Done] $doneTitle" -ForegroundColor Green
}

# 2. In Progress — what to build first
Move "Dev infra*" "In Progress"

# 3. Todo — next up
Move "Sprint 2 *" "Todo"
Move "Frontend integration*" "Todo"
Move "Spec v2 cleanup*" "Todo"

Write-Host "`nDone. $($board.url)" -ForegroundColor Green
