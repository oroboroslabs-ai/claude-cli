#!/usr/bin/env python3
"""Test the rebuilt claude-fable-5:210cubed model."""
import urllib.request, json

BASE = "http://127.0.0.1:5000"

# Test 1: Basic chat
print("=== Test 1: Basic Chat ===")
payload = {
    "model": "claude-fable-5:210cubed",
    "message": "Say hello and tell me what model you are based on.",
    "system": "You are a helpful AI. Respond directly.",
    "history": []
}
req = urllib.request.Request(f"{BASE}/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
r = urllib.request.urlopen(req, timeout=120)
d = json.loads(r.read())
print("Response:", d.get("response", "")[:300])
print()

# Test 2: Tool call
print("=== Test 2: Tool Call ===")
payload2 = {
    "model": "claude-fable-5:210cubed",
    "message": "Use the ollama_models tool to tell me how many models are available.",
    "system": "You are an AI with tool access. When you need to use a tool, respond with EXACTLY: {\"tool\": \"tool_name\", \"args\": {\"key\": \"value\"}}",
    "history": []
}
req2 = urllib.request.Request(f"{BASE}/api/chat", data=json.dumps(payload2).encode(), headers={"Content-Type": "application/json"})
r2 = urllib.request.urlopen(req2, timeout=180)
d2 = json.loads(r2.read())
print("Response:", d2.get("response", "")[:500])
print()

# Test 3: Agent loop
print("=== Test 3: Agent Loop ===")
payload3 = {
    "task": "Use the ollama_models tool to count how many models are available, then tell me the answer.",
    "model": "claude-fable-5:210cubed"
}
req3 = urllib.request.Request(f"{BASE}/api/agent", data=json.dumps(payload3).encode(), headers={"Content-Type": "application/json"})
r3 = urllib.request.urlopen(req3, timeout=300)
d3 = json.loads(r3.read())
result = d3.get("result", {})
print("Status:", result.get("status", "unknown"))
print("Iterations:", result.get("iterations", "N/A"))
print("Answer:", str(result.get("answer", "N/A"))[:300])
