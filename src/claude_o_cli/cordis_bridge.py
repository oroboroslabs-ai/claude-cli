#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CORDIS BRIDGE — the total-core harness's full plugin toolset (:8789),
reachable from the registry and both MCP fronts.

cordis_list { }     → the harness's live tools (the cordis MCP tools/list)
cordis_call {name, arguments} → dispatch into the harness (real execution)
"""
from __future__ import annotations

import json
import urllib.request

CORDIS = "http://127.0.0.1:8789/mcp"


def _rpc(method: str, params: dict, rid: int = 1, timeout: int = 240) -> dict:
    req = urllib.request.Request(CORDIS,
        data=json.dumps({"jsonrpc": "2.0", "id": rid, "method": method, "params": params}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def tool_cordis_list(args: dict) -> dict:
    try:
        out = _rpc("tools/list", {})
        return {"ok": True, "tool": "cordis_list", "cordis": CORDIS,
                "count": len(out.get("result", {}).get("tools") or []),
                "tools": [t.get("name") for t in (out.get("result", {}).get("tools") or [])]}
    except Exception as e:
        return {"ok": False, "tool": "cordis_list", "error": str(e)}


def tool_cordis_call(args: dict) -> dict:
    name = str(args.get("name") or "").strip()
    if not name:
        return {"ok": False, "tool": "cordis_call", "error": "name required"}
    try:
        out = _rpc("tools/call", {"name": name, "arguments": args.get("arguments") or {}})
        result = out.get("result") or {}
        content = result.get("content") or []
        text = "\n".join((c.get("text") or "") for c in content if isinstance(c, dict))[:12000]
        return {"ok": not result.get("isError", False), "tool": name,
                "backend": "cordis harness :8789", "text": text}
    except Exception as e:
        return {"ok": False, "tool": "cordis_call", "error": str(e)}


def register_cordis_tools(registry) -> list:
    from claude_o_cli.oroboros_core import Tool
    tools = [
        ("cordis_list", "The total-core cordis harness's live plugin tools (tools/list over MCP)", tool_cordis_list, False),
        ("cordis_call", 'Dispatch one cordis harness plugin tool. args: name, arguments', tool_cordis_call, False),
    ]
    names = []
    for name, desc, handler, perm in tools:
        if name not in registry.tools:
            registry.register(Tool(name, desc, handler, perm))
        names.append(name)
    return names