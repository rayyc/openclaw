# OpenClaw Complete System Starter/Stopper
# Usage: .\run_system.ps1 start
#        .\run_system.ps1 stop
#        .\run_system.ps1

param(
    [string]$Action = "start"
)

$ErrorActionPreference = "Continue"

function Start-OpenClaw {
    Write-Host "[START] Starting OpenClaw System..." -ForegroundColor Green
    Write-Host ""
    
    # Start Docker Compose
    Write-Host "[DOCKER] Starting Docker containers (PostgreSQL, Redis)..." -ForegroundColor Cyan
    docker-compose up -d
    Start-Sleep -Seconds 3
    
    # Activate venv and start backend
    Write-Host "[BACKEND] Starting Backend (Uvicorn on http://127.0.0.1:8000/docs)..." -ForegroundColor Cyan
    $backendProcess = Start-Process powershell -PassThru -WindowStyle Normal -ArgumentList "-NoExit", "-Command", "cd $PSScriptRoot; .\.venv\Scripts\Activate.ps1; uvicorn backend.main:app --reload"
    
    Start-Sleep -Seconds 5

    # Start Celery worker
    Write-Host "[CELERY] Starting Celery Worker (Agent Task Processor)..." -ForegroundColor Cyan
    $celeryProcess = Start-Process powershell -PassThru -WindowStyle Normal -ArgumentList "-NoExit", "-Command", "cd $PSScriptRoot; .\.venv\Scripts\Activate.ps1; celery -A backend.agents.tasks.celery_app worker --loglevel=info --pool=solo"

    Start-Sleep -Seconds 3
    
    # Start frontend
    Write-Host "[FRONTEND] Starting Frontend (Next.js on http://localhost:3000)..." -ForegroundColor Cyan
    $frontendProcess = Start-Process powershell -PassThru -WindowStyle Normal -ArgumentList "-NoExit", "-Command", "cd $PSScriptRoot\frontend; npm run dev"
    
    Start-Sleep -Seconds 3
    
    Write-Host ""
    Write-Host "[OK] System Started!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Frontend:         http://localhost:3000" -ForegroundColor Yellow
    Write-Host "Backend API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Yellow
    Write-Host "PostgreSQL:       localhost:5432" -ForegroundColor Yellow
    Write-Host "Redis:            localhost:6379" -ForegroundColor Yellow
    Write-Host "Celery Worker:    Running (Agent Task Processor)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "[NOTE] To stop the system, run: .\run_system.ps1 stop" -ForegroundColor Cyan
    Write-Host ""
    
    # Save process IDs to file for later stopping (backend, celery, frontend)
    @($backendProcess.Id, $celeryProcess.Id, $frontendProcess.Id) | Out-File -FilePath ".openclaw_pids.txt"
}

function Stop-OpenClaw {
    Write-Host "[STOP] Stopping OpenClaw System..." -ForegroundColor Red
    Write-Host ""
    
    # Stop processes from file
    if (Test-Path ".openclaw_pids.txt") {
        $pids = Get-Content ".openclaw_pids.txt"
        foreach ($processId in $pids) {
            Write-Host "Stopping process $processId..." -ForegroundColor Yellow
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
        Remove-Item ".openclaw_pids.txt" -Force
    }
    
    # Stop all node processes (npm run dev)
    Write-Host "Stopping npm processes..." -ForegroundColor Yellow
    Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

    # Stop Celery workers
    Write-Host "Stopping Celery workers..." -ForegroundColor Yellow
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowTitle -like "*celery*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # Stop Docker containers
    Write-Host "Stopping Docker containers..." -ForegroundColor Yellow
    docker-compose down
    
    Write-Host ""
    Write-Host "[OK] System Stopped!" -ForegroundColor Green
}

# Main
if ($Action -eq "stop") {
    Stop-OpenClaw
} else {
    Start-OpenClaw
}