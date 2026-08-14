# Kisan Mitra AI — One-Click Hackathon Startup Script
# ===================================================

Clear-Host
Write-Host "==================================================" -ForegroundColor Green
Write-Host "                KISAN MITRA AI                   " -ForegroundColor Green
Write-Host "     HACKATHON DEMO STARTUP CONTROLLER v2.5      " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

# Check Python availability
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

# Get local Wi-Fi IP address for mobile access
$localIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -like "*Wi-Fi*" -and $_.IPAddress -like "10.*" } | Select-Object -ExpandProperty IPAddress -First 1)
if (-not $localIp) { $localIp = "10.230.52.36" }

# Startup Backend in new window
Write-Host "[+] Launching FastAPI Backend (Port 8000 on 0.0.0.0)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $baseDir\backend; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# Wait briefly
Start-Sleep -Seconds 2

# Startup Frontend in new window
Write-Host "[+] Launching Next.js Frontend (Port 3000 on 0.0.0.0)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $baseDir\frontend; npx next dev -H 0.0.0.0 -p 3000"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "  Success: Live servers started on Network!" -ForegroundColor Green
Write-Host "  1. PC Dashboard:   http://localhost:3000" -ForegroundColor Green
Write-Host "  2. Mobile Phone:   http://$($localIp):3000" -ForegroundColor Yellow
Write-Host "  3. API Docs:       http://localhost:8000/docs" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Connect your phone to the same Wi-Fi network and open http://$($localIp):3000"

