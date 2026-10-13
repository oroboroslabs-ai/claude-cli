#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collect every tool every configured MCP server exposes (name + description)."""
import io, json, os, subprocess, sys, threading, urllib.request
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
CFG = Path(os.path.expanduser("~/.claude-cli/.claude-cli.json"))
INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "collector", "version": "1"}}}
LIST = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}


def http_tools(url):
    out = []
    for msg in (INIT, {"jsonrpc": "2.0", "method": "notifications/initialized"}, LIST):
        try:
            req = urllib.request.Request(url, data=json.dumps(msg).encode(),
                                         headers={"Content-Type": "application/json",
                                                  "Accept": "application/json, text/event-stream"})
            with urllib.request.urlopen(req, timeout=15) as r:
                body = r.read().decode("utf-8", "replace")
            for line in body.splitlines():
                if line.startswith("data:"):
                    line = line[5:].strip()
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("id") == 2 and "result" in obj:
                    out = obj["result"].get("tools", [])
        except Exception:
            pass
    return out


def stdio_tools(cmd, args):
    out = []
    try:
        p = subprocess.Popen([cmd, *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
    except Exception:
        return out
    def rd():
        for line in p.stdout:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("id") == 2 and "result" in obj:
                out.extend(obj["result"].get("tools", []))
                break
    t = threading.Thread(target=rd, daemon=True); t.start()
    for msg in (INIT, {"jsonrpc": "2.0", "method": "notifications/initialized"}, LIST):
        try:
            p.stdin.write(json.dumps(msg) + "\n"); p.stdin.flush()
        except Exception:
            break
    t.join(12); 
    try: p.kill()
    except Exception: pass
    return out


def main():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    result = {}
    for name, spec in (cfg.get("mcpServers") or {}).items():
        if spec.get("type") == "http":
            tools = http_tools(spec["url"])
        else:
            tools = stdio_tools(spec["command"], spec.get("args", []))
        result[name] = [{"name": t.get("name"), "description": (t.get("description") or "")[:200]}
                        for t in tools]
        print(f"{name}: {len(result[name])} tools")
    Path(r"Q:\claude-cli\tool_inventory.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print("saved tool_inventory.json")


if __name__ == "__main__":
    main()
