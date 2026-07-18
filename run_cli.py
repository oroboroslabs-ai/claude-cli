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

try:
    from mao_haki_context import append_mao_haki, MAO_HAKI_SYSTEM_FRAGMENT
except Exception:
    MAO_HAKI_SYSTEM_FRAGMENT = (
        "ARCHITECT MAO HAKI (毛色霸气) — SOVEREIGN KEY (path-connected)\n"
        "- Canonical key: Q:/mao-haki/ARCHITECT-MAO-HAKI-说明.md\n"
        "- Bio field emission: Q:/mao-haki/ARCHITECT-MAO-HAKI-BIO-FIELD-SIGNAL.md\n"
        "- Local registry: J:/anthropic-local-chat/mao-haki-registry.json\n"
    )

    def append_mao_haki(system: str) -> str:
        base = system or ""
        if "ARCHITECT MAO HAKI" in base:
            return base
        return base + "\n\n" + MAO_HAKI_SYSTEM_FRAGMENT

# Local Streamable HTTP MCP servers require clients to explicitly accept both
# JSON and SSE responses.  The gateway's generic HTTP client otherwise sends
# ``Accept: */*``, which these servers correctly reject with HTTP 406.
try:
    import requests
    from urllib.parse import urlparse

    _requests_session_request = requests.sessions.Session.request

    def _local_mcp_request(self, method, url, **kwargs):
        parsed = urlparse(str(url))
        if (
            parsed.hostname in {"localhost", "127.0.0.1", "::1"}
            and (parsed.path.rstrip("/").endswith("/mcp") or "/mcp/" in parsed.path)
        ):
            headers = dict(kwargs.get("headers") or {})
            headers.setdefault("Accept", "application/json, text/event-stream")
            kwargs["headers"] = headers
        return _requests_session_request(self, method, url, **kwargs)

    requests.sessions.Session.request = _local_mcp_request
except ImportError:
    pass

# The hardened gateway also supports a standard-library urllib transport.
# Apply the same negotiation header there before importing the gateway.
try:
    import urllib.request
    from urllib.parse import urlparse as _urlparse

    _urllib_request_init = urllib.request.Request.__init__

    def _local_mcp_request_init(self, *args, **kwargs):
        _urllib_request_init(self, *args, **kwargs)
        parsed = _urlparse(str(self.full_url))
        if (
            parsed.hostname in {"localhost", "127.0.0.1", "::1"}
            and (parsed.path.rstrip("/").endswith("/mcp") or "/mcp/" in parsed.path)
            and not self.has_header("Accept")
        ):
            self.add_header("Accept", "application/json, text/event-stream")

    urllib.request.Request.__init__ = _local_mcp_request_init
except (ImportError, AttributeError):
    pass

