# start.ps1 - Activate virtual environment and launch Sagittarius Log Viewer

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvActivate = Join-Path $ScriptDir ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $VenvActivate)) {
    $VenvActivate = Join-Path $ScriptDir ".venv\bin\Activate.ps1"
}

if (-not (Test-Path $VenvActivate)) {
    Write-Error "Virtual environment not found at: $VenvActivate"
    Write-Host "Run: python -m venv .venv  then  pip install -r requirements.txt"
    exit 1
}

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
. $VenvActivate

Write-Host "Starting Sagittarius Log Viewer..." -ForegroundColor Green
Set-Location $ScriptDir
python -m logview @args
