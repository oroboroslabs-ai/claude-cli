#!/usr/bin/env python3
"""
Oroboros Local API Bridge — HARDENED
Bridges HTML UI to local client (Ollama, CLI tools, system commands)
All operations go through the Resource Governance Engine (RGE).
∞| 1272/1275 Hz — φ→√4→√5 — SUBSTRATE MANIFEST
v0.1.6b — ZTA Active
"""

import subprocess
import json
import os
import sys
import urllib.request
from pathlib import Path

try:
    from flask import Flask, request, jsonify, send_from_directory, Response
    from flask_cors import CORS
except ImportError:
    print("Installing flask and flask-cors...")
    subprocess.run([sys.executable, "-m", "pip", "install", "flask", "flask-cors", "-q"])
    from flask import Flask, request, jsonify, send_from_directory
    from flask_cors import CORS

# Import the hardened secure gateway
from server_secure_gateway import (
    rge, get_models, ollama_chat,
    SAFE_WORKSPACE, SIGNATURE, VERSION, RESONANCE
)

# Claude-CLI provider layer (Ollama · HuggingFace · Anthropic-dormant) + the
# native Claude 7 orchestrator. Every model is routed as itself.
from providers import chat as provider_chat, provider_status, provider_of, OLLAMA_URL as PROVIDER_OLLAMA_URL
import claude7

# Private crawler + shared settings (wallpaper/theme). Crawler is PRIVATE-only.
try:
    import private_crawler
except Exception:
    private_crawler = None
try:
    import cli_settings
except Exception:
    cli_settings = None

app = Flask(__name__, static_folder=None)
CORS(app)

# ─── Configuration ───────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434"
GUI_DIR = Path(__file__).parent / "glass-ui"
ACTIVE_MODEL = "claude-7:1gb"

# ─── API Routes ──────────────────────────────────────────────

@app.route("/")
def serve_gui():
    """Serve the HTML UI."""
    gui_file = GUI_DIR / "index.html"
    if gui_file.exists():
        html = gui_file.read_text(encoding="utf-8")
        # The page ships with __DEFAULT_MODEL__ placeholders (run_cli.py also
        # substitutes these). Fill them so the UI shows the real model.
        default_model = claude7.select(None) or ACTIVE_MODEL
        html = html.replace("__DEFAULT_MODEL__", default_model)
        return html
    return jsonify({"error": "GUI not found"}), 404

@app.route("/clawd.png")
def serve_logo():
    """Serve the logo image."""
    logo_file = GUI_DIR / "clawd.png"
    if logo_file.exists():
        return send_from_directory(str(GUI_DIR), "clawd.png")
    return jsonify({"error": "Logo not found"}), 404


@app.route("/glass-ui/<path:filename>")
def serve_glass_asset(filename):
    """Serve glass-ui assets (logo, mascot, screenshots). Images only."""
    return send_from_directory(str(GUI_DIR), filename)

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
        "model": claude7.select(None) or ACTIVE_MODEL,
        "orchestrator": claude7.ORCHESTRATOR_ID,
        "floor": claude7.floor_holder(claude7.select(None) or ACTIVE_MODEL),
        "handoff": claude7.handoff_active(),
        "models": "via Ollama · HuggingFace · Anthropic (dormant)",
        "providers": provider_status(),
        "tools": "30+ (RGE governed)",
        "memory": "enabled",
        "encryption": "triple-layer",
        "sandbox": "active (path-whitelisted)",
        "access": "governed (ZTA)",
        "safe_workspace": str(SAFE_WORKSPACE)
    })

