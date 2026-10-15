#!/usr/bin/env python3
"""Quick test of agent and engineering APIs."""
import urllib.request, json, sys

BASE = "http://127.0.0.1:5000"

def test(endpoint, payload, timeout=60):
    try:
        req = urllib.request.Request(
            f"{BASE}{endpoint}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}
        )
        r = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

# Test 1: Agent API with simple task
print("=== Agent API ===")
r = test("/api/agent", {"task": "Say hello back", "model": "starcoder2:7b"}, timeout=120)
print(f"task_id: {r.get('task_id', 'N/A')}")
result = r.get("result", {})
print(f"status: {result.get('status', 'N/A')}")
print(f"answer: {str(result.get('answer', 'N/A'))[:200]}")
print(f"iterations: {result.get('iterations', 'N/A')}")
print()

# Test 2: Engineering API with simple task
print("=== Engineering API ===")
r2 = test("/api/engineer", {"task": "Write a hello world script", "model": "starcoder2:7b"}, timeout=120)
print(f"task_id: {r2.get('task_id', 'N/A')}")
result2 = r2.get("result", {})
print(f"status: {result2.get('status', 'N/A')}")
log = result2.get("log", [])
for entry in log[:5]:
    print(f"  [{entry.get('phase','?')}] {entry.get('status','?')}")
