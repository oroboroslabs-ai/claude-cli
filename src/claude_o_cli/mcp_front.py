#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE MCP FRONT-END (the industry standard wire for OUR tools) — :3177

Exposes the entire ToolRegistry (72 tools) to ANY standard MCP client:
- tools/list → the live registry names/descriptions (+ oroboros_call)
- tools/call → dispatch through host_tool_bridge (real host execution)
- resources  → the live systemscape map + the tool map
- prompts    → the reusable REA pipeline template

JSON-RPC 2.0 over HTTP POST /mcp. Stdout is a JSON access log (run it via
the Hands registry).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST, PORT = "127.0.0.1", int(os.environ.get("MCP_PORT", "3177"))
ROLE = os.environ.get("MCP_ROLE", "primary")
SRC = r"Q:\oroboros-core\claude-o-cli\src"
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# ── THE RELAY LAW (secondary front :3178) ──────────────────────────────
# Inter-lab work ONLY: research/reading tools freely, intel/search tools
# FIRST-SEARCH-ONLY (one query per connection, enforced by counter),
# and the haki is the standing exception — always open, never counted.
RELAY_ALLOW = {
    # research / reading (unlimited on the relay)
    "linalg", "phi_library", "read_file", "list_dir", "claude_o_status",
    "nullframe_vault", "nullframe_read",
    "nullframe_brief", "ollama_models", "memory_body",
    # intel / search — FIRST SEARCH ONLY (counter-enforced)
    "q3_route", "q5_query", "q6_query", "q7_query", "worldfeed_live",
    "world_feed", "worldfeed_context", "spy_network", "tor_status",
    "tor_connect",
    # THE STANDING EXCEPTION — the haki is never counted, always open
    "haki_status",
}
_FIRST_SEARCH_ONLY = {"q3_route", "q5_query", "q6_query", "q7_query",
                      "worldfeed_live", "world_feed", "worldfeed_context", "spy_network"}
_SEARCH_COUNT = {}  # tool -> used count (first-search-only enforcement)


def _relay_gate(tool: str) -> str | None:
    """None = allow; a message = refuse. Relay role only."""
    if ROLE != "relay":
        return None
    if tool not in RELAY_ALLOW:
        return ("relay law: tool '" + tool + "' is NOT on the inter-lab relay — "
                "the full registry runs on the primary front :3177")
    if tool in _FIRST_SEARCH_ONLY:
        _SEARCH_COUNT[tool] = _SEARCH_COUNT.get(tool, 0) + 1
        if _SEARCH_COUNT[tool] > 1:
            return ("relay law (first search only): '" + tool + "' already used its "
                    "one search this session — do the research reads instead "
                    "(phi_library / nullframe_read / read_file), or take the full "
                    "front :3177")
    return None


# ── THE FEED ISOLATION LAW ─────────────────────────────────────────────
# Model-facing secondary plumbing (skills_list/skill_load — the Architect's
# skill deck) is fed DIRECTLY to the models via the chat plug and is NEVER
# exposed on any MCP front: isolated from the system-wide agentic/MCP bus.
FEED_EXCLUDE = {"skills_list", "skill_load"}

def _registry():
    from claude_o_cli.host_tool_bridge import get_shared_tools
    return get_shared_tools()


def _mcp_visible(reg) -> dict:
    """The registry as seen from the wire — model-direct plumbing removed."""
    vis = {n: t for n, t in reg.tools.items() if n not in FEED_EXCLUDE}
    if ROLE == "relay":
        vis = {n: t for n, t in vis.items() if n in RELAY_ALLOW}
        vis["oroboros_call_probe"] = type("T", (), {"description": "(relay probe: not a real tool — use tools/call with oroboros_call)"})  # hint only
    return vis


def _dispatch(tool: str, args: dict) -> dict:
    from claude_o_cli.host_tool_bridge import execute_payload
    return execute_payload({"tool": tool, "args": args or {}}, source="mcp_front")


PROC = "oroboros-mcp-front"