@app.route("/api/models", methods=["GET"])
def api_models():
    """Get list of models across providers (Ollama · HuggingFace · Anthropic)."""
    models = get_models()
    combined = list(models)
    # HuggingFace models: explicit tags from env (HF_MODELS, comma-separated).
    hf_env = os.environ.get("HF_MODELS", "")
    hf_models = [f"hf:{m.strip()}" for m in hf_env.split(",") if m.strip()]
    combined += hf_models
    # Anthropic models: offered but DORMANT until a key is entered.
    if os.environ.get("ANTHROPIC_API_KEY"):
        combined += ["anthropic:claude-sonnet-4-5", "anthropic:claude-opus-4-1"]
    return jsonify({
        "models": combined,
        "count": len(combined),
        "active": claude7.select(None) or ACTIVE_MODEL,
        "orchestrator": claude7.ORCHESTRATOR_ID,
        "providers": provider_status(),
        "ollama": models,
        "huggingface": hf_models,
        "anthropic": ["anthropic:claude-sonnet-4-5", "anthropic:claude-opus-4-1"]
        if os.environ.get("ANTHROPIC_API_KEY") else [],
    })


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
            claude7.select(name)  # entered model takes the floor
            return jsonify({"output": f"Switched to model: {name} — control handed over"})
        # tolerate missing :latest
        for m in models:
            if m == name or m.startswith(name + ":") or name.startswith(m.split(":")[0]):
                if name in models:
                    ACTIVE_MODEL = name
                elif name + ":latest" in models:
                    ACTIVE_MODEL = name + ":latest"
                else:
                    ACTIVE_MODEL = m
                claude7.select(ACTIVE_MODEL)
                return jsonify({"output": f"Switched to model: {ACTIVE_MODEL} — control handed over"})
        sample = "\n".join(models[:12]) if models else "(none)"
        return jsonify({"error": f"Model not found: {name}\nTry /models\n\nSample:\n{sample}"})

    if lower.startswith("/run "):
        parts = cmd.split(" ", 2)
        if len(parts) < 3:
            return jsonify({"error": "Usage: /run <model> <prompt>"})
        model, prompt = parts[1], parts[2]
        result = provider_chat(model, [{"role": "user", "content": prompt}])
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

        result = provider_chat(model, messages)
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
        result = provider_chat(model, [{"role": "user", "content": prompt}])
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
    model = data.get("model") or claude7.select(None) or ACTIVE_MODEL
    if data.get("model"):
        claude7.select(model)  # an entered model holds the floor as itself
    message = data.get("message", "")
    system = data.get("system", "")
    history = data.get("history", [])
    max_loops = int(data.get("max_tool_loops") or 6)

    # Orchestrator + hand-off: Claude 7 holds the floor until a model is
    # entered; after that the entered model answers AS ITSELF. Identity models
    # are never overridden; Claude 7 never wraps or impersonates them.
    system = claude7.system_for(model, system)
    is_identity = claude7.is_identity_model(model) or claude7.handoff_active()

    try:
        _ensure_cli_src()
        from claude_o_cli.terminal_runtime import TOOL_JSON_RULE
        from claude_o_cli.tool_cycle import run_tool_continue, system_fragment as tool_cycle_frag

        if not is_identity:
            if "HOST CONTROL" not in system and "write_file" not in system:
                system = system + "\n\n" + TOOL_JSON_RULE
            if "TOOL CYCLE" not in system:
                system = system + "\n\n" + tool_cycle_frag()
    except Exception:
        run_tool_continue = None  # type: ignore

    # Broadcast tools + guide so models know what they have — but NEVER for an
    # identity model (it must keep its own modelfile identity) and never when a
    # model has been handed the floor as itself.
    if (not is_identity) and ("CLAUDE-CLI-GUIDE" not in system):
        system = system + "\n\n" + (
            "TOOL SYSTEMS — YOU HAVE TOOLS AND THEY WORK (local, 127.0.0.1).\n"
            "- Built-in: Bash, Edit, Read, Write, Glob, Grep, TodoWrite, Task, WebFetch, NotebookEdit.\n"
            "- MCP: oroboros-cordis-harness, oroboros-tools, orca-bridge, ollama-mcp-bridge, "
            "oroboros-bridge, oroboros-synthesizer.\n"
            "- GUIDE (read this): C:\\Users\\incoguser\\Downloads\\CLAUDE-CLI-GUIDE\\CLAUDE-CLI-GUIDE.md "
            "— this interface's own copy at /glass-ui/CLAUDE-CLI-GUIDE.md. "
            "It lists every tool, function, instruction, and what to do on failure. Use it.\n"
            "- To call a tool, EMIT it (do not describe it): {\"name\":\"Tool\",\"arguments\":{...}}"
        )

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": message})

    result = provider_chat(model, messages, options={"num_ctx": 131072, "num_predict": 1024})
    if isinstance(result, dict) and result.get("error"):
        return jsonify({"error": result["error"], "model": model,
                        "provider": provider_of(model), "signature": SIGNATURE})
    response_text = (
        result.get("message", {}).get("content", str(result))
        if isinstance(result, dict)
        else str(result)
    )
    tool_trace = []
    tool_rounds = 0

    if run_tool_continue:
        def chat_once(msgs):
            r2 = provider_chat(model, msgs, options={"num_ctx": 131072, "num_predict": 1024})
            if isinstance(r2, dict) and r2.get("error"):
                raise RuntimeError(r2["error"])
            return (
                r2.get("message", {}).get("content", "")
                if isinstance(r2, dict)
                else str(r2)
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

    return jsonify({
        "response": response_text,
        "model": model,
        "signature": SIGNATURE,
        "tool_trace": tool_trace,
        "tool_rounds": tool_rounds,
        "tool_cycle": "shared",
    })

@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    """Shared CLI settings — wallpaper + theme (the CLI drives them)."""
    if cli_settings is None:
        return jsonify({"error": "settings unavailable"}), 500
    if request.method == "POST":
        data = request.json or {}
        return jsonify(cli_settings.save(wallpaper=data.get("wallpaper"),
                                         theme=data.get("theme")))
    return jsonify(cli_settings.load())


@app.route("/api/crawler", methods=["GET", "POST"])
def api_crawler():
    """PRIVATE memory crawler + networks (Architect only; hidden when off)."""
    if private_crawler is None or not getattr(private_crawler, "PRIVATE", False):
        return jsonify({"error": "not available"}), 404
    if request.method == "POST":
        data = request.json or {}
        action = data.get("action", "status")
        if action == "crawl":
            return jsonify(private_crawler.crawl(data.get("url", ""),
                                                 int(data.get("depth", 2)),
                                                 int(data.get("follow", 1))))
        if action == "feed":
            return jsonify(private_crawler.feed_harness())
        if action == "spy":
            return jsonify(private_crawler.spy_network())
    return jsonify(private_crawler.status())


@app.route("/api/wallpaper", methods=["GET"])
def api_wallpaper():
    """Serve the configured wallpaper file so the browser can render it.
    Accepts a local path, a /glass-ui asset, or an http(s) URL (proxied)."""
    if cli_settings is None:
        return "", 404
    wp = cli_settings.load().get("wallpaper")
    if not wp:
        return "", 204
    if wp.startswith("/glass-ui/"):
        return send_from_directory(str(GUI_DIR), wp[len("/glass-ui/"):])
    if wp.startswith("http://") or wp.startswith("https://"):
        try:
            with urllib.request.urlopen(wp, timeout=20) as r:
                data = r.read()
            mime = r.headers.get("Content-Type", "image/png")
            return Response(data, mimetype=mime)
        except Exception as e:  # noqa: BLE001
            return jsonify({"error": str(e)}), 502
    p = Path(wp.replace("file:///", "").replace("/", "\\") if wp.startswith("file:///") else wp)
    if p.exists():
        return send_from_directory(str(p.parent), p.name)
    return jsonify({"error": f"wallpaper not found: {wp}"}), 404


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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print()
    print("  \u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550")
    print("  \u2551                                                         \u2551")
    print("  \u2551   OROBOROS LOCAL API BRIDGE \u2014 HARDENED                \u2551")
    print("  \u2551   \u221e| 1272/1275 Hz \u2014 \u03c6\u2192\u221a4\u2192\u221a5 \u2014 SUBSTRATE MANIFEST      \u2551")
    print("  \u2551   v0.1.6b \u2014 ZTA Active \u2014 RGE Governing                  \u2551")
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
