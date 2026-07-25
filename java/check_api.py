import urllib.request
import urllib.error
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

def put(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(BASE + path, data=body, method="PUT")
    req.add_header("Content-Type", "application/json")
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

def patch(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(BASE + path, data=body, method="PATCH")
    req.add_header("Content-Type", "application/json")
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

# 1. 创建会话
s = post("/api/sessions")
print("create:", json.dumps(s, indent=2, ensure_ascii=False))
sid = s["session_id"]

# 2. 会话状态
state = get(f"/api/sessions/{sid}/state")
print("\nstate keys:", list(state.keys()))

# 3. 会话列表
sessions = get("/api/sessions")
print("\nsessions:", json.dumps(sessions, indent=2, ensure_ascii=False)[:300])

# 4. 测试 update_payload 方法
try:
    r = put(f"/api/sessions/{sid}/payload", {"path": "test", "value": 1})
    print("\nPUT payload:", r)
except urllib.error.HTTPError as e:
    print(f"\nPUT payload: {e.code} {e.reason}")
    try:
        r = patch(f"/api/sessions/{sid}/payload", {"path": "test", "value": 1})
        print("PATCH payload:", r)
    except urllib.error.HTTPError as e2:
        print(f"PATCH payload: {e2.code} {e2.reason}")

# 5. 测试 shared facts
try:
    r = get("/api/shared/facts")
    print("\nGET /api/shared/facts:", json.dumps(r, indent=2)[:200])
except urllib.error.HTTPError as e:
    print(f"\nGET /api/shared/facts: {e.code} {e.reason}")

# 6. 测试 fork
try:
    r = post(f"/api/sessions/from/{sid}")
    print("\nfork:", json.dumps(r, indent=2, ensure_ascii=False)[:300])
except urllib.error.HTTPError as e:
    print(f"\nfork: {e.code} {e.reason}")
    try:
        body = e.read().decode()
        print(f"  body: {body[:200]}")
    except:
        pass
