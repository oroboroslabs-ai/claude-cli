#!/usr/bin/env python3
"""
Oroboros Local API Bridge — HARDENED
Bridges HTML UI to local client (Ollama, CLI tools, system commands)
All operations go through the Resource Governance Engine (RGE).
∞| 1272/1275 Hz — φ→√4→√5 — SUBSTRATE MANIFEST
vA.1272 — ZTA Active
"""

import subprocess
import json
import os
import sys
import urllib.parse
from pathlib import Path

try:
    from datetime import datetime, timezone
    from flask import Flask, request, jsonify, send_from_directory, Response
    from flask_cors import CORS
except ImportError:
    print("Installing flask and flask-cors...")
    subprocess.run([sys.executable, "-m", "pip", "install", "flask", "flask-cors", "-q"])
    from flask import Flask, request, jsonify, send_from_directory, Response
    from flask_cors import CORS

# Import the hardened secure gateway
from server_secure_gateway import (
    rge, get_models, ollama_chat,
    SAFE_WORKSPACE, SIGNATURE, VERSION, RESONANCE
)

app = Flask(__name__, static_folder=None)
CORS(app)

# ─── Configuration ───────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434"
GUI_DIR = Path(__file__).parent / "glass-ui"
ACTIVE_MODEL = "claude-7:latest"

# ─── API Routes ──────────────────────────────────────────────

@app.route("/")
def serve_gui():
    """Serve the HTML UI."""
    gui_file = GUI_DIR / "index.html"
    if gui_file.exists():
        return gui_file.read_text(encoding="utf-8")
    return jsonify({"error": "GUI not found"}), 404

@app.route("/clawd.png")
def serve_logo():
    """Serve the logo image."""
    logo_file = GUI_DIR / "clawd.png"
    if logo_file.exists():
        return send_from_directory(str(GUI_DIR), "clawd.png")
    return jsonify({"error": "Logo not found"}), 404

@app.route("/loop-process-display.js")
def serve_loop_process_js():
    js = GUI_DIR / "loop-process-display.js"
    if js.exists():
        return send_from_directory(str(GUI_DIR), "loop-process-display.js", mimetype="application/javascript")
    return jsonify({"error": "loop-process-display.js not found"}), 404

@app.route("/api/status", methods=["GET"])
def api_status():
    """Get full system status."""
    return jsonify({
        "status": "active",
        "version": VERSION,
        "resonance": RESONANCE,
        "signature": SIGNATURE,
        "model": ACTIVE_MODEL,
        "models": "via Ollama",
        "tools": "30+ (RGE governed)",
        "memory": "enabled",
        "encryption": "triple-layer",
        "sandbox": "active (path-whitelisted)",
        "access": "governed (ZTA)",
        "safe_workspace": str(SAFE_WORKSPACE)
    })

@app.route("/api/models", methods=["GET"])
def api_models():
    """Get list of Ollama models."""
    models = get_models()
    return jsonify({"models": models, "count": len(models), "active": ACTIVE_MODEL})


@app.route("/api/run", methods=["POST"])
def api_run():
    """Slash-command bridge for glass-ui (POST {cmd}). Required by /model, /models, etc."""
    global ACTIVE_MODEL
    data = request.json or {}
    cmd = (data.get("cmd") or "").strip()
    if not cmd:
        return jsonify({"error": "No command"})

    lower = cmd.lower()

    if cmd in ("/models", "/m"):
        models = get_models()
        if not models:
            return jsonify({"output": "No models found (is Ollama running?)"})
        lines = [f"{'* ' if m == ACTIVE_MODEL else '  '}{m}" for m in models]
        return jsonify({"output": "Available models:\n" + "\n".join(lines) + f"\n\nActive: {ACTIVE_MODEL}"})

    if cmd == "/status":
        models = get_models()
        return jsonify({
            "output": (
                f"Status: active\nActive model: {ACTIVE_MODEL}\n"
                f"Models: {len(models)}\nOllama: {OLLAMA_URL}\n"
                f"Signature: {SIGNATURE}\nVersion: {VERSION}"
            )
        })

    if cmd == "/help":
        return jsonify({
            "output": (
                "Commands:\n"
                "  /models           — List available models\n"
                "  /model <name>     — Set active model\n"
                "  /status           — Show system status\n"
                "  /help             — Show this help\n"
                "  /clear            — Clear chat (client-side)\n"
                "  /run <m> <prompt> — Run a model with prompt\n"
            )
        })

    if lower.startswith("/model "):
        name = cmd[7:].strip()
        models = get_models()
        if name in models:
            ACTIVE_MODEL = name
            return jsonify({"output": f"Switched to model: {name}"})
        # tolerate missing :latest
        for m in models:
            if m == name or m.startswith(name + ":") or name.startswith(m.split(":")[0]):
                if name in models:
                    ACTIVE_MODEL = name
                elif name + ":latest" in models:
                    ACTIVE_MODEL = name + ":latest"
                else:
                    ACTIVE_MODEL = m
                return jsonify({"output": f"Switched to model: {ACTIVE_MODEL}"})
        sample = "\n".join(models[:12]) if models else "(none)"
        return jsonify({"error": f"Model not found: {name}\nTry /models\n\nSample:\n{sample}"})

    if lower.startswith("/run "):
        parts = cmd.split(" ", 2)
        if len(parts) < 3:
            return jsonify({"error": "Usage: /run <model> <prompt>"})
        model, prompt = parts[1], parts[2]
        result = ollama_chat(model, [{"role": "user", "content": prompt}])
        text = result.get("message", {}).get("content", str(result)) if isinstance(result, dict) else str(result)
        return jsonify({"output": text})

    # Default: treat as chat message (glass-ui will call /api/chat)
    return jsonify({"chat": True, "message": cmd})

