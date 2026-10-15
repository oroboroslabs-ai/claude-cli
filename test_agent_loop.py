#!/usr/bin/env python3
"""Test the recursive agent loop."""
import urllib.request, json

# Test 1: Basic agent loop
print("=== TEST 1: Agent Loop ===")
payload = {
    "task": "List the available Ollama models using the ollama_models tool and tell me how many there are.",
    "model": "starcoder2:7b"
}
req = urllib.request.Request(
    "http://127.0.0.1:5000/api/agent",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"}
)
try:
    r = urllib.request.urlopen(req, timeout=300)
    d = json.loads(r.read())
    result = d.get("result", {})
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Iterations: {result.get('iterations', 'N/A')}")
    print(f"Answer: {str(result.get('answer', 'N/A'))[:300]}")
    log = result.get("log", [])
    for entry in log:
        print(f"  [{entry.get('type','?')}] iter {entry.get('iteration','?')}: {str(entry.get('content','') or entry.get('result',''))[:100]}")
except Exception as e:
    print(f"Error: {e}")

print()
print("=== TEST 2: Engineering Loop ===")
payload2 = {
    "task": "Write a Python script that prints 'Hello from Oroboros' and saves it as hello_oroboros.py",
    "model": "starcoder2:7b"
}
req2 = urllib.request.Request(
    "http://127.0.0.1:5000/api/engineer",
    data=json.dumps(payload2).encode(),
    headers={"Content-Type": "application/json"}
)
try:
    r2 = urllib.request.urlopen(req2, timeout=300)
    d2 = json.loads(r2.read())
    result2 = d2.get("result", {})
    print(f"Status: {result2.get('status', 'unknown')}")
    log2 = result2.get("log", [])
    for entry in log2:
        print(f"  [{entry.get('phase','?')}] {entry.get('status','?')}: {str(entry.get('result','') or entry.get('error',''))[:100]}")
except Exception as e:
    print(f"Error: {e}")
