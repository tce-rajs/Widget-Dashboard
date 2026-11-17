<#
.SYNOPSIS
    One-click automated update script for Widget Dashboard.
.DESCRIPTION
    Re-scans Excel spreadsheet, verifies 294+ widgets on disk, regenerates dashboard HTML,
    and synchronizes with D:\Projects\widget-dashboard.
.PARAMETER File
    Optional path to an updated Excel spreadsheet (.xlsx).
.PARAMETER Push
    Automatically commit and push changes to GitHub.
.EXAMPLE
    .\update_dashboard.ps1
    .\update_dashboard.ps1 -File "C:\path\to\Widgets.xlsx"
    .\update_dashboard.ps1 -Push
#>

param (
    [string]$File = "",
    [switch]$Push
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pyScript = Join-Path $scriptDir "scripts\update_dashboard.py"

if (-not (Test-Path $pyScript)) {
    Write-Host "[ERROR] Could not find scripts\update_dashboard.py at $pyScript" -ForegroundColor Red
    exit 1
}

$argsList = @()
if ($File) { $argsList += "`"$File`"" }
if ($Push) { $argsList += "--push" }

python $pyScript @argsList
