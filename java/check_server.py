import urllib.request
import urllib.error
import os
import sys

BASE_URL = os.environ.get("EVORULE_BASE_URL", "http://localhost:18080")

try:
    req = urllib.request.Request(BASE_URL + "/api/health")
    resp = urllib.request.urlopen(req, timeout=3)
    print(f"Server running: {resp.status}")
    print(f"Body: {resp.read().decode('utf-8')[:200]}")
except Exception as e:
    print(f"Server not running: {e}")
    sys.exit(1)
