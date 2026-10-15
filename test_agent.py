#!/usr/bin/env python3
"""Test the agent tool execution loop."""
import urllib.request, json

payload = {
    "model": "starcoder2:7b",
    "message": "list the available models using the ollama_models tool",
    "system": "You are an AI with tool access. When you need to use a tool, respond with: {\"tool\": \"tool_name\", \"args\": {...}}",
    "history": []
}

req = urllib.request.Request(
    "http://127.0.0.1:5000/api/chat",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"}
)

try:
    r = urllib.request.urlopen(req, timeout=120)
    d = json.loads(r.read())
    print("Response:", d.get("response", "")[:500])
except Exception as e:
    print(f"Error: {e}")
