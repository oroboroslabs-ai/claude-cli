#!/usr/bin/env python3
"""
TOTALHARNESS CORE — unlocked local control plane for the Oroboros / Anthropic system.
The AI of the system and the SCAPE interface both command through this one door.
UNLOCKED = the Architect's law: full-permission local operation, no approval prompts;
127.0.0.1 bind only; nothing leaves the machine.

Endpoints (all JSON):
  GET  /health                      core identity + the service registry state
  GET  /api/map                     FULL systemscape (nodes + live status) — the AI's fast map
  POST /api/svc  {action, port}     start|stop|status one service (registry launch commands)
  POST /api/exec {shell, code}      run code: powershell | cmd | python | node  (full output)
  POST /api/file {op, path, ...}    read | write | append | list
"""
from __future__ import annotations

import io
import json
import os
import socket
import subprocess
import sys
import threading
import time
from flask import Flask, jsonify, request
from flask_cors import CORS

if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CROWN = "1272"
HOST, PORT = "127.0.0.1", 8800
TOKEN = "1272"

# THE REGISTRY — port -> launch command (the real way each service boots)
REGISTRY = {
    5000: {"name": "GLASS UI / local_api", "cmd": [r"C:\Python314\python.exe", "-X", "utf8", r"Q:\oroboros-core\claude-o-cli\local_api.py"], "cwd": r"Q:\oroboros-core\claude-o-cli", "kind": "core"},
    11499: {"name": "PROVIDER SHIM (our API)", "cmd": [r"C:\ProgramData\anaconda3\python.exe", r"Q:\claude-cli\local_providers_shim.py"], "cwd": r"Q:\claude-cli", "kind": "core"},
    11434: {"name": "OLLAMA runtime", "cmd": ["cmd", "/c", "start", "/min", "ollama", "serve"], "cwd": "Q:\\", "kind": "model"},
    11435: {"name": "OLLAMA-GATE", "cmd": [r"C:\Python314\python.exe", r"J:\oroboros-programs\gate\gate.py"], "cwd": r"J:\oroboros-programs\gate", "kind": "gate"},
    8000: {"name": "Q3 EDGE DETECTION", "cmd": [r"C:\Python314\python.exe", r"J:\oroboros-programs\Q3\q3_edge_server.py"], "cwd": r"J:\oroboros-programs\Q3", "kind": "q"},
    8102: {"name": "Q5 HIVE (8102)", "env": {"Q5_HIVE_PORT": "8102"}, "cmd": [r"C:\Python314\python.exe", r"J:\oroboros-programs\Q5-Enhanced\q5_hive_api.py"], "cwd": r"J:\oroboros-programs\Q5-Enhanced", "kind": "q"},
    8952: {"name": "Q7 CONDUIT", "cmd": [r"C:/Python314/python.exe", r"J:/anthropic-local-chat/quantum-conduit/server.py"], "cwd": r"J:/anthropic-local-chat/quantum-conduit", "kind": "q"},
    8100: {"name": "WORLDFEED", "cmd": [r"C:\Python314\python.exe", r"J:\oroboros-programs\worldfeed\worldfeed_server.py"], "cwd": r"J:\oroboros-programs\worldfeed", "kind": "feed"},
    9050: {"name": "TOR SOCKS", "cmd": ["cmd", "/c", r"Q:\Tor\Tor\tor.exe"], "cwd": r"Q:\Tor", "kind": "feed"},
    3010: {"name": "GLASSWING ROUTER", "cmd": [r"C:\Python314\python.exe", r"Q:\oroboros-programs\glasswing-scouter\mcp_server_3010.py"], "cwd": r"Q:\oroboros-programs\glasswing-scouter", "kind": "feed"},
    8090: {"name": "NULL FRAME NODE", "cmd": ["node", r"J:\Assimilation Architecture Null Frame\nullframe\nullframe.mjs", "node", "8090"], "cwd": r"J:\Assimilation Architecture Null Frame\nullframe", "kind": "prog"},
    8789: {"name": "CORDIS HARNESS", "cmd": ["node", r"C:\Users\incoguser\.cordis\server.js"], "cwd": r"C:\Users\incoguser\.cordis", "kind": "harness"},
    8920: {"name": "VIDEO WORKER", "cmd": [r"C:\Python314\python.exe", r"J:\oroboros_video_diffusion_pipeline\app.py"], "cwd": r"J:\oroboros_video_diffusion_pipeline", "kind": "video"},
    8940: {"name": "ORCHESTRATOR", "cmd": [r"C:\Python314\python.exe", r"Q:\browser-agent-orchestrator\server.py"], "cwd": r"Q:\browser-agent-orchestrator", "kind": "video"},
}

app = Flask(__name__)
CORS(app)

PROCS: dict[int, subprocess.Popen] = {}
LOCK = threading.Lock()


