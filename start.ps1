# Kisan Mitra AI — One-Click Hackathon Startup Script
# ===================================================

Clear-Host
Write-Host "==================================================" -ForegroundColor Emerald
Write-Host "                KISAN MITRA AI                   " -ForegroundColor Emerald
Write-Host "     HACKATHON DEMO STARTUP CONTROLLER v2.5      " -ForegroundColor Emerald
Write-Host "==================================================" -ForegroundColor Emerald
Write-Host ""

# Check Python environment
Write-Host "[*] Checking Python availability..." -ForegroundColor Cyan
if (Get-Command "python" -ErrorAction SilentlyContinue) {
    $pythonVer = & python --version
    Write-Host "  Found: $pythonVer" -ForegroundColor Green
} else {
    Write-Host "  [!] Error: Python not found in system PATH." -ForegroundColor Red
    Exit
}

# Check Node environment
Write-Host "[*] Checking Node.js & npm availability..." -ForegroundColor Cyan
if (Get-Command "node" -ErrorAction SilentlyContinue) {
    $nodeVer = & node --version
    Write-Host "  Found Node: $nodeVer" -ForegroundColor Green
} else {
    Write-Host "  [!] Error: Node.js not found in system PATH." -ForegroundColor Red
    Exit
}

# Check directory structure
$baseDir = "C:\Users\Admin\Desktop\kisan-mitra-ai"
if (-not (Test-Path "$baseDir\backend") -or -not (Test-Path "$baseDir\frontend")) {
    Write-Host "  [!] Error: Current directory does not look like the Kisan Mitra repository." -ForegroundColor Red
    Exit
}

# Startup Backend in new window
Write-Host "[+] Launching FastAPI Backend (Port 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $baseDir\backend; uvicorn app.main:app --reload --port 8000"

# Wait briefly
Start-Sleep -Seconds 2

# Startup Frontend in new window
Write-Host "[+] Launching Next.js Frontend (Port 3000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $baseDir\frontend; npm run dev"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "  Success: Live servers started in background!" -ForegroundColor Green
Write-Host "  1. Live Dashboard: http://localhost:3000" -ForegroundColor Green
Write-Host "  2. API Documentation: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Keep this window open or press Ctrl+C to terminate."
