# Backend startup script for Windows PowerShell
# Runs the FastAPI server from the project root with correct Python path

Write-Host "Starting OpenClaw Backend..." -ForegroundColor Cyan

# Ensure we're in the project root
Push-Location $PSScriptRoot

# Activate virtual environment if not already activated
if (-not (Test-Path env:VIRTUAL_ENV)) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
}

# Start Uvicorn from project root (so backend.* imports work)
Write-Host "Starting Uvicorn server on http://127.0.0.1:8000" -ForegroundColor Green
uvicorn backend.main:app --reload --port 8000 --host 127.0.0.1

Pop-Location
