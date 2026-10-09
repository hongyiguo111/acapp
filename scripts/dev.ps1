# Local development launcher (Windows / PowerShell).
#   .\scripts\dev.ps1            start Redis (docker), both match servers, and Django on http://127.0.0.1:8000
#   .\scripts\dev.ps1 -Port 8001 use another web port
# Ctrl+C stops Django and the match servers; Redis keeps running (docker compose down to stop it).
param([int]$Port = 8000)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$py   = Join-Path $root ".venv\Scripts\python.exe"
$logs = Join-Path $root ".dev-logs"
New-Item -ItemType Directory -Force $logs | Out-Null

if (-not (Test-Path $py)) { throw "Missing .venv - run: python3.11 -m venv .venv ; .venv\Scripts\pip install -r requirements.txt" }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    $env:Path += ";$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin"
}

# Local settings: debug on, Redis on 16379 (Windows reserves 6379 on some machines, see docker-compose.yml)
$env:DJANGO_DEBUG = "1"
$env:REDIS_PORT   = "16379"
$env:PYTHONPATH   = $root

docker compose -f (Join-Path $root "docker-compose.yml") up -d
if ($LASTEXITCODE -ne 0) { throw "docker compose failed - is Docker Desktop running?" }

# Match servers must run from match_system/src (they use relative sys.path entries)
$matchDir = Join-Path $root "match_system\src"
$procs = @()
foreach ($script in "main.py", "dual_main.py") {
    $name = [IO.Path]::GetFileNameWithoutExtension($script)
    $procs += Start-Process $py -ArgumentList $script -WorkingDirectory $matchDir -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logs "$name.out.log") -RedirectStandardError (Join-Path $logs "$name.err.log")
}

try {
    Write-Host "Django on http://127.0.0.1:$Port  (match servers: pid $($procs.Id -join ', '); logs in .dev-logs)"
    & $py (Join-Path $root "manage.py") runserver "127.0.0.1:$Port" --noreload
}
finally {
    $procs | Where-Object { -not $_.HasExited } | Stop-Process -Force
}