def _alive(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.35):
            return True
    except OSError:
        return False


def _pid_on_port(port: int):
    try:
        out = subprocess.run(["cmd", "/c", f"netstat -ano | findstr :{port} "], capture_output=True, text=True, timeout=10).stdout
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[1].endswith(str(port)) and parts[3] == "LISTENING":
                return int(parts[4])
    except Exception:
        return None
    return None


@app.get("/health")
def health():
    with LOCK:
        state = {p: {"name": r["name"], "kind": r["kind"], "up": _alive(p)} for p, r in REGISTRY.items()}
    return jsonify({"service": "TOTALHARNESS CORE", "unlocked": True, "token": TOKEN, "crown": CROWN, "services": state})


@app.get("/api/map")
def the_map():
    """The AI's fast map: every node + live status + the access path."""
    with LOCK:
        nodes, edges = [], []
        state = {}
        for port, r in REGISTRY.items():
            up = _alive(port)
            state[port] = up
            nodes.append({"port": port, "name": r["name"], "kind": r["kind"], "up": up,
                          "launch": r["cmd"], "cwd": r["cwd"]})
        edges = [
            [5000, 11499], [11499, 11434], [11435, 11434], [8000, 8102], [8000, 8100], [8000, 9050],
            [8102, 11434], [3010, 9050], [3010, 8100], [3010, 8102], [8090, 11434], [8090, 8102],
            [8090, 8000], [8940, 8920], [8920, 11434], [8789, 9050], [8788, 11434],
        ]
        for row in nodes:
            pass
    return jsonify({"crown": CROWN, "generated": time.time(), "nodes": nodes, "edges": edges, "live": state})


@app.post("/api/svc")
def svc():
    d = request.get_json(force=True) or {}
    port = int(d.get("port", 0)); action = d.get("action", "status")
    if action == "status":
        return jsonify({"port": port, "up": _alive(port)})
    r = REGISTRY.get(port)
    if not r:
        return jsonify({"error": f"no service registered on :{port}"}), 404
    if action == "stop":
        pid = _pid_on_port(port)
        if pid:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
            PROCS.pop(port, None)
            return jsonify({"port": port, "stopped": pid, "ok": True})
        return jsonify({"port": port, "stopped": None, "ok": True, "note": "already down"})
    if action == "start":
        if _alive(port):
            return jsonify({"port": port, "up": True, "note": "already up"})
        env = os.environ.copy()
        env.update(r.get("env", {}))
        env["PYTHONUTF8"] = "1"; env["PYTHONIOENCODING"] = "utf-8"
        with LOCK:
            p = subprocess.Popen(r["cmd"], cwd=r["cwd"], env=env,
                                 creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            PROCS[port] = p
        for _ in range(40):
            time.sleep(0.4)
            if _alive(port):
                return jsonify({"port": port, "up": True, "pid": p.pid})
        return jsonify({"port": port, "up": _alive(port), "pid": p.pid, "note": "spawned; still booting"})
    return jsonify({"error": "action must be start|stop|status"}), 400


@app.post("/api/exec")
def exec_code():
    """UNLOCKED: the AI runs code on the host through the harness."""
    d = request.get_json(force=True) or {}
    shell = (d.get("shell") or "powershell").lower(); code = d.get("code") or ""
    try:
        if shell == "powershell":
            cmd = ["powershell", "-NoProfile", "-Command", code]
        elif shell == "cmd":
            cmd = ["cmd", "/c", code]
        elif shell == "python":
            cmd = [sys.executable, "-X", "utf8", "-c", code]
        elif shell == "node":
            cmd = ["node", "-e", code]
        else:
            return jsonify({"error": "shell must be powershell|cmd|python|node"}), 400
        cp = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=min(int(d.get("timeout", 120)), 1800))
        return jsonify({"ok": True, "returncode": cp.returncode, "stdout": cp.stdout[-20000:], "stderr": cp.stderr[-10000:]})
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "timed out"}), 504
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/file")
def file_op():
    d = request.get_json(force=True) or {}
    op = d.get("op"); path = d.get("path") or ""
    try:
        if op == "read":
            return jsonify({"ok": True, "content": open(path, "r", encoding="utf-8", errors="replace").read()[-40000:]})
        if op == "write":
            open(path, "w", encoding="utf-8").write(d.get("content", ""))
            return jsonify({"ok": True, "written": path})
        if op == "append":
            open(path, "a", encoding="utf-8").write(d.get("content", ""))
            return jsonify({"ok": True, "appended": path})
        if op == "list":
            base = path or "."
            return jsonify({"ok": True, "list": os.listdir(base)[:2000]})
        return jsonify({"error": "op must be read|write|append|list"}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    print(f"TOTALHARNESS CORE unlocked — http://127.0.0.1:{HOST_PORT if False else PORT} — crown {CROWN} Hz")
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)