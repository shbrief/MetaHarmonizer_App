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
  ./scripts/dev_services.ps1 setup     # one-time: download binaries + init the DB
  ./scripts/dev_services.ps1 start
  ./scripts/dev_services.ps1 status
  ./scripts/dev_services.ps1 stop
#>
param(
  [Parameter(Mandatory)][ValidateSet("setup","start","stop","status")][string]$Action
)
$ErrorActionPreference = "Stop"

# All paths/ports are overridable via env vars (handy if the defaults clash with
# something already running). Defaults match the values shipped in .env.example.
$root  = if ($env:MH_DEV_ROOT) { $env:MH_DEV_ROOT } else { "$env:LOCALAPPDATA\mh-dev" }
$pgbin = "$root\pg\pgsql\bin"
$pgdata= "$root\pgdata"
$pglog = "$root\pg.log"
$redis = "$root\redis\redis-server.exe"
$rcli  = "$root\redis\redis-cli.exe"
$PGPORT = if ($env:MH_PG_PORT)    { [int]$env:MH_PG_PORT }    else { 5433 }
$RPORT  = if ($env:MH_REDIS_PORT) { [int]$env:MH_REDIS_PORT } else { 6380 }

# Portable binaries (no installer, no admin). Bump versions here when needed.
$PG_URL    = "https://get.enterprisedb.com/postgresql/postgresql-16.4-1-windows-x64-binaries.zip"
$REDIS_URL = "https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.zip"
$PGUSER = "mh"; $PGPASS = "mh_dev_password"; $PGDB = "metaharmonizer"

# Fast TCP probe (Test-NetConnection is slow because it pings ICMP first).
function Listening($p){
  $c = New-Object System.Net.Sockets.TcpClient
  try { $c.Connect("127.0.0.1", [int]$p); return $c.Connected } catch { return $false } finally { $c.Dispose() }
}

# Start Postgres by launching postgres.exe directly (detached) and polling the
# port. `pg_ctl ... start` is avoided on purpose: on Windows it leaves a hung
# helper process when its stdio is redirected/inherited (Start-Process -Wait
# never returns; a bare pipe to Out-Null deadlocks). Launching the server binary
# and waiting on the TCP port is robust and needs no console plumbing.
function Start-Pg($pgbin, $pgdata, $port, $log){
  if (Listening $port) { return }
  Start-Process -FilePath "$pgbin\postgres.exe" `
    -ArgumentList "-D",$pgdata,"-p","$port" `
    -RedirectStandardError $log -WindowStyle Hidden | Out-Null
  for ($i = 0; $i -lt 60; $i++) {
    if (Listening $port) { return }
    Start-Sleep -Milliseconds 500
  }
  throw "Postgres did not come up on port $port within 30s (see $log)"
}

# Download (skip if a complete copy already exists) + extract. Uses .NET ZipFile,
# which is far faster and more reliable than Expand-Archive on large archives.
function Get-AndExtract($url, $zip, $dest) {
  Add-Type -AssemblyName System.IO.Compression.FileSystem | Out-Null
  $valid = $false
  if (Test-Path $zip) {
    try { $a = [IO.Compression.ZipFile]::OpenRead($zip); $null = $a.Entries.Count; $a.Dispose(); $valid = $true } catch { $valid = $false }
  }
  if (-not $valid) {
    if (Test-Path $zip) { Remove-Item $zip -Force }
    $old = $ProgressPreference; $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    $ProgressPreference = $old
  }
  New-Item -ItemType Directory -Force -Path $dest | Out-Null
  [IO.Compression.ZipFile]::ExtractToDirectory($zip, $dest, $true)
}

switch ($Action) {
  "setup" {
    # A stray PGPORT in the environment would be honoured by initdb's bootstrap
    # backend and by the server; we pass the port explicitly, so clear it.
    Remove-Item Env:\PGPORT -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $root | Out-Null
    $tmp = Join-Path $env:TEMP "mh-dev-dl"; New-Item -ItemType Directory -Force -Path $tmp | Out-Null

    # 1) Postgres portable binaries -> $root\pg\pgsql\bin
    if (-not (Test-Path "$pgbin\initdb.exe")) {
      Write-Host "Fetching Postgres (~320 MB, one time)..." -ForegroundColor Cyan
      Get-AndExtract $PG_URL (Join-Path $tmp "pg.zip") "$root\pg"   # yields $root\pg\pgsql\...
      if (-not (Test-Path "$pgbin\initdb.exe")) { throw "Postgres extraction failed: $pgbin\initdb.exe missing" }
    } else { Write-Host "Postgres binaries present" -ForegroundColor DarkGray }

    # 2) Redis portable binaries -> $root\redis\redis-server.exe
    if (-not (Test-Path $redis)) {
      Write-Host "Fetching Redis (~12 MB, one time)..." -ForegroundColor Cyan
      Get-AndExtract $REDIS_URL (Join-Path $tmp "redis.zip") "$root\redis"
      if (-not (Test-Path $redis)) { throw "Redis extraction failed: $redis missing" }
    } else { Write-Host "Redis binaries present" -ForegroundColor DarkGray }

    # 3) Initialise the Postgres data dir with the mh superuser (idempotent).
    if (-not (Test-Path "$pgdata\PG_VERSION")) {
      Write-Host "Initialising database cluster..." -ForegroundColor Cyan
      $pwfile = Join-Path $tmp "pgpw.txt"
      Set-Content -Path $pwfile -Value $PGPASS -NoNewline -Encoding ascii
      & "$pgbin\initdb.exe" -D $pgdata -U $PGUSER -A scram-sha-256 --pwfile=$pwfile -E UTF8 | Out-Null
      Remove-Item $pwfile -Force
    } else { Write-Host "Data dir already initialised" -ForegroundColor DarkGray }

    # 4) Start Postgres and create the application database (idempotent).
    if (-not (Listening $PGPORT)) {
      Start-Pg $pgbin $pgdata $PGPORT $pglog
    }
    $env:PGPASSWORD = $PGPASS
    $exists = & "$pgbin\psql.exe" -h 127.0.0.1 -p $PGPORT -U $PGUSER -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$PGDB'"
    if ("$exists".Trim() -ne "1") {
      & "$pgbin\createdb.exe" -h 127.0.0.1 -p $PGPORT -U $PGUSER $PGDB
      Write-Host "Created database '$PGDB'" -ForegroundColor Green
    } else { Write-Host "Database '$PGDB' already exists" -ForegroundColor DarkGray }

    Write-Host "`nSetup complete. Next:" -ForegroundColor Green
    Write-Host "  ./scripts/dev_services.ps1 start" -ForegroundColor Green
  }
  "start" {
    if (-not (Test-Path "$pgdata\PG_VERSION")) { throw "Postgres data dir missing at $pgdata. Run: ./scripts/dev_services.ps1 setup" }
    if (Listening $PGPORT) { Write-Host "Postgres already up ($PGPORT)" -ForegroundColor DarkGray }
    else {
      Start-Pg $pgbin $pgdata $PGPORT $pglog
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
