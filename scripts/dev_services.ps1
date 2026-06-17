<#
.SYNOPSIS
  Start/stop local dev services (PostgreSQL + Redis) WITHOUT Docker or admin rights.
.DESCRIPTION
  Uses portable binaries under %LOCALAPPDATA%\mh-dev. This is the no-Docker dev path
  for machines without WSL2/admin/Docker. On a machine WITH Docker, prefer `make up`.

    Postgres : 127.0.0.1:5433  user=mh  pw=mh_dev_password  db=metaharmonizer
    Redis    : 127.0.0.1:6380

  Matching .env values:
    DATABASE_URL=postgresql+asyncpg://mh:mh_dev_password@127.0.0.1:5433/metaharmonizer
    REDIS_URL=redis://127.0.0.1:6380/0
.EXAMPLE
  ./scripts/dev_services.ps1 start
  ./scripts/dev_services.ps1 status
  ./scripts/dev_services.ps1 stop
#>
param(
  [Parameter(Mandatory)][ValidateSet("start","stop","status")][string]$Action
)
$ErrorActionPreference = "Stop"

$root  = "$env:LOCALAPPDATA\mh-dev"
$pgbin = "$root\pg\pgsql\bin"
$pgdata= "$root\pgdata"
$pglog = "$root\pg.log"
$redis = "$root\redis\redis-server.exe"
$rcli  = "$root\redis\redis-cli.exe"
$PGPORT = 5433
$RPORT  = 6380

function Listening($p){ (Test-NetConnection 127.0.0.1 -Port $p -WarningAction SilentlyContinue).TcpTestSucceeded }

switch ($Action) {
  "start" {
    if (-not (Test-Path "$pgdata\PG_VERSION")) { throw "Postgres data dir missing at $pgdata. Re-run the one-time setup." }
    if (Listening $PGPORT) { Write-Host "Postgres already up ($PGPORT)" -ForegroundColor DarkGray }
    else {
      & "$pgbin\pg_ctl.exe" -D $pgdata -o "-p $PGPORT" -l $pglog -w start | Out-Null
      Write-Host "Postgres started ($PGPORT)" -ForegroundColor Green
    }
    if (Listening $RPORT) { Write-Host "Redis already up ($RPORT)" -ForegroundColor DarkGray }
    else {
      Start-Process -FilePath $redis -ArgumentList "--port",$RPORT -WindowStyle Hidden
      Start-Sleep 1
      Write-Host "Redis started ($RPORT)" -ForegroundColor Green
    }
  }
  "stop" {
    if (Listening $PGPORT) { & "$pgbin\pg_ctl.exe" -D $pgdata -m fast stop | Out-Null; Write-Host "Postgres stopped" -ForegroundColor Yellow }
    if (Listening $RPORT)  { & $rcli -p $RPORT shutdown nosave 2>$null; Write-Host "Redis stopped" -ForegroundColor Yellow }
  }
  "status" {
    Write-Host ("Postgres {0,-5} {1}" -f $PGPORT, $(if(Listening $PGPORT){"UP"}else{"down"}))
    Write-Host ("Redis    {0,-5} {1}" -f $RPORT,  $(if(Listening $RPORT){"UP"}else{"down"}))
  }
}
