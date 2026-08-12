#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Bad_Usb_Forge — automated Windows installer.

.DESCRIPTION
  Detects Python 3.8+, creates a dedicated venv in %USERPROFILE%\.auto-flipper-tools\venv,
  installs the package (from the local repo if the script is run from a
  checkout, otherwise clones the repo), and creates .cmd wrappers in a
  folder added to the user PATH. Never installs anything with admin
  elevation.

.EXAMPLE
  irm https://raw.githubusercontent.com/TFD-42/Bad_Usb_Forge/main/scripts/install.ps1 | iex
.EXAMPLE
  # from a local clone:
  .\scripts\install.ps1
#>

$ErrorActionPreference = "Stop"

$RepoUrl     = "https://github.com/TFD-42/Bad_Usb_Forge.git"
$InstallRoot = if ($env:AUTO_FLIPPER_HOME) { $env:AUTO_FLIPPER_HOME } else { Join-Path $env:USERPROFILE ".auto-flipper-tools" }
$VenvDir     = Join-Path $InstallRoot "venv"
$BinDir      = Join-Path $InstallRoot "bin"
$MinMajor    = 3
$MinMinor    = 8

function Log($msg)  { Write-Host "[install] $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "[warn] $msg" -ForegroundColor Yellow }
function Die($msg)  { Write-Host "[error] $msg" -ForegroundColor Red; exit 1 }

function Find-Python {
    foreach ($candidate in @("python3.12", "python3.11", "python3.10", "python3.9", "python3.8", "python3", "python", "py")) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        try {
            $verOut = & $candidate -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null
        } catch { continue }
        if (-not $verOut) { continue }
        $parts = $verOut.Trim().Split(".")
        if ([int]$parts[0] -eq $MinMajor -and [int]$parts[1] -ge $MinMinor) {
            return $candidate
        }
    }
    return $null
}

Log "Detected OS: windows"

$PythonBin = Find-Python
if (-not $PythonBin) {
    Warn "Python $MinMajor.$MinMinor+ not found."
    Warn "Install it from https://www.python.org/downloads/windows/ (check 'Add python.exe to PATH')"
    Warn "or via winget: winget install Python.Python.3.12"
    Die "Installation aborted — Python missing."
}
Log "Using Python: $PythonBin ($(& $PythonBin --version 2>&1))"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Die "git is required but was not found. Install it (https://git-scm.com/download/win), then re-run this script."
}

# Detects a local checkout (script run from the repo) otherwise clones.
# $MyInvocation.MyCommand.Path is empty when the script arrives via
# `irm ... | iex` (no local file) — in that case we always clone.
$ScriptPath = $MyInvocation.MyCommand.Path
$PyprojectPath = $null
if ($ScriptPath) {
    $ScriptDir = Split-Path -Parent $ScriptPath
    $RepoDir   = Split-Path -Parent $ScriptDir
    $PyprojectPath = Join-Path $RepoDir "pyproject.toml"
}
if ($PyprojectPath -and (Test-Path $PyprojectPath) -and (Select-String -Path $PyprojectPath -Pattern '^name = "auto-flipper-tools"' -Quiet)) {
    Log "Local repo detected: $RepoDir"
    $SourceDir = $RepoDir
} else {
    $SourceDir = Join-Path $InstallRoot "src"
    if (Test-Path (Join-Path $SourceDir ".git")) {
        Log "Updating the existing repo..."
        git -C $SourceDir pull --ff-only
    } else {
        Log "Cloning the repo into $SourceDir..."
        New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
        git clone --depth 1 $RepoUrl $SourceDir
    }
}

Log "Creating the venv in $VenvDir..."
& $PythonBin -m venv $VenvDir

$VenvPip    = Join-Path $VenvDir "Scripts\pip.exe"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

Log "Installing the package..."
& $VenvPython -m pip install --upgrade -q pip
& $VenvPip install -q $SourceDir

New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
foreach ($cmd in @("badusb-pipeline", "badusb-classify", "badusb-setup-agent", "badusb-discover")) {
    $wrapperPath = Join-Path $BinDir "$cmd.cmd"
    $targetExe   = Join-Path $VenvDir "Scripts\$cmd.exe"
    "@echo off`r`n`"$targetExe`" %*" | Set-Content -Path $wrapperPath -Encoding ASCII
}

Log "Installed. Available commands: badusb-pipeline, badusb-classify, badusb-setup-agent, badusb-discover"

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$BinDir", "User")
    Warn "$BinDir added to your user PATH — open a NEW terminal for it to take effect."
} else {
    Log "$BinDir is already in the PATH."
}

Log "Quick test:"
& (Join-Path $BinDir "badusb-pipeline.cmd") --help | Select-Object -First 3

Log "Ready. Example: badusb-pipeline C:\path\to\your\badusb\scripts"
