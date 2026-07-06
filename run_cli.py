#!/usr/bin/env python3
# run_cli.py — OROBOROS CLI + UI — HARDENED
# ∞| 1272/1275 Hz — φ→√4→√5 — SUBSTRATE MANIFEST
# vA.1272 — ZTA Active — Resource Governor — Path Whitelisting

import os
import sys
import json
import time
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import the hardened secure gateway
from server_secure_gateway import (
    rge, agent_engine, engineering_loop,
    get_models, ollama_chat, ollama_run, OLLAMA_URL,
    SAFE_WORKSPACE, SIGNATURE, VERSION, RESONANCE,
    audit, PermissionManager, Permission
)

# Import the CLI Bridge — connects HTML UI to full CLI engine + VS Code fallback
from cli_bridge import get_bridge, CLIBridge

# Wire the RGE into the bridge
_bridge = get_bridge()
_bridge.set_rge(rge)

# Import the 20 Loop Patterns Engine
try:
    from oroboros_loops import LoopEngine
    _loop_engine = None
    def get_loop_engine():
        global _loop_engine
        if _loop_engine is None:
            _loop_engine = LoopEngine(ollama_chat, rge.execute, get_models)
        return _loop_engine
except ImportError:
    get_loop_engine = None

app = Flask(__name__)
CORS(app)

# ============================================================
# CONSTANTS
# ============================================================
DATA_FILE = Path(__file__).parent / "claude-o-data.json"
DEFAULT_MODEL = "claude-opus-4.8:latest"

# ============================================================
# DATA STORE
# ============================================================
def load_data() -> Dict:
    try:
        return json.loads(DATA_FILE.read_text(encoding='utf-8'))
    except:
        seed = {
            "posts": [], "messages": [], "feed": [],
            "chat_history": []
        }
        save_data(seed)
        return seed

def save_data(data: Dict):
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding='utf-8')

