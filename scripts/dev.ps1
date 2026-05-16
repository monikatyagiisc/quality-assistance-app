# Start agent, backend, and frontend for local development (Windows PowerShell).
# Uses local PostgreSQL if already running; otherwise starts Docker Postgres.
#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

$LogDir = Join-Path $Root ".logs"
$StartedDocker = $false
$ServiceProcesses = @()

$PgHost = "localhost"
$PgPort = 5432
$PgUser = "quality_assistance"
$PgDatabase = "quality_assistance"

function Write-LogLine {
    param(
        [string]$Label,
        [string]$Message,
        [ConsoleColor]$Color = [ConsoleColor]::Gray
    )
    $previous = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = $Color
    Write-Host "[$Label] $Message"
    $Host.UI.RawUI.ForegroundColor = $previous
}

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Error: '$Name' is required but not installed or not on PATH."
    }
}

function Ensure-EnvFile {
    param([string]$Example, [string]$Target)
    if (-not (Test-Path $Target) -and (Test-Path $Example)) {
        Copy-Item $Example $Target
        Write-LogLine "system" "Created $Target from example." ([ConsoleColor]::Cyan)
    }
}

function Read-DotEnv {
    param([string]$Path)
    $values = @{}
    if (-not (Test-Path $Path)) { return $values }
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { return }
        if ($line -match '^\s*([^=]+)=(.*)$') {
            $values[$Matches[1].Trim()] = $Matches[2].Trim().Trim('"').Trim("'")
        }
    }
    return $values
}

function Load-PgConfig {
    $envFile = Join-Path $Root "backend\.env"
    $vars = Read-DotEnv $envFile

    if ($vars["DB_HOST"]) { $script:PgHost = $vars["DB_HOST"] }
    if ($vars["DB_PORT"]) { $script:PgPort = [int]$vars["DB_PORT"] }
    if ($vars["DB_USER"]) { $script:PgUser = $vars["DB_USER"] }
    if ($vars["DB_NAME"]) { $script:PgDatabase = $vars["DB_NAME"] }
    elseif ($vars["DBNAME"]) { $script:PgDatabase = $vars["DBNAME"] }
}

function Test-PostgresReady {
    try {
        $result = Test-NetConnection -ComputerName $PgHost -Port $PgPort -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
        return [bool]$result.TcpTestSucceeded
    } catch {
        return $false
    }
}

