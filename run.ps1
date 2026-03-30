# Build frontend and run backend on single localhost:5000

Write-Host "Starting Library System Application..." -ForegroundColor Green
Write-Host ""

# Activate venv
& .\.venv\Scripts\Activate.ps1

# Build frontend
Write-Host "Building frontend..." -ForegroundColor Cyan
Set-Location "frontend"
npm install
npm run build

Set-Location ".."

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "Build complete! Starting backend server..." -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Application running at: http://localhost:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop..." -ForegroundColor Yellow
Write-Host ""

# Start backend
python -m backend.app