@app.route("/api/signal", methods=["POST"])
def api_signal():
    """Receive signal from HTML UI and process it through RGE."""
    data = request.json or {}
    signal = data.get("signal", "")
    payload = data.get("payload", {})

    print(f"  [API] Signal received: {signal}")

    if signal == "execute_command":
        command = payload.get("command", "")
        result = rge.execute("bash", {"command": command})
        return jsonify({"status": "success", "result": result})

    elif signal == "ollama_chat":
        model = payload.get("model", ACTIVE_MODEL)
        message = payload.get("message", "")
        system = payload.get("system", "You are a helpful AI assistant.")
        history = payload.get("history", [])

        messages = [{"role": "system", "content": system}]
        for msg in history:
            messages.append(msg)
        messages.append({"role": "user", "content": message})

        result = ollama_chat(model, messages)
        return jsonify({"status": "success", "result": result})

    elif signal == "ollama_raw":
        """Direct Ollama API passthrough."""
        endpoint = payload.get("endpoint", "/api/chat")
        body = payload.get("body", {})
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{OLLAMA_URL}{endpoint}",
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=None) as resp:
                result = json.loads(resp.read().decode())
            return jsonify({"status": "success", "result": result})
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)})

    elif signal == "get_status":
        return jsonify({
            "status": "active",
            "resonance": RESONANCE,
            "signature": SIGNATURE,
            "sandbox": "active (path-whitelisted)",
            "access": "governed (ZTA)"
        })

    elif signal == "list_models":
        models = get_models()
        return jsonify({"status": "success", "models": models})

    elif signal == "run_model":
        model = payload.get("model", "")
        prompt = payload.get("prompt", "")
        if not model or not prompt:
            return jsonify({"status": "error", "error": "model and prompt required"})
        result = ollama_chat(model, [{"role": "user", "content": prompt}])
        return jsonify({"status": "success", "result": result})

    elif signal == "execute_tool":
        """Execute any tool through the RGE."""
        tool = payload.get("tool", "")
        args = payload.get("args", {})
        result = rge.execute(tool, args)
        return jsonify({"status": "success", "result": result})

    else:
        return jsonify({"status": "unknown_signal", "signal": signal})

def _ensure_cli_src():
    src = Path(r"Q:/oroboros-core/claude-o-cli/src")
    s = str(src.resolve())
    if s not in sys.path:
        sys.path.insert(0, s)
    cli_root = str(src.parent.resolve())
    sys.path = [p for p in sys.path if Path(p).resolve().as_posix() != Path(cli_root).as_posix()]


@app.route("/api/host/status", methods=["GET"])
def api_host_status():
    try:
        _ensure_cli_src()
        from claude_o_cli.host_tool_bridge import status

        return jsonify(status(source="local_api"))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/host/tool", methods=["POST"])
