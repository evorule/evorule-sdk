# =============================================================================
# validate-changelog.ps1 - EvoRule SDK CHANGELOG validation
# Checks: root CHANGELOG.md + per-language CHANGELOG.md
# =============================================================================
param(
    [switch]$AllowUnreleased
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$failed = $false

Write-Host "=== Changelog Validation ===" -ForegroundColor Cyan

# --- Get canonical version from Python pyproject.toml ---
$pyproject = Join-Path $repoRoot "python\pyproject.toml"
$canonicalVersion = $null
if (Test-Path $pyproject) {
    $content = Get-Content $pyproject -Raw -Encoding UTF8
    if ($content -match 'version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"') {
        $canonicalVersion = $Matches[1]
    }
}

# --- Check root CHANGELOG.md ---
$rootChangelog = Join-Path $repoRoot "CHANGELOG.md"
if (Test-Path $rootChangelog) {
    $content = Get-Content $rootChangelog -Raw -Encoding UTF8
    if ($canonicalVersion) {
        $escapedVersion = [regex]::Escape($canonicalVersion)
        $sectionPattern = "##\s*\[($escapedVersion)\]"
        if ($content -match $sectionPattern) {
            Write-Host "[OK]   root CHANGELOG has '## [$canonicalVersion]'" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] root CHANGELOG missing '## [$canonicalVersion]'" -ForegroundColor Red
            $failed = $true
        }
    }
    if (-not $AllowUnreleased) {
        if ($content -match '##\s*\[Unreleased\]') {
            Write-Host "[FAIL] root CHANGELOG has [Unreleased] section (not allowed in release mode)" -ForegroundColor Red
            $failed = $true
        }
    }
} else {
    Write-Host "[FAIL] root CHANGELOG.md not found" -ForegroundColor Red
    $failed = $true
}

# --- Check per-language CHANGELOGs ---
$langChangelogs = @(
    @{ Name = 'python';     Path = (Join-Path $repoRoot "python\CHANGELOG.md") }
    @{ Name = 'typescript'; Path = (Join-Path $repoRoot "typescript\CHANGELOG.md") }
    @{ Name = 'java';       Path = (Join-Path $repoRoot "java\CHANGELOG.md") }
)

foreach ($cl in $langChangelogs) {
    if (-not (Test-Path $cl.Path)) {
        Write-Host "[SKIP] $($cl.Name) : CHANGELOG.md not found (optional)" -ForegroundColor Yellow
        continue
    }
    $content = Get-Content $cl.Path -Raw -Encoding UTF8
    if ($canonicalVersion) {
        $escapedVersion = [regex]::Escape($canonicalVersion)
        $sectionPattern = "##\s*\[($escapedVersion)\]"
        if ($content -match $sectionPattern) {
            Write-Host "[OK]   $($cl.Name) : CHANGELOG has '## [$canonicalVersion]'" -ForegroundColor Green
        } else {
            Write-Host "[WARN] $($cl.Name) : CHANGELOG missing '## [$canonicalVersion]' (may use different version)" -ForegroundColor Yellow
        }
    }
    if (-not $AllowUnreleased) {
        if ($content -match '##\s*\[Unreleased\]') {
            Write-Host "[FAIL] $($cl.Name) : CHANGELOG has [Unreleased] section" -ForegroundColor Red
            $failed = $true
        }
    }
}

if ($AllowUnreleased) {
    Write-Host "[INFO] -AllowUnreleased set, skipping [Unreleased] check (dev mode)" -ForegroundColor Yellow
}

Write-Host ""
if ($failed) {
    Write-Host "[RESULT] FAILED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "[RESULT] PASSED" -ForegroundColor Green
    exit 0
}
