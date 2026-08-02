# =============================================================================
# validate-release.ps1 - EvoRule SDK release/tag validation
# Multi-language independent tag strategy: go-v / python-v / ts-v / java-v
# =============================================================================
param(
    [switch]$SkipTagCheck
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$failed = $false

Write-Host "=== Release Validation ===" -ForegroundColor Cyan

# --- Get canonical version ---
$pyproject = Join-Path $repoRoot "python\pyproject.toml"
$canonicalVersion = $null
if (Test-Path $pyproject) {
    $content = Get-Content $pyproject -Raw -Encoding UTF8
    if ($content -match 'version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"') {
        $canonicalVersion = $Matches[1]
    }
}

if ($canonicalVersion) {
    Write-Host "[INFO] Current version: $canonicalVersion" -ForegroundColor Yellow
} else {
    Write-Host "[FAIL] Cannot determine current version" -ForegroundColor Red
    exit 1
}

# --- Tag format validation (multi-language) ---
$tagPrefixes = @('go-v', 'python-v', 'ts-v', 'java-v')
$expectedTags = $tagPrefixes | ForEach-Object { "$_$canonicalVersion" }

if ($SkipTagCheck) {
    Write-Host "[INFO] -SkipTagCheck set, skipping tag existence check (pre-release)" -ForegroundColor Yellow
} else {
    foreach ($tag in $expectedTags) {
        $tagExists = git tag --list $tag 2>$null
        if ($tagExists) {
            Write-Host "[OK]   git tag '$tag' exists" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] git tag '$tag' does not exist" -ForegroundColor Red
            $failed = $true
        }
    }
}

# --- Check no greater tag exists ---
$allTags = git tag --list 2>$null
if ($allTags) {
    foreach ($prefix in $tagPrefixes) {
        $langTags = $allTags | Where-Object { $_ -match "^$prefix([0-9]+\.[0-9]+\.[0-9]+)$" }
        foreach ($t in $langTags) {
            $tagVer = $t -replace "^$prefix", ''
            $tagParts = $tagVer -split '\.' | ForEach-Object { [int]$_ }
            $curParts = $canonicalVersion -split '\.' | ForEach-Object { [int]$_ }
            $greater = $false
            for ($i = 0; $i -lt 3; $i++) {
                if ($tagParts[$i] -gt $curParts[$i]) { $greater = $true; break }
                if ($tagParts[$i] -lt $curParts[$i]) { break }
            }
            if ($greater) {
                Write-Host "[FAIL] Found greater tag: $t (current: $canonicalVersion)" -ForegroundColor Red
                $failed = $true
            }
        }
    }
}

Write-Host "[INFO] Stable version, ready for release" -ForegroundColor Yellow

Write-Host ""
if ($failed) {
    Write-Host "[RESULT] FAILED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "[RESULT] PASSED" -ForegroundColor Green
    exit 0
}
