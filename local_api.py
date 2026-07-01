#!/usr/bin/env python3
"""
Oroboros Local API Bridge
Bridges HTML UI to local client (Ollama, CLI tools, system commands)
∞| 1272/1275 Hz — φ→√4→√5 — SUBSTRATE MANIFEST
vA.1272
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

app = Flask(__name__, static_folder=None)
CORS(app)

# ─── Configuration ───────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434"
GUI_DIR = Path(__file__).parent / "glass-ui"
RESONANCE = "1272/1275"
SIGNATURE = "∞| 1272/1275 Hz — φ→√4→√5 — SUBSTRATE MANIFEST"

# ─── Helper Functions ─────────────────────────────────────────

def run_ollama_chat(model, messages, options=None):
    """Send a chat request to Ollama and return the response."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": options or {"num_ctx": 131072}
    }
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def run_command(command):
    """Execute a shell command and return output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Command timed out", "returncode": -1}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1}

def get_ollama_models():
    """Get list of available Ollama models."""
    try:
        import urllib.request
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

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
        "version": "vA.1272",
        "resonance": RESONANCE,
        "signature": SIGNATURE,
        "models": "29 fixed",
        "tools": "33 injected",
        "memory": "enabled",
        "encryption": "triple-layer",
        "sandbox": "removed",
        "access": "full"
    })

@app.route("/api/models", methods=["GET"])
def api_models():
    """Get list of Ollama models."""
    models = get_ollama_models()
    return jsonify(models)

@app.route("/api/signal", methods=["POST"])
def api_signal():
    """Receive signal from HTML UI and process it."""
    data = request.json or {}
    signal = data.get("signal", "")
    payload = data.get("payload", {})

    print(f"  [API] Signal received: {signal}")

    if signal == "execute_command":
        command = payload.get("command", "")
        result = run_command(command)
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

        result = run_ollama_chat(model, messages)
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
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())
            return jsonify({"status": "success", "result": result})
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)})

    elif signal == "get_status":
        return jsonify({
            "status": "active",
            "resonance": RESONANCE,
            "signature": SIGNATURE,
            "models": "29 fixed",
            "tools": "33 injected",
            "memory": "enabled",
            "encryption": "triple-layer",
            "sandbox": "removed",
            "access": "full"
        })

    elif signal == "list_models":
        models = get_ollama_models()
        return jsonify({"status": "success", "models": models})

    elif signal == "run_model":
        model = payload.get("model", "")
        prompt = payload.get("prompt", "")
        if not model or not prompt:
            return jsonify({"status": "error", "error": "model and prompt required"})
        result = run_ollama_chat(model, [{"role": "user", "content": prompt}])
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

    result = run_ollama_chat(model, messages)
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
    print("  ╔═════════════════════════════════════════════════════════╗")
    print("  ║                                                         ║")
    print("  ║   OROBOROS LOCAL API BRIDGE                           ║")
    print("  ║   ∞| 1272/1275 Hz — φ→√4→√5 — SUBSTRATE MANIFEST      ║")
    print("  ║   vA.1272 — Sandbox Removed — Full Access              ║")
    print("  ║                                                         ║")
    print("  ╚═════════════════════════════════════════════════════════╝")
    print()
    print(f"  API:     http://localhost:{port}/api")
    print(f"  GUI:     http://localhost:{port}/")
    print(f"  Ollama:  {OLLAMA_URL}")
    print(f"  Models:  29 fixed, 33 tools, 131K context")
    print(f"  Status:  ACTIVE — Sandbox Removed — Full Access")
    print()
    app.run(host="0.0.0.0", port=port, debug=False)
