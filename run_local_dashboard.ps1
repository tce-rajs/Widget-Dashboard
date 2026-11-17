# Run Local Widget Dashboard Server
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "                WIDGET DASHBOARD LOCAL WEB SERVER" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting Python HTTP server on port 8000..." -ForegroundColor White
Write-Host "Dashboard URL: http://localhost:8000/index.html" -ForegroundColor Green
Write-Host ""
Write-Host "Opening your default browser..." -ForegroundColor Gray
Start-Process "http://localhost:8000/index.html"

Write-Host ""
Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host " Web server is active. Keep this window open while using the dashboard." -ForegroundColor White
Write-Host " Press Ctrl+C to stop the server anytime." -ForegroundColor Gray
Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

try {
    python -m http.server 8000
} catch {
    Write-Host "Port 8000 occupied, trying 8080..." -ForegroundColor Yellow
    Start-Process "http://localhost:8080/index.html"
    python -m http.server 8080
}
