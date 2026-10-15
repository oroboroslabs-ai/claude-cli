#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLAUDE-CLI — ADAPTIVE LOCAL CONNECTION
======================================
Connects the local systems (MCP bridges, Docker, Orca, DeepSeek harness,
Oroboros core, Ollama) into the Claude-CLI by writing its user-scope
`mcpServers`, so every installed tool is usable locally with no external call.

ADAPTIVE: every candidate is handshake-tested before it is written. Only the
servers that actually respond to an MCP `initialize` are added, so the CLI is
never given a dead server. Re-run any time; idempotent and additive — it never
removes a by-hand server, and it removes only its own entries that stopped
working.

Normal (cloud) connection stays available: providers fall back to HuggingFace
or Anthropic when a key is entered; Anthropic is dormant otherwise. No secrets
are written.
"""
from __future__ import annotations

import io
import json
import os
import socket
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CFG = Path(os.path.expanduser("~/.claude-cli/.claude-cli.json"))
PY312 = r"C:\Users\incoguser\AppData\Local\Programs\Python\Python312\python.exe"
ANACONDA = r"C:\ProgramData\anaconda3\python.exe"
MCP = r"C:\Users\incoguser\mcp-servers"
ORCA_EXE = r"C:\Users\incoguser\AppData\Local\Programs\Orca\resources\bin\orca.exe"
INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "claude-cli", "version": "0.1.6"}}}


def py() -> str:
    for p in (PY312, ANACONDA, sys.executable):
        if p and Path(p).exists():
            return p
    return "python"


def http_ok(url: str, timeout: float = 5.0) -> bool:
    try:
        req = urllib.request.Request(
            url, data=json.dumps(INIT).encode(),
            headers={"Content-Type": "application/json",
                     "Accept": "application/json, text/event-stream"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(4096).decode("utf-8", "replace")
        return '"result"' in body
    except Exception:
        return False


def stdio_ok(cmd: str, args: list, env: dict | None, timeout: float = 8.0) -> bool:
    e = dict(os.environ)
    if env:
        e.update({k: str(v) for k, v in env.items()})
    try:
        p = subprocess.Popen([cmd, *args], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             text=True, env=e, encoding="utf-8")
    except Exception:
        return False
    got = {"ok": False}

    def reader():
        try:
            for _ in range(50):
                line = p.stdout.readline()
                if not line:
                    break
                if '"result"' in line:
                    got["ok"] = True
                    break
        except Exception:
            pass

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    try:
        p.stdin.write(json.dumps(INIT) + "\n")
        p.stdin.flush()
    except Exception:
        pass
    t.join(timeout)
    try:
        p.kill()
    except Exception:
        pass
    return got["ok"]


def candidates() -> list:
    """(name, config, test_kind) — test_kind: 'http' or ('stdio', cmd, args, env)."""
    c = []
    # HTTP local MCP servers
    c.append(("oroboros-cordis-harness",
              {"type": "http", "url": "http://127.0.0.1:8789/mcp"}, "http"))
    # stdio bridges
    p = py()
    tools_srv = Path(r"Q:\claude-cli\oroboros_tools_mcp.py")
    if tools_srv.exists():
        c.append(("oroboros-tools",
                  {"type": "stdio", "command": p, "args": [str(tools_srv)]},
                  (p, [str(tools_srv)], None)))
    orca_bridge = Path(r"Q:\oroboros-core\claude-o-cli\mcp_stdio_bridge.py")
    if orca_bridge.exists():
        c.append(("orca-bridge",
                  {"type": "stdio", "command": ANACONDA if Path(ANACONDA).exists() else p,
                   "args": [str(orca_bridge)], "env": {"ORCA_CLI_COMMAND": ORCA_EXE}},
                  (ANACONDA if Path(ANACONDA).exists() else p, [str(orca_bridge)], {"ORCA_CLI_COMMAND": ORCA_EXE})))
    stdio_map = {
        "ollama-mcp-bridge": {"OLLAMA_HOST": "http://localhost:11434", "Q3_OLLAMA_HOST": "http://localhost:11435"},
        "oroboros-bridge": {},
        "oroboros-synthesizer": {},
        "q3-worldfeed-bridge": {
            "Q3_NODE_URL": "http://localhost:8000", "AGI_OLLAMA_URL": "http://localhost:11434",
            "Q3_OLLAMA_URL": "http://localhost:11435",
            "OROBOROS_LOGS": "J:/oroboros-programs/OROBOROS_AGI/ouroboros_logs",
            "SERVICE_MANIFEST": "J:/oroboros-services.json"},
        "z-image-turbo": {},
    }
    for name, env in stdio_map.items():
        script = Path(MCP) / name / "server.py"
        if script.exists():
            cfg = {"type": "stdio", "command": p, "args": [str(script)]}
            if env:
                cfg["env"] = env
            c.append((name, cfg, (p, [str(script)], env)))
    # Docker MCP gateway: stdio launcher (streaming HTTP if it is ever up)
    c.append(("MCP_DOCKER",
              {"type": "stdio", "command": "docker",
               "args": ["mcp", "gateway", "run", "--profile", "default"],
               "env": {"LOCALAPPDATA": os.path.expandvars(r"%LOCALAPPDATA%"),
                       "ProgramData": r"C:\ProgramData", "ProgramFiles": r"C:\Program Files"}},
              ("docker", ["mcp", "gateway", "run", "--profile", "default"],
               {"LOCALAPPDATA": os.path.expandvars(r"%LOCALAPPDATA%"),
                "ProgramData": r"C:\ProgramData", "ProgramFiles": r"C:\Program Files"})))
    return c


def main() -> int:
    if not CFG.exists():
        print(f"config not found: {CFG}")
        return 2
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    existing = cfg.get("mcpServers", {}) or {}

    print("handshake-testing local MCP candidates...")
    live, dead = {}, {}
    for name, spec, test in candidates():
        ok = http_ok(spec["url"]) if test == "http" else stdio_ok(*test)
        (live if ok else dead)[name] = spec
        print(f"  {'OK  ' if ok else 'skip'} {name}")

    # Remove only entries WE manage that stopped responding; never touch a
    # server configured by hand. (This dict is the set of names we own.)
    managed = {"oroboros-cordis-harness", "orca-bridge", "ollama-mcp-bridge",
               "oroboros-bridge", "oroboros-synthesizer", "z-image-turbo",
               "q3-worldfeed-bridge", "MCP_DOCKER", "deepseek-harness",
               "oroboros-tools"}
    for name in list(existing.keys()):
        if name in managed and name not in live:
            del existing[name]

    for name, spec in live.items():
        existing[name] = spec
    cfg["mcpServers"] = existing
    cfg["enableAllProjectMcpServers"] = True

    CFG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nlive servers written: {len(live)}  ({', '.join(live) if live else 'none'})")
    print(f"skipped (not responding): {', '.join(dead) if dead else 'none'}")
    print(f"total mcpServers in config: {len(existing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
