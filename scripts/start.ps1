$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $projectRoot "backend"
$frontendPath = Join-Path $projectRoot "frontend"

if (-not (Test-Path (Join-Path $backendPath ".venv\Scripts\python.exe"))) {
    throw "Backend virtual environment not found. Follow README.md to install dependencies first."
}
if (-not (Test-Path (Join-Path $frontendPath "node_modules"))) {
    throw "Frontend dependencies not found. Run pnpm install in frontend first."
}

Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoExit", "-Command", "Set-Location '$backendPath'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendPath'; .\node_modules\.bin\next.cmd dev"
Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:3000"

