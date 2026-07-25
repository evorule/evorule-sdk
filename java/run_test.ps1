$cp = "build\classes;" +
      "build\test-classes;" +
      "build\tmp-lib\jackson-core-2.15.2.jar;" +
      "build\tmp-lib\jackson-databind-2.15.2.jar;" +
      "build\tmp-lib\jackson-annotations-2.15.2.jar;" +
      "build\test-lib\junit-platform-console-standalone-1.10.0.jar"

& java -cp $cp org.junit.platform.console.ConsoleLauncher --select-class com.evorule.EvoruleE2ETest --details=tree 2>&1
Write-Host "EXIT=$LASTEXITCODE"
