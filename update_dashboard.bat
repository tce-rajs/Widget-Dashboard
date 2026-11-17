@echo off
setlocal enabledelayedexpansion

title Widget Dashboard - One-Click Update

echo ======================================================================
echo           WIDGET DASHBOARD - ONE-CLICK AUTO-UPDATE
echo ======================================================================
echo.

set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%scripts\update_dashboard.py

if not exist "%PYTHON_SCRIPT%" (
    echo [ERROR] Could not find scripts\update_dashboard.py
    echo Looked in: %PYTHON_SCRIPT%
    echo.
    pause
    exit /b 1
)

:: Check if user passed or dragged a file onto this .bat
if "%~1"=="" (
    echo Checking for latest Excel spreadsheet automatically...
    python "%PYTHON_SCRIPT%"
) else (
    echo Processing file: "%~1"
    python "%PYTHON_SCRIPT%" "%~1"
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Update process encountered an issue. See above for details.
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ----------------------------------------------------------------------
set /p PUSH_CHOICE="Do you want to commit and push changes to GitHub now? (y/N): "
if /i "!PUSH_CHOICE!"=="y" (
    echo.
    python "%PYTHON_SCRIPT%" --push
) else (
    echo.
    echo Changes kept locally. Push whenever you are ready.
)

echo.
echo ======================================================================
echo Update complete. Press any key to close.
pause >nul
