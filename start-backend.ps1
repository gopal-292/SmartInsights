# Start SmartInsights FastAPI backend (PPT stack)
# Run from repo root: .\start-backend.ps1

$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
  # Prefer PPT database stack: PostgreSQL + pgVector
  try {
    docker info 1>$null 2>$null
    if ($LASTEXITCODE -eq 0) {
      docker compose up -d
    } else {
      Write-Host "Docker is not running. Start Docker Desktop for PostgreSQL/pgVector (PPT stack)."
    }
  } catch {
    Write-Host "Docker not available. FastAPI will fall back to SQLite until Postgres is up."
  }

  Push-Location (Join-Path $PSScriptRoot "backend")
  try {
    $gtkBin = "C:\Program Files\GTK3-Runtime Win64\bin"
    if (Test-Path $gtkBin) {
      $env:PATH = "$gtkBin;$env:PATH"
    }

    if (-not (Test-Path ".venv")) {
      python -m venv .venv
      .\.venv\Scripts\pip install -r requirements.txt
    }

    $port = 8000
    # If 8000 is blocked/busy, automatically use 8001
    try {
      $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 8000)
      $listener.Start()
      $listener.Stop()
    } catch {
      $port = 8001
      Write-Host "Port 8000 is busy - starting API on http://127.0.0.1:$port"
      Write-Host "Update frontend/.env.local NEXT_PUBLIC_API_URL to http://localhost:$port/api if needed."
    }

    Write-Host "Starting SmartInsights API on http://127.0.0.1:$port"
    & .\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port $port
  } finally {
    Pop-Location
  }
} finally {
  Pop-Location
}
