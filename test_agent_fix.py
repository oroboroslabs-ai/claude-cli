#!/usr/bin/env python3
"""Test the new agent execution endpoints."""
import urllib.request, json

BASE = "http://127.0.0.1:5000"

# Test 1: Direct tool execution
print("=== Test 1: Direct Tool ===")
req = urllib.request.Request(
    f"{BASE}/api/tool",
    data=json.dumps({"tool": "ollama_models", "args": {}}).encode(),
    headers={"Content-Type": "application/json"}
)
r = urllib.request.urlopen(req, timeout=5)
d = json.loads(r.read())
models = d.get("result", "").split("\n")
print(f"Models: {len(models)}")

# Test 2: Agent executor
print()
print("=== Test 2: Agent Executor ===")
req2 = urllib.request.Request(
    f"{BASE}/api/agent/execute",
    data=json.dumps({"task": "List the available models", "model": "glm-5:cloud"}).encode(),
    headers={"Content-Type": "application/json"}
)
r2 = urllib.request.urlopen(req2, timeout=120)
d2 = json.loads(r2.read())
print(f"Tool count: {d2.get('tool_count', 0)}")
for res in d2.get("results", []):
    print(f"  Tool: {res['tool']} -> {str(res['result'][:80])}")