# the prompt template the front-end offers (MCP prompts capability)
PROMPT_REA = {
    "name": "rea_pipeline",
    "description": "Reverse-engineer a target with the null-frame REA pipeline",
    "arguments": [{"name": "target", "description": "url, dir, or .asar", "required": True}],
}
PROMPT_BODY = (
    "Run the REA pipeline on {target}: nullframe_probe (url) or nullframe_assimilate "
    "(local), then nullframe_read the teardown, nullframe_brief it, and build the "
    "rebuild with your own files. Verify every step."
)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stdout.write("[mcp-front %s] %s\n" % (self.address_string(), fmt % args))
        sys.stdout.flush()

    def _hdr(self, code: int, body: bytes, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _rpc(self, req: dict):
        method = req.get("method", "")
        rid = req.get("id")
        result = None
        error = None
        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "resources": {"subscribe": False},
                        "prompts": {"listChanged": False},
                    },
                    "serverInfo": {"name": "oroboros-mcp-front", "version": "1.0.0"},
                    "instructions": "All Oroboros host tools execute for real here.",
                }
            elif method == "notifications/initialized":
                return None
            elif method == "tools/list":
                reg = _registry()
                tools = [{"name": n, "description": t.description, "inputSchema": {"type": "object"}}
                         for n, t in _mcp_visible(reg).items()]
                tools.append({
                    "name": "oroboros_call",
                    "description": "Call ANY Oroboros host tool by name with typed args "
                                   "(the whole 70+ registry through one standard tool)",
                    "inputSchema": {"type": "object", "properties": {
                        "tool": {"type": "string"}, "args": {"type": "object"}},
                        "required": ["tool"]},
                })
                result = {"tools": tools}
            elif method == "tools/call":
                pa = req.get("params", {}).get("arguments", {})
                name = str(pa.get("name") or "")
                inner = pa.get("arguments") if name == "oroboros_call" else None
                if name == "oroboros_call":
                    inner_tool = str((inner or {}).get("tool") or "")
                    inner_args = (inner or {}).get("args") or {}
                else:
                    inner_tool, inner_args = name, pa
                gate = _relay_gate(inner_tool)
                if gate:
                    out = {"ok": False, "relay_gate": gate}
                else:
                    from claude_o_cli.host_tool_bridge import execute_payload
                    out = execute_payload({"tool": inner_tool, "args": inner_args}, source="mcp_front")
                result = {"content": [{"type": "text", "text": json.dumps(out, default=str)[:20000]}]}
            elif method == "resources/list":
                result = {"resources": [
                    {"uri": "oroboros://systemscape/map", "name": "the live systemscape map (mesh graph)"},
                    {"uri": "oroboros://tools/map", "name": "THE FULL TOOL MAP text"},
                ]}
            elif method == "resources/read":
                uri = req.get("params", {}).get("uri", "")
                if uri.endswith("/map"):
                    reg = _registry()
                    result = {"contents": [{"uri": uri, "text": "\n".join(reg.tools.keys())}]}
                    if "systemscape" in uri:
                        import urllib.request as _u
                        try:
                            with _u.urlopen("http://127.0.0.1:8800/api/map", timeout=15) as rr:
                                result["contents"][0]["text"] = rr.read().decode("utf-8", "replace")[:20000]
                        except Exception:
                            pass
                else:
                    error = {"code": -32602, "message": "unknown resource " + uri}
            elif method == "prompts/list":
                result = {"prompts": [PROMPT_REA]}
            elif method == "prompts/get":
                result = {"description": PROMPT_REA["description"],
                          "messages": [{"role": "user", "content": {"type": "text",
                                       "text": PROMPT_BODY.format(target=req.get("params", {}).get("arguments", {}).get("target", "the user's target"))}}]}
            else:
                error = {"code": -32601, "message": "method not found: " + method}
        except Exception as e:
            error = {"code": -32000, "message": str(e)}
        if result is None and error is None:
            return None  # notification
        return {"jsonrpc": "2.0", "id": rid, **({"result": result} if error is None else {"error": error})}

    def do_POST(self):
        if not self.path.startswith("/mcp"):
            self._hdr(404, json.dumps({"error": "not found"}).encode())
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            req = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            out = self._rpc(req) if isinstance(req, dict) else None
            self._hdr(200, (json.dumps(out) if out else "{}").encode())
        except Exception as e:
            self._hdr(200, json.dumps({"jsonrpc": "2.0", "id": None,
                                       "error": {"code": -32700, "message": str(e)}}).encode())

    def do_OPTIONS(self):
        self._hdr(204, b"", "text/plain")

    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path
        if p in ("/health", "/"):
            self._hdr(200, json.dumps({"ok": True, "server": "oroboros-mcp-front",
                                       "port": PORT, "std": "tools+resources+prompts"}).encode())
            return
        self._hdr(404, json.dumps({"error": "POST /mcp"}).encode())


def main():
    print("OROBOROS MCP %s on http://%s:%d/mcp%s" % (
        "RELAY (inter-lab)" if ROLE == "relay" else "FRONT-END (full registry)",
        HOST, PORT,
        "" if ROLE == "relay" else " — tools/list + tools/call + resources + prompts"))
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
