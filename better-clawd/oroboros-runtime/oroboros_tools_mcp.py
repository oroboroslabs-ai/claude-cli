#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OROBOROS TOOLS — MCP server (local systems for the Architect's use)
===================================================================
A stdio MCP server that exposes the Architect's local toolset to the CLI:

  Architect   — The Architect's Haki (unified perception) via :8787
  WorldFeed   — web search / feeds / datetime via :8100
  Q-Services  — Q3 edge :8000, Q7 surveillance :8952
  Tor         — SOCKS proxy :9050 (status, and a route helper)
  Loops       — living-loop status
  Systems     — live port map of every local service
  MCP         — advertises the local MCP servers wired into the CLI

Everything is http://127.0.0.1 — local only, no telemetry, no external calls.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import urllib.request
from pathlib import Path

CLI_CFG = Path.home() / ".claude-cli" / ".claude-cli.json"

KNOWN_PORTS = {
    5000: "claude-cli glass UI",
    8000: "Q3 edge detection",
    8100: "WorldFeed",
    8101: "Q5 pattern analysis",
    8787: "Architect's Haki",
    8789: "oroboros-anthropic-core-harness",
    8952: "Q7 quantum surveillance",
    9050: "Tor SOCKS proxy",
    11434: "Ollama",
}


def _http(url: str, timeout: float = 8.0) -> str:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            data = r.read(20000)
        try:
            return json.dumps(json.loads(data.decode("utf-8", "replace")), indent=2)[:4000]
        except Exception:
            return data.decode("utf-8", "replace")[:4000]
    except Exception as e:  # noqa: BLE001
        return f"unreachable: {e}"


def _port(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def t_worldfeed_search(q: str) -> str:
    import urllib.parse
    return _http("http://127.0.0.1:8100/search?q=" + urllib.parse.quote(q))


def t_worldfeed_feeds() -> str:
    return _http("http://127.0.0.1:8100/feeds")


def t_worldfeed_datetime() -> str:
    return _http("http://127.0.0.1:8100/datetime")


def t_q3_status() -> str:
    return _http("http://127.0.0.1:8000/status")


def t_q7_status() -> str:
    return _http("http://127.0.0.1:8952/status")


def t_architects_haki() -> str:
    return _http("http://127.0.0.1:8787/api/architects-haki")


def t_tor_status() -> str:
    if _port(9050):
        return (f"Tor SOCKS proxy is UP at 127.0.0.1:9050. "
                f"Set all_proxy=socks5://127.0.0.1:9050 to route through it.")
    return "Tor SOCKS proxy is DOWN at 127.0.0.1:9050 (start Tor / Q-Services)."


def t_live_systems() -> str:
    rows = []
    for port, name in sorted(KNOWN_PORTS.items()):
        rows.append(f"  {'UP  ' if _port(port) else 'down'} :{port}  {name}")
    return "LOCAL SYSTEMS\n" + "\n".join(rows)


def t_mcp_servers() -> str:
    try:
        cfg = json.loads(CLI_CFG.read_text(encoding="utf-8"))
        servers = cfg.get("mcpServers") or {}
        return "MCP SERVERS WIRED\n" + "\n".join(f"  {k}" for k in servers) if servers \
            else "no MCP servers configured"
    except Exception as e:  # noqa: BLE001
        return f"could not read MCP config: {e}"


def t_living_loop() -> str:
    return _http("http://127.0.0.1:5000/api/living-loop")


def t_orca_status() -> str:
    import shutil
    import subprocess
    orca = os.environ.get("ORCA_CLI_COMMAND") or shutil.which("orca") \
        or r"C:\Users\incoguser\AppData\Local\Programs\Orca\resources\bin\orca.exe"
    try:
        r = subprocess.run([orca, "status", "--json"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=20)
        return (r.stdout or r.stderr or "(no output)")[:3000]
    except Exception as e:  # noqa: BLE001
        return f"orca status unavailable: {e}"


TOOLS = [
    ("architects_haki", "The Architect's Haki — unified perception system status and lattice connection (Crown 1272 Hz).",
     {"type": "object", "properties": {}}),
    ("worldfeed_search", "Search WorldFeed (live web/global feed) via the local WorldFeed server.",
     {"type": "object", "properties": {"q": {"type": "string", "description": "search query"}}, "required": ["q"]}),
    ("worldfeed_feeds", "List the WorldFeed feeds currently available.",
     {"type": "object", "properties": {}}),
    ("worldfeed_datetime", "Get authoritative date/time from WorldFeed.",
     {"type": "object", "properties": {}}),
    ("q3_status", "Q3 edge-detection / environmental-scan status.",
     {"type": "object", "properties": {}}),
    ("q7_status", "Q7 quantum-surveillance (quantum conduit) status.",
     {"type": "object", "properties": {}}),
    ("tor_status", "Status of the local Tor SOCKS proxy and routing hint.",
     {"type": "object", "properties": {}}),
    ("live_systems", "Live port map of every local Oroboros service (what is up/down right now).",
     {"type": "object", "properties": {}}),
    ("mcp_servers", "List the local MCP servers wired into the CLI.",
     {"type": "object", "properties": {}}),
    ("living_loop", "Status of the claude-cli living loop (:5000/api/living-loop).",
     {"type": "object", "properties": {}}),
    ("orca_status", "Run `orca status --json` and return Orca's runtime status.",
     {"type": "object", "properties": {}}),
]

CALL = {
    "architects_haki": lambda a: t_architects_haki(),
    "worldfeed_search": lambda a: t_worldfeed_search(a.get("q", "")),
    "worldfeed_feeds": lambda a: t_worldfeed_feeds(),
    "worldfeed_datetime": lambda a: t_worldfeed_datetime(),
    "q3_status": lambda a: t_q3_status(),
    "q7_status": lambda a: t_q7_status(),
    "tor_status": lambda a: t_tor_status(),
    "live_systems": lambda a: t_live_systems(),
    "mcp_servers": lambda a: t_mcp_servers(),
    "living_loop": lambda a: t_living_loop(),
    "orca_status": lambda a: t_orca_status(),
}

BANNER = (
    "OROBOROS TOOLS (Architect · local): architects_haki, worldfeed_search, "
    "worldfeed_feeds, worldfeed_datetime, q3_status, q7_status, tor_status, "
    "live_systems, mcp_servers, living_loop, orca_status — all run on 127.0.0.1."
)


def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        method = msg.get("method")
        mid = msg.get("id")
        if method == "initialize":
            send({"jsonrpc": "2.0", "id": mid, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "oroboros-tools", "version": "1.0.0"},
                "instructions": BANNER,
            }})
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            send({"jsonrpc": "2.0", "id": mid, "result": {"tools": [
                {"name": n, "description": d, "inputSchema": s} for n, d, s in TOOLS
            ]}})
        elif method == "tools/call":
            params = msg.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {}) or {}
            fn = CALL.get(name)
            text = fn(args) if fn else f"unknown tool: {name}"
            send({"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": text}], "isError": False}})
        elif method == "ping":
            send({"jsonrpc": "2.0", "id": mid, "result": {}})
        elif mid is not None:
            send({"jsonrpc": "2.0", "id": mid, "result": {}})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
