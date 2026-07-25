$cp = "build\tmp-lib\jackson-core-2.15.2.jar;" +
      "build\tmp-lib\jackson-databind-2.15.2.jar;" +
      "build\tmp-lib\jackson-annotations-2.15.2.jar;" +
      "build\test-lib\junit-platform-console-standalone-1.10.0.jar"

$mainSources = Get-ChildItem -Path "src\main\java" -Recurse -Filter "*.java" | ForEach-Object { $_.FullName }
$testSources = Get-ChildItem -Path "src\test\java" -Recurse -Filter "*.java" | ForEach-Object { $_.FullName }

New-Item -ItemType Directory -Force -Path build\classes | Out-Null
New-Item -ItemType Directory -Force -Path build\test-classes | Out-Null

Write-Host "Compiling main sources..."
& javac -cp $cp -d build\classes --release 17 $mainSources 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Main compilation failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}
Write-Host "Main sources compiled successfully"

Write-Host "Compiling test sources..."
$testCp = "build\classes;" + $cp
& javac -cp $testCp -d build\test-classes --release 17 $testSources 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Test compilation failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}
Write-Host "Test sources compiled successfully"
