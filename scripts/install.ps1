#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Auto-Flipper-Tools — installateur automatisé Windows.

.DESCRIPTION
  Détecte Python 3.8+, crée un venv dédié dans %USERPROFILE%\.auto-flipper-tools\venv,
  installe le package (depuis le dépôt local si le script est lancé depuis un
  checkout, sinon clone le dépôt), et crée des wrappers .cmd dans un dossier
  ajouté au PATH utilisateur. N'installe jamais rien en admin/élévation.

.EXAMPLE
  irm https://raw.githubusercontent.com/TFD-42/Auto-Flipper-Tools/main/scripts/install.ps1 | iex
.EXAMPLE
  # depuis un clone local:
  .\scripts\install.ps1
#>

$ErrorActionPreference = "Stop"

$RepoUrl     = "https://github.com/TFD-42/Auto-Flipper-Tools.git"
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

Log "OS détecté: windows"

$PythonBin = Find-Python
if (-not $PythonBin) {
    Warn "Python $MinMajor.$MinMinor+ introuvable."
    Warn "Installe-le depuis https://www.python.org/downloads/windows/ (coche 'Add python.exe to PATH')"
    Warn "ou via winget: winget install Python.Python.3.12"
    Die "Installation interrompue — Python manquant."
}
Log "Python utilisé: $PythonBin ($(& $PythonBin --version 2>&1))"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Die "git est requis mais introuvable. Installe-le (https://git-scm.com/download/win) puis relance ce script."
}

# Repère un checkout local (script lancé depuis le dépôt) sinon clone.
# $MyInvocation.MyCommand.Path est vide quand le script arrive via
# `irm ... | iex` (pas de fichier local) — dans ce cas on clone toujours.
$ScriptPath = $MyInvocation.MyCommand.Path
$PyprojectPath = $null
if ($ScriptPath) {
    $ScriptDir = Split-Path -Parent $ScriptPath
    $RepoDir   = Split-Path -Parent $ScriptDir
    $PyprojectPath = Join-Path $RepoDir "pyproject.toml"
}
if ($PyprojectPath -and (Test-Path $PyprojectPath) -and (Select-String -Path $PyprojectPath -Pattern '^name = "auto-flipper-tools"' -Quiet)) {
    Log "Dépôt local détecté: $RepoDir"
    $SourceDir = $RepoDir
} else {
    $SourceDir = Join-Path $InstallRoot "src"
    if (Test-Path (Join-Path $SourceDir ".git")) {
        Log "Mise à jour du dépôt existant..."
        git -C $SourceDir pull --ff-only
    } else {
        Log "Clonage du dépôt dans $SourceDir..."
        New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
        git clone --depth 1 $RepoUrl $SourceDir
    }
}

Log "Création du venv dans $VenvDir..."
& $PythonBin -m venv $VenvDir

$VenvPip    = Join-Path $VenvDir "Scripts\pip.exe"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

Log "Installation du package..."
& $VenvPython -m pip install --upgrade -q pip
& $VenvPip install -q $SourceDir

New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
foreach ($cmd in @("badusb-pipeline", "badusb-classify", "badusb-setup-agent", "badusb-discover")) {
    $wrapperPath = Join-Path $BinDir "$cmd.cmd"
    $targetExe   = Join-Path $VenvDir "Scripts\$cmd.exe"
    "@echo off`r`n`"$targetExe`" %*" | Set-Content -Path $wrapperPath -Encoding ASCII
}

Log "Installé. Commandes disponibles: badusb-pipeline, badusb-classify, badusb-setup-agent, badusb-discover"

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$BinDir", "User")
    Warn "$BinDir ajouté à ton PATH utilisateur — ouvre un NOUVEAU terminal pour que ça prenne effet."
} else {
    Log "$BinDir est déjà dans le PATH."
}

Log "Test rapide:"
& (Join-Path $BinDir "badusb-pipeline.cmd") --help | Select-Object -First 3

Log "Prêt. Exemple: badusb-pipeline C:\chemin\vers\tes\scripts\badusb"
