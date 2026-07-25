import urllib.request
import os

jars = {
    "junit-platform-console-standalone-1.10.0.jar":
        "https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.10.0/junit-platform-console-standalone-1.10.0.jar",
}

os.makedirs("build/test-lib", exist_ok=True)

for name, url in jars.items():
    path = os.path.join("build/test-lib", name)
    if os.path.exists(path):
        print(f"  {name} already exists")
        continue
    print(f"Downloading {name}...")
    try:
        urllib.request.urlretrieve(url, path)
        print(f"  Done ({os.path.getsize(path)} bytes)")
    except Exception as e:
        print(f"  Failed: {e}")

print("Done")
