@echo off
setlocal
title Widget Comparison Dashboard Local Server
cd /d "%~dp0"

echo ======================================================================
echo                WIDGET DASHBOARD LOCAL WEB SERVER
echo ======================================================================
echo.
echo Starting Python HTTP server on port 8000...
echo Dashboard URL: http://localhost:8000/index.html
echo.
echo Opening your default browser...
start http://localhost:8000/index.html
echo.
echo ----------------------------------------------------------------------
echo  Web server is active.
echo  All 203 interactive simulations with audio and JSON run seamlessly.
echo  Keep this window open while using the dashboard.
echo  Press Ctrl+C or close this window to stop.
echo ----------------------------------------------------------------------
echo.

python -m http.server 8000
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Port 8000 is occupied, starting on port 8080...
    start http://localhost:8080/index.html
    python -m http.server 8080
)

pause
