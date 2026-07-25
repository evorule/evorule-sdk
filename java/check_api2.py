import urllib.request
import json

BASE = "http://localhost:18080"

def get(path):
    req = urllib.request.Request(BASE + path)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

def post(path, data=None):
    body = json.dumps(data).encode() if data else b''
    req = urllib.request.Request(BASE + path, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

# 创建会话
s = post("/api/sessions")
sid = s["session_id"]
print(f"create session: {sid}")

# state
state = get(f"/api/sessions/{sid}/state")
print(f"\nstate keys: {list(state.keys())}")
print(f"state: {json.dumps(state, indent=2, ensure_ascii=False)[:500]}")

# debug/phase
phase = get(f"/api/sessions/{sid}/debug/phase")
print(f"\ndebug/phase: {json.dumps(phase, indent=2)}")

# list sessions
sessions = get("/api/sessions")
print(f"\nlist_sessions: {json.dumps(sessions, indent=2)[:300]}")
