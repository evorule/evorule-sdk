# =============================================================================
# validate-license.ps1 - EvoRule SDK license validation
# Checks: LICENSE contains Apache-2.0 + source files have SPDX headers
# =============================================================================
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$failed = $false

Write-Host "=== License Validation ===" -ForegroundColor Cyan

# --- Check root LICENSE ---
$licensePath = Join-Path $repoRoot "LICENSE"
if (Test-Path $licensePath) {
    $content = Get-Content $licensePath -Raw -Encoding UTF8
    if ($content -match 'Apache License|Apache-2\.0') {
        Write-Host "[OK]   LICENSE contains Apache-2.0" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] LICENSE does not contain Apache-2.0" -ForegroundColor Red
        $failed = $true
    }
} else {
    Write-Host "[FAIL] LICENSE file not found" -ForegroundColor Red
    $failed = $true
}

# --- Check SPDX headers in source files ---
$spdxPattern = 'SPDX-License-Identifier'
$sourceDirs = @(
    @{ Lang = 'Python';     Path = (Join-Path $repoRoot "python\evorule");     Ext = '*.py' }
    @{ Lang = 'TypeScript'; Path = (Join-Path $repoRoot "typescript\src");      Ext = '*.ts' }
    @{ Lang = 'Go';         Path = (Join-Path $repoRoot "go\evorule");          Ext = '*.go' }
    @{ Lang = 'Java';       Path = (Join-Path $repoRoot "java\src");            Ext = '*.java' }
)

$totalFiles = 0
$missingSpdx = 0

foreach ($dir in $sourceDirs) {
    if (-not (Test-Path $dir.Path)) {
        Write-Host "[SKIP] $($dir.Lang) : source dir not found" -ForegroundColor Yellow
        continue
    }
    $files = Get-ChildItem -Path $dir.Path -Recurse -Filter $dir.Ext -File -ErrorAction SilentlyContinue
    foreach ($f in $files) {
        $totalFiles++
        # Read first 5 lines for SPDX header
        $head = Get-Content $f.FullName -TotalCount 5 -Encoding UTF8 -ErrorAction SilentlyContinue
        $hasSpdx = $false
        foreach ($line in $head) {
            if ($line -match $spdxPattern) {
                $hasSpdx = $true
                break
            }
        }
        if (-not $hasSpdx) {
            Write-Host "[FAIL] $($dir.Lang) : $($f.Name) missing SPDX header" -ForegroundColor Red
            $missingSpdx++
            $failed = $true
        }
    }
}

if ($totalFiles -gt 0 -and $missingSpdx -eq 0) {
    Write-Host "[OK]   All $totalFiles source files have SPDX header" -ForegroundColor Green
}

Write-Host ""
if ($failed) {
    Write-Host "[RESULT] FAILED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "[RESULT] PASSED" -ForegroundColor Green
    exit 0
}