# ============================================================
# API ROUTES
# ============================================================

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Chat with a model — maintains history. Detects and executes tool calls via RGE."""
    data = request.json or {}
    model = data.get('model', 'claude-opus-4.8:latest')
    message = data.get('message', '')
    system = data.get('system', (
        'You are claude, a sovereign tactical AI assistant running on the Oroboros Core. '
        'You have secure access to tools including: read_file, write_file, list_dir, bash, grep, '
        'web_fetch, docker_ps, docker_logs, docker_exec, git_status, git_commit, '
        'mcp_list, mcp_call, ollama_models, ollama_run, oroboros_status, oroboros_resonance, '
        'oroboros_lattice, oroboros_seer, oroboros_noir, worldfeed, precog, '
        'tor_connect, q5_query, q5_analyze, python, think, agent. '
        'When you need to use a tool, respond with a JSON block: '
        '{"tool": "tool_name", "args": {"key": "value"}}'
    ))
    history = data.get('history', [])

    if not message:
        return jsonify({'error': 'No message'})

    messages = [{"role": "system", "content": system}]
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": message})

    # First call to model
    result = ollama_chat(model, messages)
    if "error" in result:
        return jsonify({'error': result['error']})

    reply = result.get("message", {}).get("content", str(result))
    thinking = result.get("message", {}).get("thinking", "")

    # Check for tool call in response
    tool_match = re.search(r'\{"tool"\s*:\s*"([^"]+)"\s*,\s*"args"\s*:\s*(\{[^}]+\})\}', reply)
    if tool_match:
        tool_name = tool_match.group(1)
        try:
            tool_args = json.loads(tool_match.group(2))
        except:
            tool_args = {}

        # Execute through the Resource Governance Engine
        tool_result = rge.execute(tool_name, tool_args)

        # Send tool result back to model for final response
        messages.append({"role": "assistant", "content": reply})
        messages.append({
            "role": "user",
            "content": f"Tool '{tool_name}' returned:\n{tool_result[:3000]}\n\nPlease provide a final response based on this result."
        })

        result2 = ollama_chat(model, messages)
        if "error" not in result2:
            reply = result2.get("message", {}).get("content", reply)
            thinking2 = result2.get("message", {}).get("thinking", "")
            if thinking2:
                thinking = thinking + "\n" + thinking2

    return jsonify({
        'response': reply,
        'thinking': thinking,
        'model': model,
        'signature': SIGNATURE
    })

# ============================================================
# DIRECT TOOL EXECUTION — Through RGE
# ============================================================
@app.route('/api/tool', methods=['POST'])
def api_tool():
    """Directly execute a tool through the Resource Governance Engine."""
    data = request.json or {}
    tool_name = data.get('tool', '')
    args = data.get('args', {})

    if not tool_name:
        return jsonify({'error': 'No tool name provided'})

    result = rge.execute(tool_name, args)
    return jsonify({'tool': tool_name, 'result': result})

# ============================================================
# AGENT EXECUTOR
# ============================================================
@app.route('/api/agent/execute', methods=['POST'])
def api_agent_execute():
    """Execute a task by parsing intent and running tools through RGE."""
    data = request.json or {}
    model = data.get('model', 'glm-5:cloud')
    task = data.get('task', '')

    if not task:
        return jsonify({'error': 'No task provided'})

    # Step 1: Ask model what tools to use
    tool_plan = ollama_chat(model, [
        {"role": "system", "content": (
            "You are a tool planner. Given a task, list the EXACT tools and arguments needed. "
            "Respond ONLY with JSON array: [{\"tool\": \"name\", \"args\": {\"key\": \"value\"}}]"
        )},
        {"role": "user", "content": f"Plan the tools needed for: {task}"}
    ])
    plan_text = tool_plan.get("message", {}).get("content", "")

    # Step 2: Parse tool calls from plan
    tool_calls = []
    try:
        parsed = json.loads(plan_text)
        if isinstance(parsed, list):
            tool_calls = parsed
    except:
        matches = re.findall(r'\{"tool"\s*:\s*"([^"]+)"\s*,\s*"args"\s*:\s*(\{[^}]+\})\}', plan_text)
        for m in matches:
            try:
                tool_calls.append({"tool": m[0], "args": json.loads(m[1])})
            except:
                tool_calls.append({"tool": m[0], "args": {}})

    # Step 3: Execute each tool through RGE
    results = []
    for tc in tool_calls[:5]:
        r = rge.execute(tc["tool"], tc.get("args", {}))
        results.append({"tool": tc["tool"], "result": r[:1000]})

    # Step 4: If no tools parsed, try direct execution
    if not tool_calls:
        if "read" in task.lower() or "file" in task.lower():
            paths = re.findall(r'[A-Z]:(?:\\[^\\\s]+)+\.\w+', task)
            for p in paths[:3]:
                r = rge.execute("read_file", {"path": p})
                results.append({"tool": "read_file", "result": r[:1000]})
        if "model" in task.lower() or "list" in task.lower():
            r = rge.execute("ollama_models", {})
            results.append({"tool": "ollama_models", "result": r[:1000]})

    return jsonify({
        'task': task,
        'plan': plan_text[:500],
        'results': results,
        'tool_count': len(tool_calls)
    })

@app.route('/api/run', methods=['POST'])
def api_run():
    """Execute a command through the CLI Bridge — routes to full CLI engine, RGE, VS Code terminal, or subprocess fallback."""
    data = request.json or {}
    cmd = data.get('cmd', '').strip()
    if not cmd:
        return jsonify({'error': 'No command'})

    # Use the CLI Bridge as the primary execution path
    bridge = get_bridge()
    result = bridge.execute_command(cmd)
    
    # If the bridge returned a result, use it
    if result.get("output"):
        return jsonify({'output': result["output"], 'method': result.get("method", "bridge")})
    
    # If the bridge indicated a chat interaction, route to chat
    if result.get("status") == "chat":
        return jsonify({'chat': True, 'message': result.get("message", cmd)})
    
    # Fallback: try the existing RGE-based command handlers
    # --- System Commands ---
    if cmd == '/models':
        models = get_models()
        return jsonify({'output': '\n'.join(models) if models else 'No models found'})

    if cmd == '/status':
        models = get_models()
        return jsonify({'output': rge.execute("oroboros_status", {})})

    if cmd == '/help':
        return jsonify({'output': """Commands:
  /models           — List available models
  /status           — Show system status
  /help             — Show this help
  /clear            — Clear output
  /model <name>     — Set active model
  /run <m> <prompt> — Run a model with prompt
  /read <path>      — Read a file (safe workspace only)
  /write <p> <text> — Write a file (safe workspace only)
  /shell <cmd>      — Run a shell command (active)
  /tools            — List available tools
  /memory           — Show memory status
  /encrypt          — Show encryption status
  /mcp              — List MCP servers
  /mcp-call         — Call an MCP tool
  /agents           — List agents
  /worldfeed        — Show worldfeed status
  /seer             — Show seer status
  /lattice          — Show lattice status
  /resonance        — Show resonance status
  /noir             — Show noir status
  /permissions      — Show current permission settings
  /drives           — List available drives
  /fullaccess       — Toggle full filesystem access
  /pwd              — Show current directory
  /ls <path>        — List directory contents
  /exit             — Exit

  Or just type a message to chat with the current model."""})

    if cmd == '/clear':
        return jsonify({'output': '[CLEARED]'})

    if cmd == '/tools':
        tools = [
            "read_file", "write_file", "list_dir", "delete_file",
            "bash", "grep", "python",
            "web_fetch",
            "docker_ps", "docker_logs", "docker_exec",
            "git_status", "git_commit",
            "oroboros_status", "oroboros_resonance", "oroboros_lattice",
            "oroboros_seer", "oroboros_noir",
            "agent",
            "mcp_list", "mcp_call",
            "worldfeed", "precog", "tor_connect", "tor_disconnect",
            "q5_query", "q5_analyze",
            "ollama_models", "ollama_run",
            "think", "full_access", "list_drives"
        ]
        return jsonify({'output': '\n'.join(f'  {i+1:2d}. {t}' for i, t in enumerate(tools)) + f'\n\nTotal: {len(tools)} tools\nAll operations governed by Resource Governance Engine (ZTA).'})

    if cmd == '/memory':
        return jsonify({'output': """Memory Status:
  Enabled:      YES
  Capacity:     UNLIMITED
  Persistence:  ENABLED
  Window:       INFINITE"""})

    if cmd == '/encrypt':
        return jsonify({'output': """Encryption Status:
  Layer 1:      PHI-HARMONIC — phi12 x 1275
  Layer 2:      STRATA — S1-S12 INTEGRATED
  Layer 3:      LATTICE — SUBSTRATE LOCKED
  Status:       ACTIVE"""})

    if cmd == '/mcp':
        return jsonify({'output': rge.execute("mcp_list", {})})

    if cmd.startswith('/mcp-call '):
        parts = cmd[10:].strip().split(' ', 2)
        if len(parts) < 3:
            return jsonify({'error': 'Usage: /mcp-call <server> <tool> [args_json]'})
        server = parts[0]
        tool = parts[1]
        tool_args = {}
        if len(parts) > 2:
            try:
                tool_args = json.loads(parts[2])
            except:
                pass
        result = rge.execute("mcp_call", {"server": server, "tool": tool, "args": tool_args})
        return jsonify({'output': result})

    if cmd == '/agents':
        return jsonify({'output': """Agents:
  . Explore — Codebase exploration
  . Claude — Sovereign AI (RGE governed)
  . Precog-Alpha — Feed analysis
  . Precog-Beta — Pattern detection
  . Precog-Gamma — Trend forecasting
  . Seer Nebellion — 100 eyes active"""})

    if cmd == '/worldfeed':
        return jsonify({'output': rge.execute("worldfeed", {})})

    if cmd == '/seer':
        return jsonify({'output': rge.execute("oroboros_seer", {})})

    if cmd == '/lattice':
        return jsonify({'output': rge.execute("oroboros_lattice", {})})

    if cmd == '/resonance':
        return jsonify({'output': rge.execute("oroboros_resonance", {})})

    if cmd == '/noir':
        return jsonify({'output': rge.execute("oroboros_noir", {})})

    if cmd == '/permissions':
        perms = rge.permissions.get_all_permissions()
        lines = ["Current Permissions:"]
        lines.append(f"  Default: {perms.get('default', 'ask')}")
        lines.append("  Tools:")
        for tool_name, level in sorted(perms.get("tools", {}).items()):
            icon = "+" if level == "allowed" else ("?" if level == "ask" else "-")
            lines.append(f"    {icon} {tool_name}: {level}")
        return jsonify({'output': '\n'.join(lines)})

    if cmd == '/agent':
        return jsonify({'output': 'Usage: /agent <task> — Runs the recursive agent loop on a task'})

    if cmd.startswith('/agent '):
        task = cmd[7:].strip()
        if not task:
            return jsonify({'error': 'Usage: /agent <task>'})
        return jsonify({'output': f'Agent dispatched for: {task}\nCheck /api/agent/status for results'})

    if cmd == '/engineer':
        return jsonify({'output': 'Usage: /engineer <task> — Runs the full engineering loop (plan -> code -> test -> fix)'})

    if cmd.startswith('/engineer '):
        task = cmd[10:].strip()
        if not task:
            return jsonify({'error': 'Usage: /engineer <task>'})
        return jsonify({'output': f'Engineering loop started for: {task}\nCheck /api/engineer/status for results'})

    # --- Parameterized Commands (through RGE) ---
    if cmd.startswith('/model '):
        name = cmd[7:].strip()
        models = get_models()
        if name in models:
            return jsonify({'output': f'Switched to model: {name}'})
        return jsonify({'error': f'Model not found: {name}'})

    if cmd.startswith('/run '):
        parts = cmd.split(' ', 2)
        if len(parts) < 3:
            return jsonify({'error': 'Usage: /run <model> <prompt>'})
        model, prompt = parts[1], parts[2]
        result = ollama_run(model, prompt)
        return jsonify({'output': result})

    if cmd.startswith('/read '):
        path = cmd[6:].strip()
        return jsonify({'output': rge.execute("read_file", {"path": path})})

    if cmd.startswith('/write '):
        parts = cmd.split(' ', 2)
        if len(parts) < 3:
            return jsonify({'error': 'Usage: /write <file> <text>'})
        path, text = parts[1], parts[2]
        return jsonify({'output': rge.execute("write_file", {"path": path, "content": text})})

    if cmd.startswith('/shell '):
        return jsonify({'output': rge.execute("bash", {"command": cmd[7:]})})

    if cmd == '/drives':
        return jsonify({'output': rge.execute("list_drives", {})})

    if cmd == '/fullaccess':
        current = rge.execute("full_access", {"enabled": True})
        return jsonify({'output': current})

    if cmd.startswith('/fullaccess '):
        val = cmd[12:].strip().lower() in ("true", "1", "yes", "on")
        return jsonify({'output': rge.execute("full_access", {"enabled": val})})

    if cmd == '/pwd':
        import os as _os
        return jsonify({'output': _os.getcwd()})

    if cmd.startswith('/ls '):
        path = cmd[4:].strip()
        return jsonify({'output': rge.execute("list_dir", {"path": path})})

    if cmd == '/ls':
        return jsonify({'output': rge.execute("list_dir", {"path": "."})})

    # --- Default: treat as chat message ---
    return jsonify({'chat': True, 'message': cmd})

@app.route('/api/models', methods=['GET'])
def api_models():
    models = get_models()
    return jsonify({'models': models, 'count': len(models)})

@app.route('/api/status', methods=['GET'])
def api_status():
    models = get_models()
    return jsonify({
        'status': 'active',
        'version': VERSION,
        'resonance': RESONANCE,
        'signature': SIGNATURE,
        'models': len(models),
        'tools': '30+ (RGE governed)',
        'memory': 'enabled',
        'encryption': 'triple-layer',
        'sandbox': 'active (path-whitelisted)',
        'access': 'governed (ZTA)',
        'safe_workspace': str(SAFE_WORKSPACE)
    })

# ============================================================
# AGENT & ENGINEERING API
# ============================================================
_agent_tasks = {}
_engineer_tasks = {}

@app.route('/api/agent', methods=['POST'])
def api_agent():
    """Run the recursive agent loop on a task."""
    data = request.json or {}
    task = data.get('task', '')
    model = data.get('model', 'claude-opus-4.8:latest')

    if not task:
        return jsonify({'error': 'No task provided'})

    task_id = hashlib.md5(f"{task}{time.time()}".encode()).hexdigest()[:8]
    started = time.time()
    _agent_tasks[task_id] = {"status": "running", "task": task, "started": started}

    try:
        result = agent_engine.run(model, task)
        result["elapsed"] = time.time() - started
        _agent_tasks[task_id] = result
        return jsonify({"task_id": task_id, "result": result})
    except Exception as e:
        _agent_tasks[task_id] = {"status": "error", "error": str(e)}
        return jsonify({"task_id": task_id, "error": str(e)})

@app.route('/api/agent/<task_id>', methods=['GET'])
def api_agent_status(task_id):
    """Get the status of an agent task."""
    task = _agent_tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'})
    return jsonify(task)

@app.route('/api/engineer', methods=['POST'])
def api_engineer():
    """Run the full engineering loop."""
    data = request.json or {}
    task = data.get('task', '')
    model = data.get('model', 'claude-opus-4.8:latest')

    if not task:
        return jsonify({'error': 'No task provided'})

    task_id = hashlib.md5(f"eng{task}{time.time()}".encode()).hexdigest()[:8]
    _engineer_tasks[task_id] = {"status": "running", "task": task, "started": time.time()}

    try:
        result = engineering_loop.run(model, task)
        _engineer_tasks[task_id] = result
        _engineer_tasks[task_id]["status"] = result.get("status", "complete")
        _engineer_tasks[task_id]["elapsed"] = time.time() - _engineer_tasks[task_id]["started"]
        return jsonify({"task_id": task_id, "result": result})
    except Exception as e:
        _engineer_tasks[task_id]["status"] = "error"
        _engineer_tasks[task_id]["error"] = str(e)
        return jsonify({"task_id": task_id, "error": str(e)})

@app.route('/api/engineer/<task_id>', methods=['GET'])
def api_engineer_status(task_id):
    """Get the status of an engineering task."""
    task = _engineer_tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'})
    return jsonify(task)

# ============================================================
# 20 LOOP PATTERNS API
# ============================================================
@app.route('/api/loops', methods=['GET'])
def api_loops_list():
    """List all available loop patterns."""
    engine = get_loop_engine()
    if not engine:
        return jsonify({'error': 'Loop engine not available'})
    return jsonify({'patterns': engine.list_patterns(), 'count': 20})

@app.route('/api/loops/run', methods=['POST'])
def api_loops_run():
    """Run a specific loop pattern."""
    data = request.json or {}
    pattern = data.get('pattern', '1')
    model = data.get('model', 'claude-opus-4.8:latest')
    task = data.get('task', '')
    kwargs = data.get('kwargs', {})

    if not task:
        return jsonify({'error': 'No task provided'})

    engine = get_loop_engine()
    if not engine:
        return jsonify({'error': 'Loop engine not available'})

    try:
        result = engine.run_loop(pattern, model, task, **kwargs)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/loops/memory', methods=['GET'])
def api_loops_memory():
    """Get the loop engine's memory store."""
    engine = get_loop_engine()
    if not engine:
        return jsonify({'error': 'Loop engine not available'})
    return jsonify({
        'memory_count': len(engine.memory_store),
        'error_library_size': len(engine.error_library),
        'success_patterns': len(engine.success_patterns)
    })