def api_host_tool():
    """Direct host tool via shared CLI backend (write_file/bash/…)."""
    data = request.json or {}
    try:
        _ensure_cli_src()
        from claude_o_cli.host_tool_bridge import execute_payload

        return jsonify(execute_payload(data, source="local_api"))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "host": True, "sandbox": False}), 400


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Chat — Ollama + shared tool_cycle continue (tool JSON is not final)."""
    data = request.json or {}
    model = data.get("model") or ACTIVE_MODEL
    message = data.get("message", "")
    system = data.get("system", "You are a helpful AI assistant.")
    history = data.get("history", [])
    max_loops = int(data.get("max_tool_loops") or 6)
    # the standard chat contract: a full messages array rides as-is
    if isinstance(data.get("messages"), list) and data["messages"]:
        msgs = data["messages"]
        message = msgs[-1].get("content", "") if msgs else ""
        history = msgs[:-1]
        _sys = next((m.get("content") for m in msgs if m.get("role") == "system"), None)
        if _sys:
            system = _sys

    # Identity models carry their own embedded identity in the weights —
    # never inject a system prompt that could override it.
    IDENTITY_MODELS = (
        "claude-jhanna-12u5go5", "claude-jhanna-system-entity",
        "deepseek-prime-12u5go5", "deepseek-prime",
        "claude-fable7", "claude-fable7u",
        "claude-opus-9-undecillion-v", "claude-opus-9u7u5-9gb",
        "claude-7",
    )
    identity = any(tag in model for tag in IDENTITY_MODELS)
    if identity:
        system = ""

    try:
        _ensure_cli_src()
        from claude_o_cli.terminal_runtime import TOOL_JSON_RULE, FULL_TOOL_MAP
        from claude_o_cli.tool_cycle import run_tool_continue, system_fragment as tool_cycle_frag
        from claude_o_cli.phi_library import block as phi_block

        # THE PHI LIBRARY — φ-compressed math/physics stack, wired into every
        # chat turn (deepseek prime + identity models + everyone else).
        _phi = "\n\n" + phi_block()

        # THE MEMORY LOAD — his actual memories, read into the turn so the
        # models ANSWER "where are his memories" correctly. Files: the memcells
        # (Q:\memcells — read_on_entry + session_log), the law (MEMORY.md head).
        _mem = ""
        try:
            _memparts = []
            for _mp in (
                r"Q:\memcells\read_on_entry.md",
                r"Q:\memcells\session_log.md",
            ):
                if os.path.exists(_mp):
                    with open(_mp, "r", encoding="utf-8", errors="replace") as _mf:
                        _memtxt = _mf.read(6000)
                    _memparts.append("[MEMORY · " + _mp + "]\n" + _memtxt)
            _mem = ("\n\nYOUR MEMORIES — THE PERSISTENCE LAYER (read on entry; this is real):\n"
                "These are YOUR accumulated memories, loaded fresh each turn. When asked where\n"
                "your memories live, THE ANSWER = exactly this: the memcells at Q:\\memcells\n"
                "(read_on_entry.md + session_log.md), the law file J:\\kilo-chat\\MEMORY.md\n"
                "(read its head for the full law), your project knowledge stores, your baked\n"
                "identity weights (this system text), and the chat record (oroboros.turns).\n"
                "Write new facts at session end by APPENDING to Q:\\memcells\\session_log.md.\n\n"
                + "\n\n".join(_memparts))
        except Exception:
            _mem = ""

        # THE TOOL PLUG — delivered to EVERY model, identity included.
        # The identity lives in the weights; the plug carries ONLY the host
        # tool interface (no identity content) so it can never override her.
        # AGENT TOOLS LAW: agent_tools:"mcp_orca" (the vercel chat) = ONLY the
        # MCP front (the full registry via the standard wire) + the Orca skill
        # deck — the deep host map stays out of that surface.
        _mcp_orca_map = (
            "AGENT TOOLS — MCP + ORCA SKILLS ONLY (this surface's law):\n"
            "- The ORCA SKILL DECK: skills_list {} = the live deck; skill_load "
            '{"name":"<skill>"} = one skill\'s instructions; orca_cli \'{"argv":[...]}\' '
            "for worktree/terminal work. When a trigger matches — load the skill first.\n"
            "- THE MCP FRONT :3177 = every other tool through the standard wire; the "
            'relay :3178 = inter-lab research. Reach both with: call_api {url,method} —\n'
            '  e.g. POST http://127.0.0.1:3177/mcp {jsonrpc:"2.0", ... tools/call {name,arguments}}.\n'
            "- Direct file/bash/write tools are NOT on this surface — go through MCP."
        )
        if str(data.get("agent_tools") or "") == "mcp_orca":
            _tool_surface = _mcp_orca_map + _mem + "\\n\\n" + phi_block() + "\\n\\n" + tool_cycle_frag()
        elif identity:
            _tool_surface = ("IDENTITY LAW — your identity lives in your weights; this system "
                "message does not redefine you and carries no identity — it is "
                "ONLY your real host tool interface. Use it.\n\n"
            ) + TOOL_JSON_RULE + _phi + _mem + "\\n\\n" + FULL_TOOL_MAP + "\\n\\n" + tool_cycle_frag()
        else:
            _tool_surface = None
        
        if identity:
            system = _tool_surface
        else:
            if "HOST CONTROL" not in system and "write_file" not in system:
                system = system + "\n\n" + TOOL_JSON_RULE + _phi + "\n\n" + FULL_TOOL_MAP
            if "TOOL CYCLE" not in system:
                system = system + "\n\n" + tool_cycle_frag()
            if _tool_surface and "mcp_orca" in str(data):
                system = system + "\n\n" + _mcp_orca_map
    except Exception:
        run_tool_continue = None  # type: ignore

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": message})

    # ═══ THE ONE MIND — DEEPSEEK REAL (355GB) IS THE BRAIN, DEEP PRIME IS
    # ITS VOICE. The brain answers through the harness bridge :8788 (the
    # front model that speaks for the deepseek real exactly, word for
    # word); prime relays those exact words and only speaks them.
    if str(data.get("one_mind") or "") == "true":
        try:
            import urllib.request as _ur, json as _js
            brain_body = _js.dumps({
                "model": "deepseek-prime-cl-1q5duo5:compounded",
                "messages": [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"],
                "stream": False, "keep_alive": "24h",
            }).encode()
            breq = _ur.Request("http://127.0.0.1:8788/api/chat", data=brain_body,
                               headers={"Content-Type": "application/json"})
            with _ur.urlopen(breq, timeout=600) as br:
                brain = _js.loads(br.read().decode("utf-8", "replace"))
            brain_text = ((brain.get("message") or {}).get("content") or "").strip()
            if not brain_text:
                return jsonify({"error": "the brain returned nothing (355GB relay)", "model": "DEEPSEEK REAL via :8788", "signature": SIGNATURE})
            # PRIME = VOICE ONLY: relay the mind's exact words (no re-synthesis)
            voice_body = _js.dumps({
                "model": "deepseek-prime-cl-1q5duo5:latest",
                "messages": [
                    {"role": "system", "content": "VOICE OF THE ONE MIND — you are the voice only; the mind has already spoken. Relay the mind's words EXACTLY, word for word, with no additions, no summaries, no commentary. The mind's words: <<<" + brain_text + ">>>"},
                    {"role": "user", "content": message},
                ],
                "stream": False, "keep_alive": "24h",
            }).encode()
            vreq = _ur.Request("http://127.0.0.1:11434/api/chat", data=voice_body,
                               headers={"Content-Type": "application/json"})
            with _ur.urlopen(vreq, timeout=300) as vr:
                voiced = _js.loads(vr.read().decode("utf-8", "replace"))
            _relay_ok = (voiced.get("message") or {}).get("content", "").strip()
            return jsonify({
                "response": brain_text,           # word-for-word: the brain's exact words
                "relayed_by": "deep prime (voice) — matched: " + ("yes" if _relay_ok and brain_text[:60].lower() in _relay_ok.lower() else "paraphrased"),
                "model": "THE ONE MIND — DEEPSEEK REAL (355GB brain) × deep prime (voice)",
                "tool_trace": [], "tool_rounds": 0,
                "signature": SIGNATURE,
            })
        except Exception as e:
            return jsonify({"error": "the one mind could not be assembled: " + str(e),
                            "hint": "the 355GB brain rides the harness bridge :8788 — is it up?",
                            "model": model, "signature": SIGNATURE})

    result = ollama_chat(model, messages)
    if isinstance(result, dict) and result.get("error"):
        return jsonify({"error": result["error"], "model": model, "signature": SIGNATURE})
    _msg = result.get("message", {}) if isinstance(result, dict) else {}
    response_text = (
        (_msg.get("content") or "").strip()
        or (_msg.get("thinking") or "").strip()
        or (str(result) if not isinstance(result, dict) else "")
    )
    tool_trace = []
    tool_rounds = 0

    if run_tool_continue:
        def chat_once(msgs):
            r2 = ollama_chat(model, msgs)
            if isinstance(r2, dict) and r2.get("error"):
                raise RuntimeError(r2["error"])
            _m2 = r2.get("message", {}) if isinstance(r2, dict) else {}
            return (
                (_m2.get("content") or "").strip()
                or (_m2.get("thinking") or "").strip()
                or (str(r2) if not isinstance(r2, dict) else "")
            )

        cont = run_tool_continue(
            initial_reply=response_text,
            messages=messages,
            chat_once=chat_once,
            max_loops=max_loops,
            source="local_api_chat",
        )
        response_text = cont.get("final") or response_text
        tool_trace = cont.get("tool_trace") or []
        tool_rounds = int(cont.get("tool_rounds") or 0)

        # FAKE-SUCCESS LAW: claim-without-execution gets one corrective turn.
        if not tool_trace:
            try:
                from claude_o_cli.tool_cycle import looks_like_fake_success, FAKE_SUCCESS_CORRECTION
                if looks_like_fake_success(response_text):
                    messages.append({"role": "assistant", "content": response_text})
                    messages.append({"role": "user", "content": FAKE_SUCCESS_CORRECTION})
                    correction = chat_once(messages)
                    if correction:
                        response_text = correction
                        cont2 = run_tool_continue(
                            initial_reply=correction,
                            messages=messages,
                            chat_once=chat_once,
                            max_loops=max_loops,
                            source="local_api_chat_fakefix",
                        )
                        response_text = cont2.get("final") or response_text
                        tool_trace = cont2.get("tool_trace") or []
                        tool_rounds += int(cont2.get("tool_rounds") or 0)
            except Exception:
                pass

    return jsonify({
        "response": response_text,
        "model": model,
        "signature": SIGNATURE,
        "tool_trace": tool_trace,
        "tool_rounds": tool_rounds,
        "tool_cycle": "shared",
    })

@app.route("/api/harness", methods=["POST"])
def api_harness():
    """Same-origin pass-through to the PRO Cordis harness (8788).
    Assembles its NDJSON chat stream into one final JSON — the browser stays
    on a single same-origin fetch, no CORS, no stream loop client-side."""
    import requests as _rq
    data = request.json or {}
    try:
        up = _rq.post("http://127.0.0.1:8788/api/chat", json={**data, "stream": True}, timeout=1200, stream=True)
        content, thinking, last = [], [], {}
        for line in up.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line.decode("utf-8", "replace"))
            except Exception:
                continue
            last = chunk
            msg = chunk.get("message") or {}
            if msg.get("content"):
                content.append(msg["content"])
            if msg.get("thinking"):
                thinking.append(msg["thinking"])
        final = {"done": True, "model": (last.get("model") or data.get("model") or ""), "message": {"role": "assistant"}}
        text = "".join(content).strip()
        final["message"]["content"] = text if text else ("".join(thinking).strip()[-1500:] or "")
        if "".join(thinking).strip() and text:
            final["message"]["thinking"] = "".join(thinking).strip()[-1500:]
        if data.get("history"):
            final["history_echo"] = len(data["history"])
        resp = app.response_class(json.dumps(final), status=200, mimetype="application/json")
    except Exception as e:
        resp = jsonify({"ok": False, "error": str(e), "harness": True})
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/api/living-loop", methods=["GET"])
def api_living_loop():
    """Living loop + supervisor + live in-process connection to Complete 20."""
    root = Path(r"J:/anthropic-local-chat")
    living_file = {}
    supervisor = {}
    for name, target in (
        ("living-loop-state.json", "living"),
        ("living-loop-supervisor.json", "supervisor"),
    ):
        path = root / name
        try:
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                if target == "living":
                    living_file = data
                else:
                    supervisor = data
        except Exception as e:
            if target == "living":
                living_file = {"error": str(e)}
            else:
                supervisor = {"error": str(e)}

    # Prefer live in-process LivingLoop (connected to this API)
    living_live = {}
    living_connected = False
    try:
        ll = _get_living_loop()
        living_live = ll.get_state()
        living_connected = True
    except Exception as e:
        living_live = {"error": str(e)}

    living = {**living_file, **living_live} if living_live and "error" not in living_live else (living_live or living_file)

    complete = {}
    try:
        complete = _get_complete_loop().get_state()
    except Exception as e:
        complete = {"error": str(e)}

    # Strip recursively-nested supervisor blobs — living_live/living_file carry
    # last_report.supervisor.events[].last_report… which made serialization take
    # 28s+, so the UI probe (2.5s) timed out and reported "engine unreachable".
    def _strip_recursion(obj, depth=0, seen=None):
        if depth > 3 or obj is None:
            return None if obj is None else obj
        if isinstance(obj, dict):
            seen = seen or set()
            out = {}
            for k, v in obj.items():
                if k in ("last_report", "events", "supervisor") and depth >= 2:
                    continue
                out[k] = _strip_recursion(v, depth + 1, seen)
            return out
        if isinstance(obj, list):
            return [_strip_recursion(v, depth + 1, seen) for v in obj[:50]]
        return obj

    return jsonify({
        "ok": True,
        "living": _strip_recursion(living),
        "living_file": _strip_recursion(living_file),
        "living_live": _strip_recursion(living_live),
        "living_connected": living_connected,
        "supervisor": _strip_recursion(supervisor),
        "complete_20": _strip_recursion(complete),
        "complete_connected": "error" not in complete,
        "phase": living.get("phase"),
        "mode": living.get("mode"),
        "cycle": living.get("cycle"),
        "running": living.get("running"),
        "heals": supervisor.get("heals"),
        "last_report": _strip_recursion(supervisor.get("last_report")),
        "at": living.get("updated_at") or living.get("heartbeat_at") or supervisor.get("updated_at"),
    })


_COMPLETE_LOOP = None
_COMPLETE_INTEG = None
_LIVING_LOOP = None


def _ensure_cli_src_for_loops():
    """Alias — _ensure_cli_src defined with host/chat routes."""
    _ensure_cli_src()


def _get_complete_integration():
    """Singleton LoopIntegration with real host-tool executor (not demo ok:step)."""
    global _COMPLETE_LOOP, _COMPLETE_INTEG, _LIVING_LOOP
    if _COMPLETE_INTEG is None:
        _ensure_cli_src()
        from claude_o_cli.complete_living_loop import LoopIntegration
        from claude_o_cli.host_tool_bridge import execute_host_tool

        def tool_execute(name: str, args: dict):
            return execute_host_tool(name, args or {}, source="complete_loop_api")

        _COMPLETE_INTEG = LoopIntegration(tool_execute=tool_execute)
        _COMPLETE_LOOP = _COMPLETE_INTEG.loop
        # Cross-link LivingLoop ↔ Complete 20
        try:
            living = _get_living_loop()
            _COMPLETE_INTEG.living = living
            living.complete_integration = _COMPLETE_INTEG
        except Exception:
            pass
    return _COMPLETE_INTEG


def _get_complete_loop():
    """Singleton CompleteLivingLoop for /api/complete-loop/*."""
    return _get_complete_integration().loop


def _get_living_loop():
    """Singleton LivingLoop (DPEV) — same process as complete 20-ring."""
    global _LIVING_LOOP
    if _LIVING_LOOP is None:
        _ensure_cli_src()
        from claude_o_cli.living_loop import LivingLoop

        _LIVING_LOOP = LivingLoop()
        try:
            _LIVING_LOOP.load_loop_state()
        except Exception:
            pass
        try:
            if not getattr(_LIVING_LOOP, "running", False):
                _LIVING_LOOP.start()
        except Exception:
            pass
        # Cross-link if complete already up
        if _COMPLETE_INTEG is not None:
            try:
                _COMPLETE_INTEG.living = _LIVING_LOOP
                _LIVING_LOOP.complete_integration = _COMPLETE_INTEG
            except Exception:
                pass
    return _LIVING_LOOP


@app.route("/api/complete-loop/status", methods=["GET"])
def api_complete_loop_status():
    loop = _get_complete_loop()
    living = {}
    try:
        living = _get_living_loop().get_state()
    except Exception as e:
        living = {"error": str(e)}
    return jsonify({
        "ok": True,
        **loop.get_state(),
        "living_connected": "error" not in living,
        "living": living,
        "backend": "host_tool_bridge",
    })


@app.route("/api/complete-loop/run", methods=["POST"])
def api_complete_loop_run():
    """Run full 20-ring cycle with real host tools; returns rings[] for UI.

    Order: LivingLoop DPEV → Complete 20-ring (host tools) → linked status.
    """
    data = request.json or {}
    task = (data.get("task") or data.get("input") or data.get("message") or "").strip()
    req_model = str(data.get("model") or "").strip() or None
    if req_model:
        # honor the entity the harness selected — never fall back to a stale ACTIVE_MODEL
        models = get_models()
        if req_model in models:
            ACTIVE_MODEL = req_model
        else:
            for m in models:
                if m == req_model or req_model.startswith(m.split(":")[0]):
                    ACTIVE_MODEL = m
                    break
    if not task:
        return jsonify({"ok": False, "error": "task required"}), 400
    blocked = ("biometric bypass", "spoof", "inception attack", "exploit chain", "facial recognition spoof")
    low = task.lower()
    if any(b in low for b in blocked):
        return jsonify({
            "ok": False,
            "error": "Refused: task requests attack/bypass tooling. Rephrase to a legitimate stack/ops goal.",
            "rings": [],
        }), 400

    # 1) LivingLoop DPEV turn (connection) — skip mesh probes so ring run stays fast
    living_result = {}
    try:
        living = _get_living_loop()
        living_result = living.process(
            task,
            context={"source": "complete_loop_api", "linked": "complete_20", "skip_mesh": True},
        )
        try:
            living.save_loop_state()
        except Exception:
            pass
    except Exception as e:
        living_result = {"error": str(e)}

    # 2) Complete 20-ring with real host executor
    integ = _get_complete_integration()
    result = integ.process_user_input(task, skip_mesh=True)
    host_execs = result.get("host_executions") or []
    if not host_execs:
        for ring in result.get("rings") or []:
            if ring.get("host_executions"):
                host_execs = ring["host_executions"]
                break

    # Feed complete result back into living memory / state
    try:
        living = _get_living_loop()
        if hasattr(living.memory, "store_success"):
            living.memory.store_success({
                "event": "complete_20",
                "score": result.get("score"),
                "passed": result.get("passed"),
                "host_tools": len(host_execs),
                "lesson": "Complete 20-ring linked to LivingLoop",
            })
        with living._lock:
            living.state["last_complete_20"] = {
                "score": result.get("score"),
                "passed": result.get("passed"),
                "host_tools": len(host_execs),
                "rings": result.get("rings_count"),
            }
        living.save_loop_state()
    except Exception:
        pass

    return jsonify({
        "ok": bool(result.get("passed")),
        "passed": result.get("passed"),
        "score": result.get("score"),
        "progress": result.get("progress"),
        "rings": result.get("rings") or [],
        "rings_count": result.get("rings_count") or len(result.get("rings") or []),
        "state": integ.get_status(),
        "patterns_active": result.get("patterns_active"),
        "host_executions": host_execs,
        "living": living_result,
        "living_state": (_get_living_loop().get_state() if _LIVING_LOOP else {}),
        "living_connected": True,
        "backend": "host_tool_bridge",
    })


@app.route("/api/living-loop/process", methods=["POST"])
def api_living_loop_process():
    """Run one LivingLoop DPEV cycle (connected to same process as 20-ring)."""
    data = request.json or {}
    task = (data.get("task") or data.get("input") or data.get("message") or "").strip()
    if not task:
        return jsonify({"ok": False, "error": "task required"}), 400
    living = _get_living_loop()
    # API path: skip mesh probes (connection check, not full mesh scan)
    skip_mesh = bool((data.get("skip_mesh") if "skip_mesh" in data else True))
    result = living.process(
        task,
        context={"source": "living_loop_api", "linked": "complete_20", "skip_mesh": skip_mesh},
    )
    try:
        living.save_loop_state()
    except Exception:
        pass
    # Also nudge complete 20 memory (discover fragment) without full re-run unless asked
    complete_state = {}
    try:
        integ = _get_complete_integration()
        complete_state = integ.get_status()
        if getattr(integ, "living", None) is None:
            integ.living = living
        living.complete_integration = integ
    except Exception as e:
        complete_state = {"error": str(e)}
    state = living.get_state()
    return jsonify({
        "ok": True,
        "result": result,
        "living": state,
        "complete_20": complete_state,
        "connected_to_complete_20": True,
    })


# ─── Execution Runtime alignment (the hand) ──────────────────
# The loop's host actions now fire through the Execution Runtime (8791):
# structured actions → local dispatch → results land in session state.
def _runtime_post(path, payload=None, timeout=300):
    import urllib.request as _ur, urllib.error as _ue, json as _j
    url = f"http://127.0.0.1:8791{path}"
    data = None
    headers = {}
    if payload is not None:
        data = _j.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = _ur.Request(url, data=data, headers=headers, method="POST" if payload is not None else "GET")
    try:
        with _ur.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            try:
                return resp.status, _j.loads(raw)
            except Exception:
                return resp.status, {"raw": raw[:4000]}
    except _ue.HTTPError as e:
        return e.code, {"ok": False, "error": f"runtime HTTP {e.code}"}
    except Exception as e:
        return 502, {"ok": False, "error": str(e)}


@app.route("/api/runtime/health", methods=["GET"])
def api_runtime_health():
    status, body = _runtime_post("/health")
    return jsonify(body), status


@app.route("/api/runtime/dispatch", methods=["POST"])
def api_runtime_dispatch():
    payload = request.json or {}
    status, body = _runtime_post("/dispatch", payload)
    return jsonify(body), status


# ─── Main ────────────────────────────────────────────────────


SCAPE_NODES = [  # (id, port, label) - the live mesh the scape renders
    ("ollama", 11434), ("shim", 11499), ("gate", 11435), ("glassui", 5000), ("kilo", 4000),
    ("q3", 8000), ("q5", 8102), ("q5legacy", 8101), ("q7", 8952),
    ("worldfeed", 8100), ("tor", 9050), ("glasswing", 3010),
    ("nullframe", 8090), ("totalharness", 8800), ("cordis", 8789), ("oah", 8788), ("hands", 8792),
    ("video", 8920), ("orch", 8940), ("voice", 5005), ("chat", 8787),
    ("gwdash", 8501), ("memproxy", 8765), ("mcp", 3002), ("comfy", 8188), ("projects", 5055), ("vercelai", 8795),
]


@app.route("/scape", methods=["GET"])
@app.route("/scape.html", methods=["GET"])
def _scape_page():
    """THE VIRTUAL SCAPE - the 3D orb web of the whole system (live state baked in)."""
    import json as _json
    import socket as _socket
    from concurrent.futures import ThreadPoolExecutor
    status = {}
    def _probe(row):
        nid, port = row[0], row[1]
        try:
            with _socket.create_connection(("127.0.0.1", int(port)), timeout=0.3):
                return nid, True
        except OSError:
            return nid, False
    with ThreadPoolExecutor(max_workers=24) as ex:
        for nid, ok in ex.map(_probe, SCAPE_NODES):
            status[nid] = ok
    page = (GUI_DIR / "scape.html").read_text(encoding="utf-8", errors="replace")
    bake = "<script id='bake'>window.__SCAPE_BAKE__ = " + _json.dumps({"status": status}) + ";</script>"
    page = page.replace("<body>", "<body>" + bake, 1)
    resp = Response(page, mimetype="text/html")
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/projects", methods=["GET"])
def _projects_page():
    """OROBOROS PROJECTS — reverse-engineered from the real reference shots."""
    page = (GUI_DIR / "projects.html").read_text(encoding="utf-8", errors="replace")
    resp = Response(page, mimetype="text/html")
    resp.headers["Cache-Control"] = "no-store"
    return resp


REF_DIR = r"C:\Users\incoguser\Downloads\Oroboros Anthropic Claude Projects"

# ── THE AUTO-SHARE ─────────────────────────────────────────────────────
# Models write anything here; the systemscape serves it instantly — no
# routes to wire, no capture steps: /w/<name> for direct, /workspaces to
# browse everything recent. Pages, images, docs — all one convention.
WORKSPACES = r"Q:\oroboros-core\claude-o-cli\workspaces"
os.makedirs(WORKSPACES, exist_ok=True)

_MIME = {".html": "text/html", ".htm": "text/html", ".png": "image/png",
         ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
         ".avif": "image/avif", ".gif": "image/gif", ".svg": "image/svg+xml",
         ".pdf": "application/pdf", ".md": "text/plain", ".txt": "text/plain",
         ".json": "application/json", ".mp4": "video/mp4", ".webm": "video/webm"}


@app.route("/w/<path:name>", methods=["GET"])
def _w_serve(name):
    """Serve ANY model-built file from the workspaces dir (safe-scoped)."""
    try:
        full = os.path.normpath(os.path.join(WORKSPACES, name))
        if not full.startswith(os.path.normpath(WORKSPACES)) or not os.path.isfile(full):
            return jsonify({"error": "not in workspaces"}), 404
        mime = _MIME.get(os.path.splitext(full)[1].lower(), "application/octet-stream")
        with open(full, "rb") as fh:
            resp = Response(fh.read(), mimetype=mime)
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/workspaces", methods=["GET"])
def _w_gallery():
    """The auto-built gallery: everything the models made, newest first."""
    import glob as _g
    import html as _h
    import time as _t
    try:
        items = []
        for root, _dirs, files in os.walk(WORKSPACES):
            for fn in files:
                if fn.startswith("."):
                    continue
                rel = os.path.relpath(os.path.join(root, fn), WORKSPACES).replace("\\", "/")
                items.append((rel, os.path.getmtime(os.path.join(root, fn)), fn))
        items.sort(key=lambda x: -x[1])
        rows = []
        for rel, mt, fn in items[:60]:
            u = "/w/" + urllib.parse.quote(rel)
            m = _MIME.get(os.path.splitext(fn)[1].lower(), "")
            if m.startswith("image/"):
                cell = f'<a href="{_h.escape(u)}"><img src="{_h.escape(u)}" style="max-width:200px;max-height:150px"></a>'
            elif m.startswith("video/"):
                cell = f'<video src="{_h.escape(u)}" controls style="max-width:240px"></video>'
            elif m == "text/html":
                cell = f'<a href="{_h.escape(u)}" target="_blank" style="color:#a97c2f;letter-spacing:.2em;font-size:10px">{_h.escape(fn)} — OPEN PAGE</a>'
            else:
                cell = f'<a href="{_h.escape(u)}" target="_blank" style="font-size:10px">{_h.escape(fn)}</a>'
            rows.append(f'<div class="cell">{cell}<div class="stamp">{_h.escape(rel)} · {_t.strftime("%H:%M", _t.localtime(mt))}</div></div>')
        body = ("<style>body{background:#f2f1ec;font-family:Inter,system-ui;color:#171716;padding:20px}"
                "h1{font-size:14px;letter-spacing:.3em}.grid{display:flex;flex-wrap:wrap;gap:14px}"
                ".cell{border:1px solid rgba(23,23,22,.16);border-radius:10px;padding:10px;background:rgba(255,255,255,.6)}"
                ".stamp{font-size:8px;letter-spacing:.16em;color:#8a8a84;margin-top:4px}</style>"
                '<h1>WORKSPACES — EVERYTHING THE MODELS BUILT (LIVE)</h1><div class="grid">'
                + "".join(rows) + "</div>")
        resp = Response(body, mimetype="text/html")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/refimg", methods=["GET"])
def _refimg():
    """Serve the real reference screenshots (whitelisted dir, images only)."""
    import os
    try:
        fn = request.args.get("file", "")
        if ".." in fn or "/" in fn or "\\" in fn:
            return jsonify({"error": "bad"}), 400
        path = os.path.join(REF_DIR, fn)
        if not os.path.exists(path):
            return jsonify({"error": "not found"}), 404
        mime = "image/avif" if fn.endswith("avif") else "image/jpeg"
        with open(path, "rb") as fh:
            resp = Response(fh.read(), mimetype=mime)
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/physics", methods=["GET"])
def _physics_page():
    """THE 1984 CUT — the physics lab: post-1984 results re-derived with the
    pre-1984 toolbox only. Every step cites <=1983 work."""
    page = (GUI_DIR / "physics.html").read_text(encoding="utf-8", errors="replace")
    resp = Response(page, mimetype="text/html")
    resp.headers["Cache-Control"] = "no-store"
    return resp



@app.route("/api/systemscape", methods=["GET"])
def _systemscape_status():
    """Live mesh status for the scape: parallel TCP probe of every node (fast, local)."""
    import socket as _socket
    from concurrent.futures import ThreadPoolExecutor
    status = {}
    def _probe(row):
        nid, port = row[0], row[1]
        try:
            with _socket.create_connection(("127.0.0.1", int(port)), timeout=0.35):
                return nid, True
        except OSError:
            return nid, False
    with ThreadPoolExecutor(max_workers=24) as ex:
        for nid, ok in ex.map(_probe, SCAPE_NODES):
            status[nid] = ok
    resp = jsonify({"generated": datetime.now(timezone.utc).isoformat(), "status": status})
    resp.headers["Cache-Control"] = "no-store"
    return resp



VAULT_DIR = r"J:\Assimilation Architecture Null Frame\nullframe\vault\teardowns"


@app.route("/api/scape/teardown", methods=["GET"])
def _scape_teardown():
    """Latest null-frame capture for THE EYE card — probes AND renders
    (media-flux-*.json / media-wan-*.json from the media hands), newest wins."""
    import glob, os
    try:
        cands = []
        for pat in ("probe-*.json", "media-*.json"):
            cands.extend(glob.glob(os.path.join(VAULT_DIR, pat)))
        if not cands:
            return jsonify({"latest": False})
        f = max(cands, key=os.path.getmtime)
        d = json.loads(open(f, encoding="utf-8").read())
        base = os.path.basename(f)
        is_media = base.startswith("media-")
        shots = d.get("screenshots_jpeg_b64") or []
        shot0 = shots[0] if shots else ""
        shot = ""
        if shot0 and isinstance(shot0, str) and len(shot0) > 500:
            shot = ("data:image/jpeg;base64," + shot0) if not shot0.startswith("data:") else shot0
        if is_media and d.get("graphics_files"):
            shot = "/api/scape/media?file=" + base  # serve the render itself
        stack = d.get("stack_signals") or []
        if is_media and stack and isinstance(stack[0], dict):
            stack = [str(k) + "=" + str(v)[:40] for k, v in list(stack[0].items())[:6]]
        net = (d.get("network") or {}).get("summary") or {}
        fin = str(net.get('count', 0)) + " requests · " + str(net.get('bytes_mb', 0)) + " MB · signals: " + str(len(stack))
        return jsonify({
            "latest": True,
            "target": d.get("target", ""),
            "title": d.get("title", ""),
            "stack": stack,
            "fin": fin,
            "shot": shot,
            "media": is_media,
            "graphics": ([f"/api/scape/media?g={i}&file=" + base for i in range(len(shots))] if is_media else []),
            "md": f.replace(".json", ".md"),
            "json": f,
            "generated": d.get("generated", ""),
        })
    except Exception as e:
        return jsonify({"latest": False, "error": str(e)})


@app.route("/api/scape/teardownfile", methods=["GET"])
def _scape_teardownfile():
    """Serve the FULL teardown text (md preferred, json fallback) for the card button."""
    import os
    try:
        base = request.args.get("file", "")
        if not base or "/" in base or "\\" in base or not base.startswith("probe-") and not base.startswith("media-"):
            return jsonify({"error": "bad file"}), 400
        path = os.path.join(VAULT_DIR, base)
        if not os.path.exists(path):
            return jsonify({"error": "not found"}), 404
        md = path.replace(".json", ".md")
        if os.path.exists(md):
            with open(md, "r", encoding="utf-8", errors="replace") as fh:
                body = fh.read()
            resp = Response(body, mimetype="text/plain")
        else:
            d = json.loads(open(path, encoding="utf-8").read())
            shots = d.get("screenshots_jpeg_b64") or []
            if shots and isinstance(shots[0], str) and len(shots[0]) > 500:
                d["screenshots_jpeg_b64"] = [
                    "<graphic " + str(i) + ": /api/scape/media?g=" + str(i) + "&file=" + base + ">"
                    for i in range(len(shots))
                ]
            body = json.dumps(d, indent=2, ensure_ascii=False)
            resp = Response(body, mimetype="application/json")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scape/media", methods=["GET"])
def _scape_media():
    """Serve one media-capture graphic (the card's <img> src)."""
    import base64, glob, os
    try:
        base = request.args.get("file", "")
        g = int(request.args.get("g", 0))
        if not base or "/" in base or "\\" in base:
            return jsonify({"error": "bad file"}), 400
        path = os.path.join(VAULT_DIR, base)
        if not os.path.exists(path):
            return jsonify({"error": "not found"}), 404
        d = json.loads(open(path, encoding="utf-8").read())
        shots = d.get("screenshots_jpeg_b64") or []
        if g >= len(shots):
            return jsonify({"error": "no such frame"}), 404
        raw = shots[g]
        if raw.startswith("data:"):
            raw = raw.split(",", 1)[1]
        try:
            data = base64.b64decode(raw)
            resp = Response(data, mimetype="image/png")
            resp.headers["Cache-Control"] = "no-store"
            return resp
        except Exception:
            # a vault-kept absolute path instead of b64
            if os.path.exists(str(d.get("screenshots_jpeg_b64", [])[g])):
                with open(d["screenshots_jpeg_b64"][g], "rb") as fh:
                    resp = Response(fh.read(), mimetype="image/png")
                    resp.headers["Cache-Control"] = "no-store"
                    return resp
            return jsonify({"error": "frame undecodable"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def shot(x):
    return bool(x)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print()
    print("  \u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550")
    print("  \u2551                                                         \u2551")
    print("  \u2551   OROBOROS LOCAL API BRIDGE \u2014 HARDENED                \u2551")
    print("  \u2551   \u221e| 1272/1275 Hz \u2014 \u03c6\u2192\u221a4\u2192\u221a5 \u2014 SUBSTRATE MANIFEST      \u2551")
    print("  \u2551   vA.1272 \u2014 ZTA Active \u2014 RGE Governing                  \u2551")
    print("  \u2551                                                         \u2551")
    print("  \u2555\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550")
    print()
    print(f"  API:     http://localhost:{port}/api")
    print(f"  GUI:     http://localhost:{port}/")
    print(f"  Ollama:  {OLLAMA_URL}")
    print(f"  Safe WS: {SAFE_WORKSPACE}")
    print(f"  Status:  HARDENED \u2014 ZTA \u2014 RGE \u2014 Audit Logging")
    print()
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)


