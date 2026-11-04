# MiniDAQ GUI setup for Windows (replaces install_native.sh, which is Linux-only).
#
#   powershell -ExecutionPolicy Bypass -File .\install_windows.ps1 [-Python 3.11] [-SkipPythonDeps] [-SkipTests]
#
# 1. Checks for the packet driver (Npcap; legacy WinPcap also works).
# 2. Creates GUI_DAQ\.venv and installs requirements-windows.txt.
# 3. Builds the optional C++ extensions (native decoder, track fitter) if MSVC
#    Build Tools are installed; without them the GUI uses the Python decoder and
#    track fitting is disabled.
# 4. Runs the Npcap self-test and the capture parity tests.
#
# The Linux helpers in native_capture\ (setcap'd libpcap programs) are not built
# on Windows: win_pcap.py and win_capture.py provide the same services in-process.

param(
    [string]$Python = "3.11",
    [switch]$SkipPythonDeps,
    [switch]$SkipTests
)
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

# --- 1. packet driver ----------------------------------------------------------
$npcap  = Join-Path $env:SystemRoot "System32\Npcap\wpcap.dll"
$compat = Join-Path $env:SystemRoot "System32\wpcap.dll"
if (Test-Path $npcap) {
    Write-Host "Packet driver: Npcap ($npcap)"
} elseif (Test-Path $compat) {
    $product = (Get-Item $compat).VersionInfo.ProductName
    Write-Host "Packet driver: $product ($compat)"
    if ($product -match "WinPcap") {
        Write-Warning "WinPcap is unmaintained. Npcap (https://npcap.com) is recommended; tick 'WinPcap API-compatible mode' or not, both work."
    }
} else {
    throw "No packet driver found. Install Npcap from https://npcap.com, then run this script again."
}

# --- 2. virtual environment and Python packages -------------------------------
$venv = Join-Path $root ".venv"
$py = Join-Path $venv "Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "Creating virtual environment with Python $Python ..."
    & py "-$Python" -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw "Could not create $venv with 'py -$Python'." }
}
Write-Host ("Using " + (& $py --version))

if (-not $SkipPythonDeps) {
    & $py -m pip install --upgrade pip setuptools wheel
    if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed" }
    & $py -m pip install -r (Join-Path $root "requirements-windows.txt")
    if ($LASTEXITCODE -ne 0) { throw "Installing requirements-windows.txt failed" }
}

# --- 3. optional C++ extensions -------------------------------------------------
$vswhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
$haveMsvc = $false
if (Test-Path $vswhere) {
    $vs = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    $haveMsvc = [bool]$vs
}
if ($haveMsvc) {
    Write-Host "Building optional C++ extensions with MSVC ..."
    & $py -m pip install --no-build-isolation -e (Join-Path $root "cppfit")
    if ($LASTEXITCODE -ne 0) { Write-Warning "Track fitter (cppfit) build failed; track fitting stays disabled." }
    Push-Location (Join-Path $root "native_decoder")
    & $py setup.py build_ext --inplace
    if ($LASTEXITCODE -ne 0) { Write-Warning "Native decoder build failed; the Python decoder is used." }
    Pop-Location
} else {
    Write-Host "MSVC Build Tools not found: skipping the optional C++ extensions (Python decoder, no track fitting)."
}

# --- 4. checks -------------------------------------------------------------------
& $py (Join-Path $root "win_pcap.py")
if ($LASTEXITCODE -ne 0) { throw "Npcap self-test failed" }
if (-not $SkipTests) {
    & $py -m unittest test_win_capture
    if ($LASTEXITCODE -ne 0) { throw "Capture parity tests failed" }
}

Write-Host ""
Write-Host "Done. Start the GUI with:"
Write-Host "  $py $(Join-Path $root 'GUI_DAQ_init.py')"