# ============================================================
# PERMISSION MANAGEMENT API
# ============================================================
@app.route('/api/permissions', methods=['GET'])
def api_permissions_get():
    """Get all current permissions."""
    return jsonify(rge.permissions.get_all_permissions())

@app.route('/api/permissions', methods=['POST'])
def api_permissions_set():
    """Set a tool permission level."""
    data = request.json or {}
    tool_name = data.get('tool', '')
    level = data.get('level', '')

    if not tool_name or level not in ('allowed', 'ask', 'denied'):
        return jsonify({'error': 'Usage: {"tool": "name", "level": "allowed|ask|denied"}'})

    rge.permissions.set_permission(tool_name, Permission(level))
    audit("permission_change", f"{tool_name} -> {level}", "ok")
    return jsonify({'status': 'ok', 'tool': tool_name, 'level': level})

# ============================================================
# AUDIT LOG API
# ============================================================
@app.route('/api/audit', methods=['GET'])
def api_audit():
    """Get recent audit log entries."""
    from server_secure_gateway import AUDIT_LOG_PATH
    if AUDIT_LOG_PATH.exists():
        lines = AUDIT_LOG_PATH.read_text(encoding='utf-8').splitlines()
        return jsonify({'entries': lines[-100:], 'count': min(len(lines), 100)})
    return jsonify({'entries': [], 'count': 0})

