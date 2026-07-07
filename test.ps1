# test.ps1 - Start Sagittarius Log Viewer and the Dummy Log Generator for testing

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Locate the Python executable in the virtual environment
$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    $VenvPython = Join-Path $ScriptDir ".venv/bin/python"
}
if (-not (Test-Path $VenvPython)) {
    Write-Warning "Virtual environment Python not found. Falling back to system python..."
    $VenvPython = "python"
}

Write-Host "Starting Dummy Log Generator in the background..." -ForegroundColor Cyan
$GeneratorJob = Start-Job -Name "SagittariusDummyGenerator" -ScriptBlock {
    param($python, $dir)
    Set-Location $dir
    & $python tools/log_generator.py --port 9999 --rate 2.0 --pattern mixed
} -ArgumentList $VenvPython, $ScriptDir

# Give the generator a moment to boot (it will auto-retry connecting)
Start-Sleep -Seconds 1

Write-Host "Starting Sagittarius Log Viewer..." -ForegroundColor Green
Write-Host "Logs from the generator will start showing up immediately." -ForegroundColor Green
Write-Host "Closing the Log Viewer window will automatically stop the dummy generator." -ForegroundColor Yellow

# Run the Log Viewer in the foreground
& $VenvPython -m logview --port 9999

Write-Host "Stopping Dummy Log Generator..." -ForegroundColor Cyan
Stop-Job $GeneratorJob
Remove-Job $GeneratorJob
Write-Host "Done!" -ForegroundColor Green
