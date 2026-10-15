#!/usr/bin/env python3
"""Debug test for agent loop - show raw response."""
import urllib.request, json

payload = {
    "task": "Say hello and list 3 models using ollama_models tool",
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
    print("RAW RESPONSE:")
    print(json.dumps(d, indent=2)[:2000])
except Exception as e:
    print(f"Error: {e}")