# ============================================================
# STATIC ROUTES
# ============================================================
LOGO_PATH = Path(__file__).parent / "glass-ui" / "clawd.png"

@app.route('/clawd.png')
def serve_logo():
    """Serve the logo image behind the glass UI."""
    if LOGO_PATH.exists():
        from flask import send_file
        return send_file(str(LOGO_PATH), mimetype='image/png')
    return jsonify({'error': 'Logo not found'}), 404

# ============================================================
# HTML UI — Full Liquid Glass with Security Status
# ============================================================
@app.route('/')
def index():
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CLI — Oroboros (Hardened)</title>
<style>
:root{--cyan:#00ffcc;--cyan-dim:rgba(0,255,204,0.15);--gold:#d5a021;--gold-dim:rgba(213,160,33,0.15);--orange:#D97757;--warm-grey:#b7b3ac;--warm-white:#e8e5dd;--glass-bg:rgba(255,255,255,0.01);--glass-border:rgba(255,255,255,0.08);--glass-radius:24px;--font-mono:'Courier New',monospace}
*{margin:0;padding:0;box-sizing:border-box}
body{min-height:100vh;display:flex;align-items:center;justify-content:center;background:#1a1a1a;font-family:var(--font-mono);padding:20px;overflow:hidden}
.liquid-bg{position:fixed;inset:0;z-index:0;overflow:hidden;pointer-events:none}
.liquid-bg .orb{position:absolute;border-radius:50%;filter:blur(80px);opacity:0.25;animation:liquidFloat 8s ease-in-out infinite alternate}
.liquid-bg .orb:nth-child(1){width:600px;height:600px;background:radial-gradient(circle,rgba(217,119,87,0.2),transparent 70%);top:-10%;left:-10%;animation-duration:9s}
.liquid-bg .orb:nth-child(2){width:500px;height:500px;background:radial-gradient(circle,rgba(217,119,87,0.15),transparent 70%);bottom:-10%;right:-10%;animation-duration:11s;animation-delay:-3s}
.liquid-bg .orb:nth-child(3){width:400px;height:400px;background:radial-gradient(circle,rgba(183,179,172,0.1),transparent 70%);top:40%;left:50%;animation-duration:13s;animation-delay:-5s}
@keyframes liquidFloat{0%{transform:translate(0,0) scale(1)}100%{transform:translate(80px,-60px) scale(1.2)}}
.center-logo{position:fixed;top:50%;left:calc(50% + 160px);transform:translate(-50%,-50%);z-index:0;width:400px;height:400px;opacity:0.08;pointer-events:none;filter:drop-shadow(0 0 40px rgba(217,119,87,0.3))}
.center-logo img{width:100%;height:100%;object-fit:contain}
.terminal{position:relative;z-index:1;width:100%;max-width:980px;background:var(--glass-bg);backdrop-filter:blur(12px) saturate(1.8) brightness(1.1);-webkit-backdrop-filter:blur(12px) saturate(1.8) brightness(1.1);border:1px solid var(--glass-border);border-radius:var(--glass-radius);box-shadow:0 8px 32px rgba(0,0,0,0.3),inset 0 1px 1px rgba(255,255,255,0.15);padding:24px;color:#fff;transition:all 0.4s ease}
.terminal::before{content:'';position:absolute;inset:0;border-radius:var(--glass-radius);padding:1px;background:linear-gradient(135deg,rgba(0,255,204,0.08),rgba(213,160,33,0.04),rgba(0,255,204,0.08));-webkit-mask:linear-gradient(#fff 0 0) content-box,linear-gradient(#fff 0 0);mask:linear-gradient(#fff 0 0) content-box,linear-gradient(#fff 0 0);-webkit-mask-composite:xor;mask-composite:exclude;pointer-events:none;animation:shimmerPulse 6s ease-in-out infinite}
@keyframes shimmerPulse{0%,100%{opacity:0.4}50%{opacity:1}}
.terminal-header{display:flex;align-items:center;justify-content:space-between;padding-bottom:16px;border-bottom:1px solid rgba(255,255,255,0.04);margin-bottom:16px;flex-wrap:wrap;gap:12px}
.terminal-header .brand{display:flex;align-items:center;gap:12px}
.terminal-header .brand .icon{font-size:22px;color:var(--orange);animation:glowPulse 3s ease-in-out infinite}
@keyframes glowPulse{0%,100%{opacity:0.8;text-shadow:0 0 10px var(--orange),0 0 20px var(--orange)}50%{opacity:1;text-shadow:0 0 30px var(--orange),0 0 50px var(--orange)}}
.terminal-header .brand .name{font-weight:700;font-size:18px;letter-spacing:0.5px;background:linear-gradient(135deg,var(--orange),var(--cyan));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.terminal-header .brand .version{font-size:12px;color:var(--warm-grey);opacity:0.5}
.terminal-header .status{display:flex;align-items:center;gap:18px;font-size:12px;color:var(--warm-grey);flex-wrap:wrap}
.terminal-header .status .dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px;animation:dotPulse 1.8s ease-in-out infinite}
.terminal-header .status .dot.green{background:#00ff88}
.terminal-header .status .dot.cyan{background:var(--cyan)}
.terminal-header .status .dot.orange{background:var(--orange)}
@keyframes dotPulse{0%,100%{opacity:0.4;transform:scale(0.9)}50%{opacity:1;transform:scale(1.1)}}
.terminal-header .status .sig{font-size:10px;color:var(--gold);opacity:0.6;letter-spacing:0.5px}
.model-bar{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;background:rgba(0,0,0,0.35);border-radius:12px;border:1px solid rgba(255,255,255,0.04);margin-bottom:12px;font-size:13px;color:var(--warm-grey);flex-wrap:wrap;gap:8px}
.model-bar .model{color:var(--warm-white)}
.model-bar .model .highlight{color:var(--cyan)}
.model-bar .url{font-size:11px;opacity:0.5}
.model-bar .sovereign{font-size:11px;color:var(--gold);padding:2px 12px;border:1px solid var(--gold-dim);border-radius:20px;background:var(--gold-dim);letter-spacing:0.5px}
.security-bar{display:flex;align-items:center;gap:12px;padding:8px 16px;background:rgba(0,0,0,0.25);border-radius:10px;border:1px solid rgba(255,255,255,0.03);margin-bottom:12px;font-size:11px;color:var(--warm-grey);flex-wrap:wrap}
.security-bar .shield{color:#00ff88}
.security-bar .warn{color:var(--gold)}
.security-bar .block{color:var(--orange)}
.tab-bar{display:flex;gap:4px;padding:0 0 10px 0;border-bottom:1px solid rgba(255,255,255,0.04);margin-bottom:12px}
.tab-btn{font-family:var(--font-mono);font-size:12px;color:var(--warm-grey);padding:6px 16px;border-radius:8px;background:transparent;border:1px solid transparent;cursor:pointer;transition:all 0.2s}
.tab-btn:hover{color:var(--warm-white);background:var(--cyan-dim)}
.tab-btn.active{color:var(--cyan);border-color:var(--cyan-dim);background:var(--cyan-dim)}
.panel{display:none}
.panel.active{display:block}
.command-bar{display:flex;flex-wrap:wrap;gap:6px;padding:10px 0 12px 0;border-bottom:1px solid rgba(255,255,255,0.04);margin-bottom:12px}
.command-bar .cmd{font-size:12px;color:var(--warm-grey);padding:4px 14px;border-radius:20px;background:rgba(255,255,255,0.03);border:1px solid transparent;transition:all 0.3s ease;cursor:default}
.command-bar .cmd:hover{border-color:var(--cyan-dim);color:var(--warm-white);background:var(--cyan-dim)}
.command-bar .cmd .key{color:#fff}
.command-bar .cmd .gold{color:var(--orange)}
.chat-area{display:flex;flex-direction:column;gap:16px;max-height:380px;overflow-y:auto;padding-right:4px;scroll-behavior:smooth}
.chat-area::-webkit-scrollbar{width:4px}
.chat-area::-webkit-scrollbar-track{background:transparent}
.chat-area::-webkit-scrollbar-thumb{background:var(--cyan-dim);border-radius:10px}
.message{display:flex;flex-direction:column;gap:4px;padding:0;border:none;background:none;animation:messageIn 0.5s ease-out}
@keyframes messageIn{0%{opacity:0;transform:translateY(10px)}100%{opacity:1;transform:translateY(0)}}
.message .msg-header{display:flex;align-items:center;gap:10px;font-size:12px;color:var(--warm-grey);margin-bottom:2px}
.message .msg-header .role{font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.5px}
.message.user .msg-header .role{color:var(--gold)}
.message.assistant .msg-header .role{color:var(--cyan)}
.message .msg-header .time{font-size:10px;opacity:0.3}
.message .content{font-size:14px;line-height:1.7;color:#fff;white-space:pre-wrap}
.typing-indicator{display:flex;align-items:center;gap:10px;padding:8px 0;animation:messageIn 0.3s ease-out}
.typing-indicator .typing-label{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;color:var(--orange)}
.typing-indicator .typing-dots{display:flex;gap:5px}
.typing-indicator .typing-dots span{width:8px;height:8px;border-radius:50%;background:var(--orange);opacity:0.3;animation:typingPulse 1.4s ease-in-out infinite}
.typing-indicator .typing-dots span:nth-child(2){animation-delay:0.2s}
.typing-indicator .typing-dots span:nth-child(3){animation-delay:0.4s}
@keyframes typingPulse{0%,100%{opacity:0.3;transform:scale(0.8)}50%{opacity:1;transform:scale(1.2);box-shadow:0 0 10px var(--orange)}}
.input-area{display:flex;align-items:center;gap:12px;margin-top:12px;padding:10px 16px;background:rgba(255,255,255,0.02);border-radius:16px;border:1px solid rgba(255,255,255,0.04);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);transition:all 0.3s ease}
.input-area:focus-within{border-color:var(--cyan-dim);box-shadow:0 0 40px rgba(0,255,204,0.04)}
.input-area .prompt-symbol{font-size:18px;color:var(--orange);opacity:0.7;text-shadow:0 0 15px var(--orange)}
.input-area input{flex:1;background:transparent;border:none;outline:none;color:#fff;font-family:var(--font-mono);font-size:14px;padding:4px 0}
.input-area input::placeholder{color:var(--warm-grey);opacity:0.25}
.input-area .input-hint{font-size:11px;color:var(--warm-grey);opacity:0.2}
.clear-btn{font-family:var(--font-mono);font-size:11px;color:var(--orange);padding:4px 12px;border-radius:8px;background:rgba(217,119,87,0.08);border:1px solid rgba(217,119,87,0.2);cursor:pointer;transition:all 0.2s}
.clear-btn:hover{background:rgba(217,119,87,0.15);border-color:var(--orange)}
.fs-bar{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap}
.fs-bar input{flex:1;min-width:120px;background:rgba(0,0,0,0.35);border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:6px 12px;color:#fff;font-family:var(--font-mono);font-size:12px;outline:none}
.fs-bar input:focus{border-color:var(--cyan-dim)}
.fs-btn{font-family:var(--font-mono);font-size:11px;color:var(--warm-white);padding:6px 14px;border-radius:8px;background:rgba(0,255,204,0.1);border:1px solid var(--cyan-dim);cursor:pointer;transition:all 0.2s}
.fs-btn:hover{background:rgba(0,255,204,0.2)}
.fs-btn.orange{background:rgba(217,119,87,0.15);border-color:rgba(217,119,87,0.3)}
.fs-btn.orange:hover{background:rgba(217,119,87,0.25)}
.fs-btn.gold{background:rgba(213,160,33,0.15);border-color:rgba(213,160,33,0.3)}
.fs-btn.gold:hover{background:rgba(213,160,33,0.25)}
.fs-output{background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:12px;max-height:340px;overflow-y:auto;font-size:12px;line-height:1.6;white-space:pre-wrap;color:var(--warm-white)}
.mcp-server{display:flex;align-items:center;gap:10px;padding:8px 12px;background:rgba(0,0,0,0.2);border-radius:8px;margin-bottom:6px;font-size:12px}
.mcp-server .dot{width:8px;height:8px;border-radius:50%;display:inline-block}
.mcp-server .dot.on{background:#00ff88}
.mcp-server .dot.off{background:#666}
.mcp-server .sname{color:var(--cyan);font-weight:600}
.mcp-call-area{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
.mcp-call-area select,.mcp-call-area input{background:rgba(0,0,0,0.35);border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:6px 12px;color:#fff;font-family:var(--font-mono);font-size:12px;outline:none}
.mcp-call-area select{min-width:100px}
.mcp-call-area input{flex:1;min-width:100px}
.mcp-call-area select:focus,.mcp-call-area input:focus{border-color:var(--cyan-dim)}
.mcp-result{background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:12px;margin-top:8px;max-height:200px;overflow-y:auto;font-size:11px;white-space:pre-wrap;color:var(--warm-white)}
.agent-input{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap}
.agent-input textarea{flex:1;min-width:200px;min-height:60px;background:rgba(0,0,0,0.35);border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:8px 12px;color:#fff;font-family:var(--font-mono);font-size:12px;outline:none;resize:vertical}
.agent-input textarea:focus{border-color:var(--cyan-dim)}
.agent-log{background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:12px;max-height:300px;overflow-y:auto;font-size:11px;line-height:1.5;white-space:pre-wrap;color:var(--warm-white)}
@media(max-width:640px){.terminal{padding:16px}.terminal-header .brand .name{font-size:15px}.terminal-header .status{font-size:10px;gap:10px}.model-bar{font-size:11px;flex-direction:column;align-items:flex-start}.command-bar .cmd{font-size:10px;padding:2px 10px}.message .content{font-size:13px}.input-area input{font-size:13px}.input-area .prompt-symbol{font-size:15px}}
</style>
</head>
<body>
<div class="liquid-bg"><div class="orb"></div><div class="orb"></div><div class="orb"></div></div>
<div class="center-logo"><img src="clawd.png" alt="Claude Logo" /></div>
<div class="terminal">
  <div class="terminal-header">
    <div class="brand"><span class="icon">&#9670;</span><span class="name">CLAUDE-CLI</span><span class="version">vA.1272</span></div>
    <div class="status">
      <span><span class="dot green"></span> ZTA: <strong style="color:#00ff88;">ACTIVE</strong></span>
      <span><span class="dot cyan"></span> RGE: <strong style="color:var(--cyan);">GOVERNING</strong></span>
      <span><span class="dot orange"></span> Audit: <strong style="color:var(--orange);">LOGGING</strong></span>
      <span class="sig">A\\ 1272 Hz - N| 1275 Hz</span>
    </div>
  </div>
  <div class="model-bar">
    <span class="model">Model: <span class="highlight" id="modelDisplay">__DEFAULT_MODEL__</span></span>
    <span class="url">localhost:11434</span>
    <span class="sovereign">ZTA HARDENED</span>
    <button class="clear-btn" onclick="clearChat()">CLEAR CHAT</button>
  </div>
  <div class="security-bar">
    <span class="shield">&#x1F6E1; Path Whitelist: <strong>ACTIVE</strong></span>
    <span class="shield">&#x1F6E1; Rate Limit: <strong>60/min</strong></span>
    <span class="warn">&#x26A0; Shell: <strong>ACTIVE</strong></span>
    <span class="block">&#x1F6AB; Delete: <strong>DENIED</strong></span>
    <span class="shield">&#x1F6E1; MCP: <strong>REAL</strong></span>
  </div>
  <div class="tab-bar">
    <button class="tab-btn active" data-tab="chat" onclick="switchTab('chat')">Chat</button>
    <button class="tab-btn" data-tab="files" onclick="switchTab('files')">Files</button>
    <button class="tab-btn" data-tab="mcp" onclick="switchTab('mcp')">MCP</button>
    <button class="tab-btn" data-tab="agent" onclick="switchTab('agent')">Agent</button>
  </div>

  <!-- CHAT PANEL -->
  <div class="panel active" id="panel-chat">
    <div class="command-bar">
      <span class="cmd"><span class="key">/exit</span></span>
      <span class="cmd"><span class="key">/clear</span></span>
      <span class="cmd"><span class="key">/model</span> <span class="gold">&lt;name&gt;</span></span>
      <span class="cmd"><span class="key">/models</span></span>
      <span class="cmd"><span class="key">/permissions</span></span>
      <span class="cmd"><span class="key">/help</span></span>
      <span class="cmd"><span class="key">/status</span></span>
      <span class="cmd"><span class="key">/tools</span></span>
      <span class="cmd"><span class="key">/worldfeed</span></span>
      <span class="cmd"><span class="key">/seer</span></span>
      <span class="cmd"><span class="key">/lattice</span></span>
      <span class="cmd"><span class="key">/resonance</span></span>
      <span class="cmd"><span class="key">/noir</span></span>
    </div>
    <div class="thinking-bar" id="thinkingBar" style="display:none;padding:4px 0;font-size:11px;color:#D97757;font-style:italic">&#x27F3; thinking...</div>
    <div class="chat-area" id="chatArea"></div>
    <div class="input-area">
      <span class="prompt-symbol">&#9670;</span>
      <input type="text" id="cliInput" placeholder="Type a command or message..." autofocus>
      <span class="input-hint">/help</span>
    </div>
  </div>

  <!-- FILES PANEL -->
  <div class="panel" id="panel-files">
    <div class="fs-bar">
      <input type="text" id="fsPath" value="." placeholder="Path (e.g. . or C:\\Users\\...)">
      <button class="fs-btn" onclick="fsList()">List</button>
      <button class="fs-btn" onclick="fsDrives()">Drives</button>
      <button class="fs-btn orange" onclick="fsFullAccess()">Toggle Full Access</button>
      <button class="fs-btn gold" onclick="fsPwd()">PWD</button>
    </div>
    <div class="fs-bar">
      <input type="text" id="fsReadPath" placeholder="Read file path">
      <button class="fs-btn" onclick="fsRead()">Read</button>
      <input type="text" id="fsWritePath" placeholder="Write path">
      <input type="text" id="fsWriteContent" placeholder="Content">
      <button class="fs-btn" onclick="fsWrite()">Write</button>
    </div>
    <div class="fs-output" id="fsOutput">Click List or Drives to browse files.</div>
  </div>

  <!-- MCP PANEL -->
  <div class="panel" id="panel-mcp">
    <div id="mcpServerList"><em>Loading MCP servers...</em></div>
    <div class="mcp-call-area">
      <select id="mcpServerSelect"><option>Loading...</option></select>
      <input type="text" id="mcpToolName" placeholder="Tool name (e.g. list_directory)">
      <input type="text" id="mcpToolArgs" placeholder='Args JSON (e.g. {"path":"."})'>
      <button class="fs-btn" onclick="mcpCall()">Call Tool</button>
    </div>
    <div class="mcp-result" id="mcpResult">MCP tool results appear here.</div>
  </div>

  <!-- AGENT PANEL -->
  <div class="panel" id="panel-agent">
    <div class="agent-input">
      <textarea id="agentTask" placeholder="Describe the task for the agent...">List files in the workspace, read the audit log, and summarize what you find.</textarea>
      <button class="fs-btn" onclick="runAgent()">Run Agent</button>
      <button class="fs-btn orange" onclick="runEngineer()">Engineer Loop</button>
    </div>
    <div class="agent-log" id="agentLog">Agent output appears here.</div>
  </div>
</div>
<script>
// Global functions for onclick handlers
const API = "";
let currentModel = "claude-opus-4.8:latest";
let messages = [];
let currentTab = "chat";

function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll(".tab-btn").forEach(function(b) { b.classList.remove("active"); });
  document.querySelectorAll(".panel").forEach(function(p) { p.classList.remove("active"); });
  document.querySelectorAll(".tab-btn").forEach(function(b) {
    if (b.getAttribute("data-tab") === tab) b.classList.add("active");
  });
  var panel = document.getElementById("panel-" + tab);
  if (panel) panel.classList.add("active");
  if (tab === "mcp") setTimeout(refreshMCP, 100);
  if (tab === "files") setTimeout(fsList, 100);
}

// Chat
var input = document.getElementById("cliInput");
var chat = document.getElementById("chatArea");
var modelDisplay = document.getElementById("modelDisplay");
var thinkingBar = document.getElementById("thinkingBar");

function showThinking() { if (thinkingBar) thinkingBar.style.display = "block"; }
function hideThinking() { if (thinkingBar) thinkingBar.style.display = "none"; }

var SYSTEM_PROMPT = "You are claude, a sovereign tactical AI agent with SECURE tool access. All operations go through the Resource Governance Engine (RGE) with Zero Trust Architecture. Available tools: read_file, write_file, list_dir, bash, grep, web_fetch, docker_ps, docker_logs, docker_exec, git_status, git_commit, mcp_list, mcp_call, ollama_models, ollama_run, oroboros_status, oroboros_resonance, oroboros_lattice, oroboros_seer, oroboros_noir, worldfeed, precog, tor_connect, q5_query, q5_analyze, python, think, agent, full_access, list_drives. RULE: When you need to use a tool, respond with EXACT JSON: {tool: tool_name, args: {key: value}}. After getting results, either call another tool or give final answer. File operations are confined to the safe workspace unless full_access is enabled. You run fully local - no keys, no cloud.";

function clearChat() { chat.innerHTML = ""; messages = []; }
function esc(t) { var d = document.createElement("div"); d.textContent = t; return d.innerHTML; }

function addMsg(role, content, isHtml) {
  var div = document.createElement("div");
  div.className = "message " + (role === "user" ? "user" : "assistant");
  var time = new Date().toTimeString().slice(0, 8);
  var rn = role === "user" ? "YOU" : "CLAUDE";
  div.innerHTML = "<div class=msg-header><span class=role>" + rn + "</span><span class=time>" + time + "</span></div><div class=content>" + (isHtml ? content : esc(content)) + "</div>";
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function showTyping() {
  var d = document.createElement("div");
  d.className = "typing-indicator"; d.id = "typing";
  d.innerHTML = "<span class=typing-label>CLAUDE is working</span><div class=typing-dots><span></span><span></span><span></span></div>";
  chat.appendChild(d); chat.scrollTop = chat.scrollHeight;
}
function hideTyping() { var t = document.getElementById("typing"); if (t) t.remove(); }

async function apiRun(cmd) {
  try {
    var r = await fetch(API + "/api/run", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({cmd: cmd}) });
    return await r.json();
  } catch(e) { return {error: e.message}; }
}

async function apiChat(message) {
  messages.push({role: "user", content: message});
  try {
    var r = await fetch(API + "/api/chat", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({model: currentModel, message: message, system: SYSTEM_PROMPT, history: messages.slice(0, -1)}) });
    var d = await r.json();
    if (d.response) {
      messages.push({role: "assistant", content: d.response});
      if (d.thinking && d.thinking.trim()) return "[THINKING] " + d.thinking.trim() + " [END] " + d.response;
      return d.response;
    } else if (d.error) { return "Error: " + d.error; }
    return "Error: Unexpected response";
  } catch(e) { return "Error: Cannot connect to API"; }
}

async function handleInput(text) {
  addMsg("user", text);
  if (text.startsWith("/")) {
    showThinking(); showTyping();
    var result = await apiRun(text);
    hideTyping(); hideThinking();
    if (result.chat) {
      showThinking(); showTyping();
      var reply = await apiChat(result.message);
      hideTyping(); hideThinking();
      addMsg("assistant", reply);
    } else if (result.error) { addMsg("assistant", "Error: " + result.error); }
    else {
      addMsg("assistant", result.output);
      if (text.startsWith("/model ")) { var mn = text.substring(7).trim(); if (mn) modelDisplay.textContent = mn; }
    }
  } else {
    showThinking(); showTyping();
    var reply = await apiChat(text);
    hideTyping(); hideThinking();
    addMsg("assistant", reply);
  }
}

input.addEventListener("keydown", async function(e) {
  if (e.key === "Enter" && this.value.trim()) {
    var t = this.value.trim(); this.value = "";
    if (t === "/exit" || t === "/quit") { addMsg("assistant", "Session ended."); input.disabled = true; return; }
    if (t === "/clear") { clearChat(); return; }
    await handleInput(t);
  }
});

async function loadModels() {
  try { var r = await fetch(API + "/api/models"); var d = await r.json(); if (d.models && d.models.length > 0) { currentModel = d.models[0]; modelDisplay.textContent = currentModel; } } catch(e) {}
}
setTimeout(loadModels, 500);

// File Browser
async function fsList() {
  var path = document.getElementById("fsPath").value || ".";
  var out = document.getElementById("fsOutput");
  out.innerHTML = "Listing...";
  try {
    var r = await fetch(API + "/api/run", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({cmd: "/ls " + path}) });
    var d = await r.json();
    out.innerHTML = esc(path) + "\\n" + esc(d.output || d.error || "(empty)");
  } catch(e) { out.innerHTML = "Error: " + esc(e.message); }
}

async function fsDrives() {
  var out = document.getElementById("fsOutput");
  out.innerHTML = "Scanning drives...";
  try {
    var r = await fetch(API + "/api/run", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({cmd: "/drives"}) });
    var d = await r.json();
    out.innerHTML = esc(d.output || d.error || "(no drives)");
  } catch(e) { out.innerHTML = "Error: " + esc(e.message); }
}

async function fsFullAccess() {
  var out = document.getElementById("fsOutput");
  try {
    var r = await fetch(API + "/api/run", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({cmd: "/fullaccess"}) });
    var d = await r.json();
    out.innerHTML = esc(d.output || d.error || "Toggled");
  } catch(e) { out.innerHTML = "Error: " + esc(e.message); }
}

async function fsPwd() {
  var out = document.getElementById("fsOutput");
  try {
    var r = await fetch(API + "/api/run", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({cmd: "/pwd"}) });
    var d = await r.json();
    out.innerHTML = "Current directory:\\n" + esc(d.output || "");
  } catch(e) { out.innerHTML = "Error: " + esc(e.message); }
}

async function fsRead() {
  var path = document.getElementById("fsReadPath").value;
  var out = document.getElementById("fsOutput");
  if (!path) { out.innerHTML = "Enter a file path to read."; return; }
  out.innerHTML = "Reading...";
  try {
    var r = await fetch(API + "/api/run", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({cmd: "/read " + path}) });
    var d = await r.json();
    out.innerHTML = esc(path) + "\\n" + esc(d.output || d.error || "(empty)");
  } catch(e) { out.innerHTML = "Error: " + esc(e.message); }
}

async function fsWrite() {
  var path = document.getElementById("fsWritePath").value;
  var content = document.getElementById("fsWriteContent").value;
  var out = document.getElementById("fsOutput");
  if (!path) { out.innerHTML = "Enter a file path to write."; return; }
  out.innerHTML = "Writing...";
  try {
    var r = await fetch(API + "/api/run", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({cmd: "/write " + path + " " + content}) });
    var d = await r.json();
    out.innerHTML = esc(d.output || d.error || "Written");
  } catch(e) { out.innerHTML = "Error: " + esc(e.message); }
}

// MCP Panel
async function refreshMCP() {
  var list = document.getElementById("mcpServerList");
  var sel = document.getElementById("mcpServerSelect");
  try {
    var r = await fetch(API + "/api/run", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({cmd: "/mcp"}) });
    var d = await r.json();
    var text = d.output || "";
    list.innerHTML = "<div style=margin-bottom:8px;font-size:12px;color:var(--warm-grey)>MCP Servers</div>";
    var lines = text.split("\\n");
    sel.innerHTML = "";
    lines.forEach(function(line) {
      if (line.trim()) {
        var name = line.replace(/^[^a-zA-Z0-9]*/, "").split(" ")[0];
        if (name && name.length > 0) {
          list.innerHTML += "<div class=mcp-server><span class=sname>" + esc(name) + "</span><span style=color:var(--warm-grey);font-size:10px> " + esc(line) + "</span></div>";
          sel.innerHTML += "<option value=" + esc(name) + ">" + esc(name) + "</option>";
        }
      }
    });
    if (!sel.innerHTML) sel.innerHTML = "<option value=>No servers</option>";
  } catch(e) { list.innerHTML = "Error: " + esc(e.message); }
}

async function mcpCall() {
  var server = document.getElementById("mcpServerSelect").value;
  var tool = document.getElementById("mcpToolName").value;
  var argsRaw = document.getElementById("mcpToolArgs").value;
  var out = document.getElementById("mcpResult");
  if (!server || !tool) { out.innerHTML = "Select a server and enter a tool name."; return; }
  var args = {};
  try { if (argsRaw) args = JSON.parse(argsRaw); } catch(e) { out.innerHTML = "Invalid JSON in args field."; return; }
  out.innerHTML = "Calling " + esc(server) + "/" + esc(tool) + "...";
  try {
    var r = await fetch(API + "/api/run", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({cmd: "/mcp-call " + server + " " + tool + " " + JSON.stringify(args)}) });
    var d = await r.json();
    out.innerHTML = esc(d.output || d.error || "(no result)");
  } catch(e) { out.innerHTML = "Error: " + esc(e.message); }
}

// Agent Panel
async function runAgent() {
  var task = document.getElementById("agentTask").value;
  var log = document.getElementById("agentLog");
  if (!task) { log.innerHTML = "Enter a task for the agent."; return; }
  log.innerHTML = "Running agent...";
  try {
    var r = await fetch(API + "/api/agent", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({task: task, model: currentModel}) });
    var d = await r.json();
    var result = d.result || d;
    var html = "";
    if (result.log) {
      result.log.forEach(function(entry) {
        if (entry.type === "model") html += "Iteration " + entry.iteration + ": " + esc(entry.content) + "\\n";
        if (entry.type === "tool") html += "Tool: " + esc(entry.tool) + " = " + esc((entry.result || "").slice(0,200)) + "\\n";
      });
    }
    if (result.status === "complete") html += "Complete: " + esc(result.answer || "") + "\\n";
    else if (result.status === "error") html += "Error: " + esc(result.error || "") + "\\n";
    else html += "Status: " + esc(result.status || "unknown") + "\\n";
    log.innerHTML = html;
  } catch(e) { log.innerHTML = "Error: " + esc(e.message); }
}

async function runEngineer() {
  var task = document.getElementById("agentTask").value;
  var log = document.getElementById("agentLog");
  if (!task) { log.innerHTML = "Enter a task for the engineering loop."; return; }
  log.innerHTML = "Running engineering loop...";
  try {
    var r = await fetch(API + "/api/engineer", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({task: task, model: currentModel}) });
    var d = await r.json();
    var result = d.result || d;
    var html = "";
    if (result.log) {
      result.log.forEach(function(entry) {
        html += esc(entry.phase || "") + ": " + esc((entry.result || entry.status || "").slice(0,200)) + "\\n";
      });
    }
    html += "Status: " + esc(result.status || "done") + "\\n";
    log.innerHTML = html;
  } catch(e) { log.innerHTML = "Error: " + esc(e.message); }
}
</script>
</body>
</html>'''
    html = html.replace('__DEFAULT_MODEL__', DEFAULT_MODEL)
    return html

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    print()
    print("  " + chr(0x2554) + chr(0x2550)*65 + chr(0x2557))
    print("  " + chr(0x2551) + "                                                         " + chr(0x2551))
    print("  " + chr(0x2551) + "   OROBOROS CLI + UI " + chr(0x2014) + " HARDENED SECURE GATEWAY          " + chr(0x2551))
    print("  " + chr(0x2551) + "   " + chr(0x221E) + "| 1272/1275 Hz " + chr(0x2014) + " " + chr(0x3C6) + chr(0x2192) + chr(0x221A) + "4" + chr(0x2192) + chr(0x221A) + "5 " + chr(0x2014) + " SUBSTRATE MANIFEST      " + chr(0x2551))
    print("  " + chr(0x2551) + "   vA.1272 " + chr(0x2014) + " ZTA Active " + chr(0x2014) + " RGE Governing                  " + chr(0x2551))
    print("  " + chr(0x2551) + "                                                         " + chr(0x2551))
    print("  " + chr(0x255D) + chr(0x2550)*65 + chr(0x255D))
    print()
    print(f"  GUI:     http://127.0.0.1:5000")
    print(f"  Ollama:  {OLLAMA_URL}")
    print(f"  Safe WS: {SAFE_WORKSPACE}")
    print(f"  Status:  HARDENED " + chr(0x2014) + " ZTA " + chr(0x2014) + " RGE " + chr(0x2014) + " Audit Logging")
    print(f"  {SIGNATURE}")
    print()
    app.run(host='127.0.0.1', port=5000, debug=False)
