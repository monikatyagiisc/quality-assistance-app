# Build and start the full stack with Docker Compose (Windows PowerShell).
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is required. Install Docker Desktop and try again."
}

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.docker.example") {
        Copy-Item ".env.docker.example" ".env"
        Write-Host "Created .env from .env.docker.example — set GOOGLE_API_KEY before continuing."
    } else {
        Write-Error "Missing .env file. Create one with GOOGLE_API_KEY (see .env.docker.example)."
    }
}

$envContent = Get-Content ".env" -Raw
if ($envContent -notmatch 'GOOGLE_API_KEY=(?!your-gemini-api-key)(?!\s*$).+') {
    Write-Error "Set a valid GOOGLE_API_KEY in $Root\.env"
}

Write-Host "Building and starting services..."
docker compose up --build -d

Write-Host ""
Write-Host "Waiting for services to become healthy..."
$deadline = (Get-Date).AddMinutes(3)

while ((Get-Date) -lt $deadline) {
    $backendOk = $false
    $agentOk = $false
    $frontendOk = $false
    try { Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 3 | Out-Null; $backendOk = $true } catch {}
    try { Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing -TimeoutSec 3 | Out-Null; $agentOk = $true } catch {}
    try { Invoke-WebRequest -Uri "http://localhost:5173/" -UseBasicParsing -TimeoutSec 3 | Out-Null; $frontendOk = $true } catch {}

    if ($backendOk -and $agentOk -and $frontendOk) {
        Write-Host ""
        Write-Host "All services are up."
        Write-Host "  Frontend:  http://localhost:5173"
        Write-Host "  Backend:   http://localhost:8000  (docs: /docs)"
        Write-Host "  Agent:     http://localhost:8001  (docs: /docs)"
        Write-Host "  Postgres:  localhost:5432"
        Write-Host ""
        Write-Host "Logs:  docker compose logs -f"
        Write-Host "Stop:  docker compose down"
        exit 0
    }
    Start-Sleep -Seconds 3
}

Write-Error "Services did not become healthy within 3 minutes. Run: docker compose ps"
docker compose ps
exit 1
