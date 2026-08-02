# =============================================================================
# validate-version.ps1 - EvoRule SDK multi-language version consistency check
# Checks: Python (pyproject.toml) / TypeScript (package.json) / Java (build.gradle.kts)
# =============================================================================
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

$failed = $false

# --- Read version from each language ---
function Get-PythonVersion {
    param([string]$path)
    $content = Get-Content $path -Raw -Encoding UTF8
    if ($content -match 'version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"') {
        return $Matches[1]
    }
    return $null
}

function Get-TypeScriptVersion {
    param([string]$path)
    $content = Get-Content $path -Raw -Encoding UTF8
    if ($content -match '"version"\s*:\s*"([0-9]+\.[0-9]+\.[0-9]+)"') {
        return $Matches[1]
    }
    return $null
}

function Get-JavaVersion {
    param([string]$path)
    $content = Get-Content $path -Raw -Encoding UTF8
    if ($content -match 'version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"') {
        return $Matches[1]
    }
    return $null
}

Write-Host "=== Version Validation (Multi-Language) ===" -ForegroundColor Cyan

$projects = [ordered]@{
    'python'     = @{ File = (Join-Path $repoRoot "python\pyproject.toml");       Func = 'Get-PythonVersion' }
    'typescript' = @{ File = (Join-Path $repoRoot "typescript\package.json");     Func = 'Get-TypeScriptVersion' }
    'java'       = @{ File = (Join-Path $repoRoot "java\build.gradle.kts");       Func = 'Get-JavaVersion' }
}

$versions = @{}
foreach ($name in $projects.Keys) {
    $info = $projects[$name]
    if (-not (Test-Path $info.File)) {
        Write-Host "[FAIL] $name : $($info.File) not found" -ForegroundColor Red
        $failed = $true
        continue
    }
    $ver = & $info.Func -path $info.File
    if ($null -eq $ver) {
        Write-Host "[FAIL] $name : version not found in $($info.File)" -ForegroundColor Red
        $failed = $true
        continue
    }
    $versions[$name] = $ver
    Write-Host "[OK]   $name : $ver" -ForegroundColor Green
}

# --- Check consistency ---
if ($versions.Count -ge 2) {
    $firstKey = ($versions.Keys | Select-Object -First 1)
    $firstVersion = $versions[$firstKey]
    $allMatch = $true
    foreach ($name in $versions.Keys) {
        if ($versions[$name] -ne $firstVersion) {
            Write-Host "[FAIL] $name ($($versions[$name])) != reference ($firstVersion)" -ForegroundColor Red
            $failed = $true
            $allMatch = $false
        }
    }
    if ($allMatch) {
        Write-Host "[OK]   All SDK versions match: $firstVersion" -ForegroundColor Green
    }
}

# --- MAJOR consistency ---
$majors = $versions.Values | ForEach-Object { ($_ -split '\.')[0] } | Sort-Object -Unique
if ($majors.Count -eq 1) {
    Write-Host "[OK]   All SDKs share MAJOR = $($majors[0])" -ForegroundColor Green
} elseif ($majors.Count -gt 1) {
    Write-Host "[WARN] SDKs have different MAJOR versions: $($majors -join ', ')" -ForegroundColor Yellow
}

# --- L1 Document version literal scan ---
Write-Host ""
Write-Host "=== L1 Document Version Scan ===" -ForegroundColor Cyan
$firstKey = ($versions.Keys | Select-Object -First 1)
$canonicalVersion = $versions[$firstKey]
if ($canonicalVersion) {
    $canonicalTag = "v$canonicalVersion"
    $l1Docs = @()
    $l1Docs += Get-ChildItem -Path $repoRoot -Filter "*.md" -File -ErrorAction SilentlyContinue
    $l1Docs += Get-ChildItem -Path (Join-Path $repoRoot "docs") -Filter "*.md" -File -ErrorAction SilentlyContinue
    foreach ($lang in @("python", "typescript", "go", "java")) {
        $langDir = Join-Path $repoRoot $lang
        if (Test-Path $langDir) {
            $l1Docs += Get-ChildItem -Path $langDir -Filter "*.md" -File -ErrorAction SilentlyContinue
        }
    }

    $staleFound = $false
    $versionPattern = [regex]'v[0-9]+\.[0-9]+\.[0-9]+'
    $whitelist = @('CHANGELOG', 'vX', 'v0.1.0', 'v1.0', 'v0.2', 'v0.3')
    foreach ($doc in $l1Docs) {
        $lines = Get-Content $doc.FullName -Encoding UTF8 -ErrorAction SilentlyContinue
        for ($i = 0; $i -lt $lines.Count; $i++) {
            $line = $lines[$i]
            $matches = $versionPattern.Matches($line)
            foreach ($m in $matches) {
                $lit = $m.Value
                if ($lit -eq $canonicalTag) { continue }
                $isWhitelisted = $false
                foreach ($w in $whitelist) {
                    if ($lit -like "$w*" -or $line -match 'CHANGELOG|废弃|audit|历史') {
                        $isWhitelisted = $true
                        break
                    }
                }
                if (-not $isWhitelisted -and $lit -match '^v[0-9]') {
                    Write-Host "[WARN] $($doc.Name):$($i+1) stale version literal: $lit" -ForegroundColor Yellow
                    $staleFound = $true
                }
            }
        }
    }
    if (-not $staleFound) {
        Write-Host "[OK]   L1 docs contain no stale version literals" -ForegroundColor Green
    }
}

Write-Host ""
if ($failed) {
    Write-Host "[RESULT] FAILED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "[RESULT] PASSED" -ForegroundColor Green
    exit 0
}
