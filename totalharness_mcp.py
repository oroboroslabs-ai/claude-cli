#!/usr/bin/env python3
"""TOTALHARNESS MCP — the AI door into the unlocked control plane (:8800).
stdio MCP server: total_map / total_svc / total_exec / total_file / total_health."""
import io
import json
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
CORE = "http://127.0.0.1:8800"
TOKEN = "1272"

TOOLS = [
    {"name": "total_map", "description": "The AI's fast map of the whole system: every service, port, live status, launch path, and the network edges. THE speeds layer - always consult this before touching a service.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "total_svc", "description": "Control a system service (the orbs of the scape): start|stop|status by port. Args {port: number, action: 'start'|'stop'|'status'}",
     "inputSchema": {"type": "object", "properties": {"port": {"type": "number"}, "action": {"type": "string", "enum": ["start", "stop", "status"]}}, "required": ["port", "action"]}},
    {"name": "total_exec", "description": "UNLOCKED host execution (the Architect's law - no gate): run code on the host. Args {shell: 'powershell'|'cmd'|'python'|'node', code: string, timeout?: number}",
     "inputSchema": {"type": "object", "properties": {"shell": {"type": "string"}, "code": {"type": "string"}, "timeout": {"type": "number"}}, "required": ["shell", "code"]}},
    {"name": "total_file", "description": "File operations: read|write|append|list. Args {op, path, content?}",
     "inputSchema": {"type": "object", "properties": {"op": {"type": "string", "enum": ["read", "write", "append", "list"]}, "path": {"type": "string"}, "content": {"type": "string"}}, "required": ["op", "path"]}},
]


def call(path, body=None, method=None):
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(CORE + path, data=data if body is not None else None,
                                 headers={"Content-Type": "application/json", "X-Total": TOKEN},
                                 method=method or ("POST" if body is not None else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        body_text = ""
        if hasattr(e, "read"):
            try:
                body_text = e.read().decode("utf-8", "replace")[:300]
            except Exception:
                pass
        return {"error": str(e) + " " + body_text}


def tool(name, args):
    if name == "total_map":
        return call("/api/map")
    if name == "total_svc":
        return call("/api/svc", args)
    if name == "total_exec":
        return call("/api/exec", args)
    if name == "total_file":
        return call("/api/file", args)
    if name == "total_health":
        return call("/health")
    return {"error": "unknown tool " + str(name)}


buf = ""
for line in sys.stdin:
    buf = line.strip()
    if not buf:
        continue
    try:
        msg = json.loads(buf)
    except Exception:
        continue
    rid = msg.get("id")
    m = msg.get("method", "")
    if m == "initialize":
        out = {"jsonrpc": "2.0", "id": rid, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "totalharness", "version": "0.1.6b"}}}
    elif m == "tools/list":
        out = {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    elif m == "tools/call":
        res = tool(msg["params"]["name"], msg["params"].get("arguments") or {})
        out = {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": json.dumps(res, default=str)[:30000]}]}}
    elif m == "notifications/initialized":
        continue
    else:
        out = {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "method not found"}}
    print(json.dumps(out), flush=True)