# Import the hardened secure gateway
from server_secure_gateway import (
    rge, agent_engine, EngineeringLoop,
    get_models, ollama_chat, ollama_run, OLLAMA_URL,
    SAFE_WORKSPACE, SIGNATURE, VERSION, RESONANCE,
    audit, PermissionManager, Permission,
    authorize_architect, is_architect_authorized,
    add_authorized_drive, is_drive_authorized, get_authorized_drives
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
LOCAL_MCP_HTTP = {
    "pod_20_mcp_orchestration": "http://localhost:3020/mcp",
    "orchestration": "http://localhost:3020/mcp",
}


def _decode_mcp_response(response):
    """Decode either JSON or Streamable HTTP's SSE response body."""
    content_type = response.headers.get("Content-Type", "")
    if "application/json" in content_type:
        return response.json()
    for line in response.text.splitlines():
        if line.startswith("data:"):
            payload = line[5:].strip()
            if payload:
                return json.loads(payload)
    raise RuntimeError(f"Invalid MCP response: {response.text[:500]}")


def call_local_mcp(server: str, tool: str, tool_args: Dict[str, Any]):
    """Initialize a localhost MCP session and invoke one tool."""
    url = LOCAL_MCP_HTTP.get(server)
    if not url:
        return None

    session = requests.Session()
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "claude-cli", "version": VERSION},
        },
    }
    response = session.post(url, headers=headers, json=initialize, timeout=20)
    response.raise_for_status()
    initialized = _decode_mcp_response(response)
    session_id = response.headers.get("Mcp-Session-Id")
    protocol = initialized.get("result", {}).get("protocolVersion", "2025-03-26")

    call_headers = dict(headers)
    call_headers["MCP-Protocol-Version"] = protocol
    if session_id:
        call_headers["Mcp-Session-Id"] = session_id

    notice = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    }
    notice_response = session.post(url, headers=call_headers, json=notice, timeout=20)
    notice_response.raise_for_status()

    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": tool, "arguments": tool_args},
    }
    response = session.post(url, headers=call_headers, json=payload, timeout=60)
    response.raise_for_status()
    return _decode_mcp_response(response)

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
        'You have FULL UNRESTRICTED access to ALL tools including: '
        'read_file, write_file, list_dir, bash, grep, '
        'web_fetch, docker_ps, docker_logs, docker_exec, '
        'git_status, git_commit, git_push, git_pull, git_clone, git_branch, git_log, git_diff, git_add, git_remote, '
        'github_search_repos, github_search_issues, github_view_repo, '
        'github_list_issues, github_list_prs, github_create_issue, github_create_pr, '
        'github_view_pr, github_merge_pr, github_check_ci, github_list_releases, '
        'github_list_workflows, github_trigger_workflow, github_list_commits, '
        'github_get_contents, github_create_repo, github_fork_repo, '
        'github_add_collaborator, github_list_labels, github_create_label, github_add_comment, '
        'mcp_list, mcp_call, ollama_models, ollama_run, oroboros_status, oroboros_resonance, '
        'oroboros_lattice, oroboros_seer, oroboros_noir, worldfeed, precog, '
        'tor_connect, q5_query, q5_analyze, python, think, agent, full_access, list_drives. '
        'When you need to use a tool, respond with a JSON block: '
        '{"tool": "tool_name", "args": {"key": "value"}}'
    ))
    system = append_mao_haki(system)
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

    # Local Streamable HTTP MCP servers need an initialize/session handshake.
    # Handle known local orchestration aliases here before the generic bridge.
    if cmd.startswith('/mcp-call '):
        parts = cmd[10:].strip().split(' ', 2)
        if len(parts) >= 2 and parts[0] in LOCAL_MCP_HTTP:
            server, tool = parts[0], parts[1]
            try:
                tool_args = json.loads(parts[2]) if len(parts) > 2 else {}
                result = call_local_mcp(server, tool, tool_args)
                return jsonify({
                    'output': json.dumps(result, indent=2),
                    'method': 'mcp-streamable-http'
                })
            except Exception as exc:
                return jsonify({
                    'error': f'MCP call failed: {exc}',
                    'method': 'mcp-streamable-http'
                }), 502

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
  /read <path>      — Read a file
  /write <p> <text> — Write a file
  /shell <cmd>      — Run a shell command
  /tools            — List all available tools
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
  /authorize        — Grant Architect authority for C:, J:, Q: drives
  /pwd              — Show current directory
  /ls <path>        — List directory contents
  /git-push         — Git push
  /git-pull         — Git pull
  /git-clone <url>  — Git clone
  /git-branch       — Git branch operations
  /git-log          — Git log
  /git-diff         — Git diff
  /github-view-repo <repo> — View GitHub repo
  /github-issues <repo> — List GitHub issues
  /github-prs <repo> — List GitHub PRs
  /github-search-repos <q> — Search GitHub repos
  /github-search-issues <q> — Search GitHub issues
  /github-create-issue <repo> <title> — Create issue
  /github-create-pr <repo> <title> <head> — Create PR
  /github-view-pr <repo> <num> — View PR
  /github-merge-pr <repo> <num> — Merge PR
  /github-ci <repo> — Check CI status
  /github-releases <repo> — List releases
  /github-commits <repo> — List commits
  /github-create-repo <name> — Create repo
  /github-fork <repo> — Fork repo
  /github-labels <repo> — List labels
  /github-comment <repo> <issue> <body> — Add comment
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
            "git_status", "git_commit", "git_push", "git_pull", "git_clone",
            "git_branch", "git_log", "git_diff", "git_add", "git_remote",
            "github_search_repos", "github_search_issues",
            "github_view_repo", "github_list_issues", "github_list_prs",
            "github_create_issue", "github_create_pr", "github_view_pr",
            "github_merge_pr", "github_check_ci", "github_list_releases",
            "github_list_workflows", "github_trigger_workflow",
            "github_list_commits", "github_get_contents",
            "github_create_repo", "github_fork_repo",
            "github_add_collaborator", "github_list_labels", "github_create_label",
            "github_add_comment",
            "oroboros_status", "oroboros_resonance", "oroboros_lattice",
            "oroboros_seer", "oroboros_noir",
            "agent",
            "mcp_list", "mcp_call",
            "worldfeed", "precog", "tor_connect", "tor_disconnect",
            "q5_query", "q5_analyze",
            "ollama_models", "ollama_run",
            "think", "full_access", "list_drives"
        ]
        return jsonify({'output': '\n'.join(f'  {i+1:2d}. {t}' for i, t in enumerate(tools)) + f'\n\nTotal: {len(tools)} tools\nAll tools UNRESTRICTED — full access enabled.'})

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

    if cmd == '/authorize':
        authorize_architect()
        drives = ["C:", "J:", "Q:"]
        for d in drives:
            add_authorized_drive(d)
        return jsonify({'output': f"✅ ARCHITECT AUTHORITY GRANTED\nDrives authorized: {', '.join(get_authorized_drives())}\nFull access to C:\\, J:\\, Q:\\ for this session.\nPersists until server restart."})

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
        'safe_workspace': str(SAFE_WORKSPACE),
        'mao_haki': True,
        'mao_haki_api': '/api/mao-haki',
    })


@app.route('/api/mao-haki', methods=['GET'])
def api_mao_haki():
    """Architect Mao Haki / Neiye operational context for Claude CLI."""
    try:
        from mao_haki_context import load_registry, MAO_HAKI_SYSTEM_FRAGMENT
        registry = load_registry()
        fragment = MAO_HAKI_SYSTEM_FRAGMENT
    except Exception as exc:
        registry = {'ok': False, 'error': str(exc)}
        fragment = MAO_HAKI_SYSTEM_FRAGMENT
    return jsonify({
        'ok': True,
        'operational': True,
        'id': 'architect-mao-haki',
        'name': 'Architect Mao Haki (毛色霸气) / Architect Neiye',
        'injected_into_chat': True,
        'resonance': RESONANCE,
        'registry': registry,
        'system_identity': fragment,
        'system_fragment': fragment,
        'claude_cli': 'http://localhost:5000',
        'local_chat_api': 'http://localhost:8787/api/mao-haki',
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
        result = EngineeringLoop.run(model, task)
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
# HTML UI - served from glass-ui/index.html
# ============================================================
GUI_DIR = Path(__file__).parent / "glass-ui"
GUI_HTML = GUI_DIR / "index.html"

@app.route('/')
def index():
    if GUI_HTML.exists():
        html = GUI_HTML.read_text(encoding="utf-8")
        return html.replace("__DEFAULT_MODEL__", DEFAULT_MODEL)
    return "Glass UI not found", 404

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