function Wait-PostgresReady {
    for ($i = 1; $i -le 30; $i++) {
        if (Test-PostgresReady) { return $true }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Ensure-Postgres {
    Load-PgConfig

    if (Test-PostgresReady) {
        Write-LogLine "postgres" "Already running at ${PgHost}:${PgPort} (skipping Docker)." ([ConsoleColor]::Blue)
        return
    }

    Require-Command "docker"
    Write-LogLine "postgres" "Not reachable at ${PgHost}:${PgPort}. Starting Docker..." ([ConsoleColor]::Blue)
    docker compose up -d postgres
    if ($LASTEXITCODE -ne 0) { throw "docker compose failed to start postgres." }

    $script:StartedDocker = $true
    $script:PgHost = "localhost"
    $script:PgPort = 5432
    $script:PgUser = "quality_assistance"
    $script:PgDatabase = "quality_assistance"

    Write-LogLine "postgres" "Waiting for Docker PostgreSQL..." ([ConsoleColor]::Blue)
    if (-not (Wait-PostgresReady)) {
        throw "PostgreSQL did not become ready in time."
    }
}

function Add-UvToPath {
    $uvPath = Join-Path $env:USERPROFILE ".local\bin"
    if ((Test-Path $uvPath) -and ($env:PATH -notlike "*$uvPath*")) {
        $env:PATH = "$uvPath;$env:PATH"
    }
}

function Start-DevService {
    param(
        [string]$Label,
        [string]$WorkingDirectory,
        [string]$CommandLine
    )

    $logFile = Join-Path $LogDir "$Label.log"
    New-Item -ItemType File -Path $logFile -Force | Out-Null

    Write-LogLine $Label "Starting..." ([ConsoleColor]::Yellow)

    $proc = Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/c", $CommandLine `
        -WorkingDirectory $WorkingDirectory `
        -PassThru `
        -WindowStyle Hidden

    $script:ServiceProcesses += [PSCustomObject]@{
        Label = $Label
        Process = $proc
        LogFile = $logFile
        CommandLine = $CommandLine
        WorkingDirectory = $WorkingDirectory
    }
}

function Stop-DevServices {
    Write-Host ""
    Write-Host "Stopping app services..."
    foreach ($svc in $ServiceProcesses) {
        if ($svc.Process -and -not $svc.Process.HasExited) {
            Stop-Process -Id $svc.Process.Id -Force -ErrorAction SilentlyContinue
        }
    }
    if ($StartedDocker) {
        Write-Host "Stopping Docker PostgreSQL..."
        docker compose stop postgres 2>$null
    }
    Write-Host "Done."
}

# --- Main ---
try {
    Add-UvToPath
    Require-Command "uv"
    Require-Command "yarn"

    Ensure-EnvFile (Join-Path $Root "backend\.env.example") (Join-Path $Root "backend\.env")
    Ensure-EnvFile (Join-Path $Root "agent\.env.example") (Join-Path $Root "agent\.env")
    Ensure-EnvFile (Join-Path $Root "frontend\.env.example") (Join-Path $Root "frontend\.env")

    $agentEnv = Join-Path $Root "agent\.env"
    if (-not (Test-Path $agentEnv) -or ((Get-Content $agentEnv -Raw) -notmatch 'GOOGLE_API_KEY=\S+')) {
        Write-Warning "Set GOOGLE_API_KEY in agent\.env before using the agent."
    }

    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    Ensure-Postgres

    Write-LogLine "system" "Installing Python dependencies..." ([ConsoleColor]::Cyan)
    Push-Location (Join-Path $Root "agent")
    uv sync --quiet
    Pop-Location
    Push-Location (Join-Path $Root "backend")
    uv sync --quiet
    Pop-Location

    Write-LogLine "system" "Running database migrations..." ([ConsoleColor]::Cyan)
    Push-Location (Join-Path $Root "backend")
    uv run alembic upgrade head
    Pop-Location

    Write-LogLine "system" "Installing frontend dependencies..." ([ConsoleColor]::Cyan)
    Push-Location (Join-Path $Root "frontend")
    yarn install --frozen-lockfile 2>$null
    if ($LASTEXITCODE -ne 0) { yarn install }
    Pop-Location

    $agentDir = Join-Path $Root "agent"
    $backendDir = Join-Path $Root "backend"
    $frontendDir = Join-Path $Root "frontend"

    Start-DevService -Label "agent" -WorkingDirectory $agentDir `
        -CommandLine "uv run quality-assistance-agent >> `"$(Join-Path $LogDir 'agent.log')`" 2>&1"
    Start-DevService -Label "backend" -WorkingDirectory $backendDir `
        -CommandLine "uv run quality-assistance-backend >> `"$(Join-Path $LogDir 'backend.log')`" 2>&1"
    Start-DevService -Label "frontend" -WorkingDirectory $frontendDir `
        -CommandLine "yarn dev >> `"$(Join-Path $LogDir 'frontend.log')`" 2>&1"

    Start-Sleep -Seconds 3
    Load-PgConfig

    Write-Host ""
    Write-LogLine "system" "All services started." ([ConsoleColor]::Cyan)
    Write-LogLine "system" "  Frontend:  http://localhost:5173" ([ConsoleColor]::Cyan)
    Write-LogLine "system" "  Backend:   http://localhost:8000  (docs: /docs)" ([ConsoleColor]::Cyan)
    Write-LogLine "system" "  Agent:     http://localhost:8001  (docs: /docs)" ([ConsoleColor]::Cyan)
    Write-LogLine "postgres" "  Database:  ${PgHost}:${PgPort} ($PgDatabase)" ([ConsoleColor]::Blue)
    Write-Host ""
    Write-LogLine "system" "Logs: $LogDir\agent.log, backend.log, frontend.log" ([ConsoleColor]::Cyan)
    Write-LogLine "system" "Press Ctrl+C to stop app services." ([ConsoleColor]::Cyan)
    if ($StartedDocker) {
        Write-LogLine "postgres" "Docker PostgreSQL started by this script will be stopped on exit." ([ConsoleColor]::Blue)
    }
    Write-Host ""

    while ($true) {
        foreach ($svc in $ServiceProcesses) {
            if ($svc.Process.HasExited) {
                throw "Service '$($svc.Label)' exited unexpectedly. Check $($svc.LogFile)"
            }
        }
        Start-Sleep -Seconds 2
    }
} catch {
    if ($_.Exception.Message -notlike "*exited unexpectedly*") {
        Write-Error $_.Exception.Message
    } else {
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
    exit 1
} finally {
    Stop-DevServices
}
