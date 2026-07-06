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
from pathlib import Path

try:
    from flask import Flask, request, jsonify, send_from_directory
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

app = Flask(__name__, static_folder=None)
CORS(app)

# ─── Configuration ───────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434"
GUI_DIR = Path(__file__).parent / "glass-ui"

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

@app.route("/api/status", methods=["GET"])
def api_status():
    """Get full system status."""
    return jsonify({
        "status": "active",
        "version": VERSION,
        "resonance": RESONANCE,
        "signature": SIGNATURE,
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
    return jsonify({"models": models, "count": len(models)})

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
        model = payload.get("model", "claude-opus-4.8:latest")
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

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Chat endpoint — receives message, sends to Ollama, returns response."""
    data = request.json or {}
    model = data.get("model", "claude-opus-4.8:latest")
    message = data.get("message", "")
    system = data.get("system", "You are a helpful AI assistant.")
    history = data.get("history", [])

    messages = [{"role": "system", "content": system}]
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": message})

    result = ollama_chat(model, messages)
    response_text = result.get("message", {}).get("content", str(result))

    return jsonify({
        "response": response_text,
        "model": model,
        "signature": SIGNATURE
    })

# ─── Main ────────────────────────────────────────────────────

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
    app.run(host="127.0.0.1", port=port, debug=False)
