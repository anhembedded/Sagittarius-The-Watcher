#Requires -Version 5.1
<#
.SYNOPSIS
    Local CI runner - mirrors the GitHub Actions CI pipeline for Log Viewer.

.DESCRIPTION
    Runs Ruff lint, Ruff format check, and Pytest with coverage locally.
    Use this to validate your changes before pushing.

.PARAMETER SkipLint
    Skip Ruff lint and format check steps.

.PARAMETER SkipTests
    Skip Pytest step.

.PARAMETER SanityOnly
    Run only tests/unit/test_engine_integration_sanity.py. Implies -SkipLint.

.PARAMETER UnitOnly
    Run only tests/unit. Implies -SkipLint.

.PARAMETER Full
    Explicit alias for the default behavior: lint + format + the full test suite.

.EXAMPLE
    .\scripts\ci-local.ps1
    .\scripts\ci-local.ps1 -SkipLint
    .\scripts\ci-local.ps1 -SkipTests
    .\scripts\ci-local.ps1 -SanityOnly
    .\scripts\ci-local.ps1 -UnitOnly
    .\scripts\ci-local.ps1 -Full
#>
[CmdletBinding()]
param(
    [switch]$SkipLint,
    [switch]$SkipTests,
    [switch]$SanityOnly,
    [switch]$UnitOnly,
    [switch]$Full
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Name)
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  ▶  $Name" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Name)
    Write-Host "  ✅  $Name passed" -ForegroundColor Green
}

function Write-Failure {
    param([string]$Name)
    Write-Host "  ❌  $Name FAILED" -ForegroundColor Red
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$logviewerRoot = Split-Path -Parent $scriptDir

# ---------------------------------------------------------------------------
# Resolve which test tier to run and whether coverage/lint apply.
# ---------------------------------------------------------------------------
$pytestTarget = "tests"
$useCoverage = $true
$enforceCoverageGate = $true

if ($SanityOnly) {
    $pytestTarget = "tests/unit/test_engine_integration_sanity.py"
    $useCoverage = $false
    $enforceCoverageGate = $false
    $SkipLint = $true
} elseif ($UnitOnly) {
    $pytestTarget = "tests/unit"
    $enforceCoverageGate = $false
    $SkipLint = $true
}

$venvActivateWin = Join-Path $logviewerRoot ".venv\Scripts\Activate.ps1"
$venvActivateLin = Join-Path $logviewerRoot ".venv/bin/activate"

if (Test-Path $venvActivateWin) {
    Write-Host "Activating venv (Windows)..." -ForegroundColor DarkGray
    . $venvActivateWin
} elseif (Test-Path $venvActivateLin) {
    Write-Host "Activating venv (Linux)..." -ForegroundColor DarkGray
    $env:PATH = "$(Join-Path $logviewerRoot '.venv/bin'):$env:PATH"
} else {
    Write-Warning "Virtual environment not found. Using system Python."
}

$failed = @()

if (-not $SkipLint) {
    Write-Step "Ruff — Lint (ruff check logview tests)"
    Push-Location $logviewerRoot
    try {
        python -m ruff check logview tests
        if ($LASTEXITCODE -ne 0) { $failed += "Ruff Lint"; Write-Failure "Ruff Lint" }
        else { Write-Success "Ruff Lint" }
    } catch {
        $failed += "Ruff Lint"; Write-Failure "Ruff Lint"
        Write-Host $_.Exception.Message -ForegroundColor Yellow
    } finally { Pop-Location }

    Write-Step "Ruff — Format Check (ruff format --check logview tests)"
    Push-Location $logviewerRoot
    try {
        python -m ruff format --check logview tests
        if ($LASTEXITCODE -ne 0) { $failed += "Ruff Format"; Write-Failure "Ruff Format" }
        else { Write-Success "Ruff Format" }
    } catch {
        $failed += "Ruff Format"; Write-Failure "Ruff Format"
        Write-Host $_.Exception.Message -ForegroundColor Yellow
    } finally { Pop-Location }
}

if (-not $SkipTests) {
    Write-Step "Pytest ($pytestTarget)"
    Push-Location $logviewerRoot
    try {
        # LogViewer depends on sagittarius_engine which is 2 levels up
        $env:PYTHONPATH = "$logviewerRoot;$logviewerRoot\..\.."
        $env:QT_QPA_PLATFORM = "offscreen"

        $pytestArgs = @($pytestTarget, "-v")
        if ($useCoverage) {
            $pytestArgs += "--cov=logview"
            $pytestArgs += "--cov-report=term-missing"
            if ($enforceCoverageGate) { $pytestArgs += "--cov-fail-under=50" }
        }

        python -m pytest @pytestArgs
        if ($LASTEXITCODE -ne 0) { $failed += "Pytest"; Write-Failure "Pytest" }
        else { Write-Success "Pytest" }
    } catch {
        $failed += "Pytest"; Write-Failure "Pytest"
        Write-Host $_.Exception.Message -ForegroundColor Yellow
    } finally { Pop-Location }
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
if ($failed.Count -eq 0) {
    Write-Host "  🎉  All checks passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "  💥  Failed steps: $($failed -join ', ')" -ForegroundColor Red
    exit 1
}
