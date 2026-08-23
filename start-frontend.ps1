# Start SmartInsights Next.js frontend
# Run from repo root in a SEPARATE terminal: .\start-frontend.ps1

$ErrorActionPreference = "Stop"
Push-Location (Join-Path $PSScriptRoot "frontend")
try {
  if (-not (Test-Path "node_modules")) {
    npm install
  }
  Write-Host "Starting SmartInsights frontend on http://localhost:3000 ..."
  npx next dev -p 3000
} finally {
  Pop-Location
}
