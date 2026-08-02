# =============================================================================
# validate-all.ps1 - EvoRule SDK one-stop validation orchestrator
# Runs: validate-version + validate-changelog + validate-license + validate-release + check_doc_safety
# =============================================================================
param(
    [switch]$PreRelease
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$scriptsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$failed = $false

if ($PreRelease) {
    Write-Host "=== Validate-All Mode: PRE-RELEASE ===" -ForegroundColor Magenta
    Write-Host "(skip tag check, allow [Unreleased])"
} else {
    Write-Host "=== Validate-All Mode: STRICT (post-release) ===" -ForegroundColor Magenta
}

Write-Host ""

# --- 1. validate-version ---
Write-Host ">>> [validate-version] <<<" -ForegroundColor Cyan
& (Join-Path $scriptsDir "validate-version.ps1")
if ($LASTEXITCODE -ne 0) { $failed = $true }
Write-Host ""

# --- 2. validate-changelog ---
Write-Host ">>> [validate-changelog] <<<" -ForegroundColor Cyan
if ($PreRelease) {
    & (Join-Path $scriptsDir "validate-changelog.ps1") -AllowUnreleased
} else {
    & (Join-Path $scriptsDir "validate-changelog.ps1")
}
if ($LASTEXITCODE -ne 0) { $failed = $true }
Write-Host ""

# --- 3. validate-license ---
Write-Host ">>> [validate-license] <<<" -ForegroundColor Cyan
& (Join-Path $scriptsDir "validate-license.ps1")
if ($LASTEXITCODE -ne 0) { $failed = $true }
Write-Host ""

# --- 4. validate-release ---
Write-Host ">>> [validate-release] <<<" -ForegroundColor Cyan
if ($PreRelease) {
    & (Join-Path $scriptsDir "validate-release.ps1") -SkipTagCheck
} else {
    & (Join-Path $scriptsDir "validate-release.ps1")
}
if ($LASTEXITCODE -ne 0) { $failed = $true }
Write-Host ""

# --- 5. check_doc_safety ---
Write-Host ">>> [check_doc_safety] <<<" -ForegroundColor Cyan
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}
if ($pythonCmd) {
    & $pythonCmd.Source (Join-Path $scriptsDir "check_doc_safety.py") --skip-git
    if ($LASTEXITCODE -ne 0) { $failed = $true }
} else {
    Write-Host "[FAIL] Python not found, cannot run check_doc_safety.py" -ForegroundColor Red
    $failed = $true
}
Write-Host ""

# --- Summary ---
Write-Host "=========== SUMMARY ===========" -ForegroundColor Cyan
if ($failed) {
    Write-Host "SOME CHECKS FAILED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "ALL CHECKS PASSED" -ForegroundColor Green
    exit 0
}
