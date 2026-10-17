# One-time setup for local development on Windows PowerShell.
#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "'$Name' is required but is not installed or not on PATH. See docs\SETUP-WINDOWS.md."
    }
}

function Invoke-Checked {
    param(
        [string]$Command,
        [string[]]$Arguments
    )
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Command $($Arguments -join ' ')"
    }
}

function Ensure-EnvFile {
    param([string]$Example, [string]$Target)
    if (-not (Test-Path $Target)) {
        Copy-Item $Example $Target
        Write-Host "Created $Target from its example."
    }
}

function Set-EnvPlaceholder {
    param(
        [string]$Path,
        [string]$Name,
        [string]$Placeholder,
        [string]$Value
    )

    $content = [System.IO.File]::ReadAllText($Path)
    $pattern = "(?m)^$([regex]::Escape($Name))=(.*)$"
    $match = [regex]::Match($content, $pattern)
    if ($match.Success) {
        $current = $match.Groups[1].Value.Trim().Trim('"').Trim("'")
        if ($current -eq $Placeholder) {
            $content = [regex]::Replace($content, $pattern, "$Name=$Value", 1)
            [System.IO.File]::WriteAllText($Path, $content)
            Write-Host "Generated a development value for $Name in $Path."
        }
    }
}

function Get-EnvValue {
    param([string]$Path, [string]$Name, [string]$Default)
    $content = [System.IO.File]::ReadAllText($Path)
    $pattern = "(?m)^$([regex]::Escape($Name))=(.*)$"
    $match = [regex]::Match($content, $pattern)
    if (-not $match.Success) { return $Default }
    return $match.Groups[1].Value.Trim().Trim('"').Trim("'")
}

function New-UrlSafeKey {
    param([bool]$KeepPadding = $false)
    $bytes = New-Object byte[] 32
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($bytes)
    } finally {
        $generator.Dispose()
    }

    $value = [Convert]::ToBase64String($bytes).Replace('+', '-').Replace('/', '_')
    if (-not $KeepPadding) { $value = $value.TrimEnd('=') }
    return $value
}

function Test-TcpPort {
    param([string]$HostName, [int]$Port)
    return [bool](Test-NetConnection -ComputerName $HostName -Port $Port `
        -InformationLevel Quiet -WarningAction SilentlyContinue -ErrorAction SilentlyContinue)
}

function Ensure-Postgres {
    param([string]$HostName, [int]$Port)
    if (Test-TcpPort -HostName $HostName -Port $Port) {
        Write-Host "PostgreSQL is reachable at ${HostName}:$Port."
        return
    }

    if ($HostName -notin @("localhost", "127.0.0.1") -or $Port -ne 5432) {
        throw "PostgreSQL is not reachable at ${HostName}:$Port. Start your configured database and rerun setup."
    }

    Require-Command "docker"
    Write-Host "PostgreSQL is not reachable. Starting the project's PostgreSQL container..."
    Invoke-Checked -Command "docker" -Arguments @("compose", "up", "-d", "postgres")

    for ($attempt = 1; $attempt -le 30; $attempt++) {
        if (Test-TcpPort -HostName "localhost" -Port 5432) {
            Write-Host "PostgreSQL is ready."
            return
        }
        Start-Sleep -Seconds 1
    }
    throw "PostgreSQL did not become ready. Check that Docker Desktop is running."
}

try {
    Require-Command "python"
    Require-Command "node"
    Require-Command "npm"
    Require-Command "uv"
    Require-Command "yarn"

    $pythonVersion = (& python --version 2>&1 | Out-String).Trim()
    if ($pythonVersion -notmatch "Python\s+(\d+)\.(\d+)") {
        throw "Could not determine Python version. Install Python 3.11 or newer."
    }
    if ([int]$Matches[1] -lt 3 -or ([int]$Matches[1] -eq 3 -and [int]$Matches[2] -lt 11)) {
        throw "$pythonVersion found; Python 3.11 or newer is required."
    }

    $nodeVersion = ((& node --version).Trim() -replace '^v', '')
    if ([version]$nodeVersion -lt [version]'20.0') {
        throw "Node.js $nodeVersion found; Node.js 20 or newer is required."
    }

    Ensure-EnvFile (Join-Path $Root "backend\.env.example") (Join-Path $Root "backend\.env")
    Ensure-EnvFile (Join-Path $Root "agent\.env.example") (Join-Path $Root "agent\.env")
    Ensure-EnvFile (Join-Path $Root "frontend\.env.example") (Join-Path $Root "frontend\.env")

    $backendEnv = Join-Path $Root "backend\.env"
    Set-EnvPlaceholder -Path $backendEnv -Name "DB_PASSWORD" `
        -Placeholder "your_password" -Value "quality_assistance"
    Set-EnvPlaceholder -Path $backendEnv -Name "JWT_SECRET" `
        -Placeholder "change-me-in-production" -Value (New-UrlSafeKey)
    Set-EnvPlaceholder -Path $backendEnv -Name "ENCRYPTION_KEY" `
        -Placeholder "change-me-generate-with-cryptography-fernet" -Value (New-UrlSafeKey -KeepPadding $true)

    $pgHost = Get-EnvValue -Path $backendEnv -Name "DB_HOST" -Default "localhost"
    $pgPort = [int](Get-EnvValue -Path $backendEnv -Name "DB_PORT" -Default "5432")
    Ensure-Postgres -HostName $pgHost -Port $pgPort

    Write-Host "Installing agent and backend Python dependencies..."
    Push-Location (Join-Path $Root "agent")
    try { Invoke-Checked -Command "uv" -Arguments @("sync", "--quiet") }
    finally { Pop-Location }

    Push-Location (Join-Path $Root "backend")
    try { Invoke-Checked -Command "uv" -Arguments @("sync", "--quiet") }
    finally { Pop-Location }

    Write-Host "Installing frontend dependencies..."
    Push-Location (Join-Path $Root "frontend")
    try {
        & yarn install --frozen-lockfile
        if ($LASTEXITCODE -ne 0) { Invoke-Checked -Command "yarn" -Arguments @("install") }
    } finally { Pop-Location }

    Write-Host "Applying database migrations..."
    Push-Location (Join-Path $Root "backend")
    try { Invoke-Checked -Command "uv" -Arguments @("run", "alembic", "upgrade", "head") }
    finally { Pop-Location }

    $agentEnv = Join-Path $Root "agent\.env"
    $agentBackend = Get-EnvValue -Path $agentEnv -Name "AGENT_BACKEND" -Default "gemini"
    $googleApiKey = Get-EnvValue -Path $agentEnv -Name "GOOGLE_API_KEY" -Default ""

    Write-Host ""
    Write-Host "Setup complete. Run the application with: .\scripts\dev.ps1"
    Write-Host "The local secrets are in backend\.env; setup preserves existing non-placeholder values."
    if ($agentBackend -eq "gemini" -and $googleApiKey -like "your-*") {
        Write-Warning "Add a Gemini API key to agent\.env before requesting AI assistance."
    }
} catch {
    Write-Error $_.Exception.Message
    exit 1
}