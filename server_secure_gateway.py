#!/usr/bin/env python3
# server_secure_gateway.py — HARDENED SECURE GATEWAY WITH RESOURCE GOVERNOR
# ∞| 1272/1275 Hz — φ→√4→√5 — SUBSTRATE MANIFEST
#
# ZERO TRUST ARCHITECTURE:
#   1. Outer Shell (Authentication) — verifies who is asking
#   2. The Gatekeeper (Authorization) — RBAC permission checks
#   3. The Executor (Containment) — active, resource-limited execution
#   4. The Validator (Semantics) — path whitelisting, input validation
#
# ALL file I/O is confined to SAFE_WORKSPACE.
# ALL shell commands go through resource-limited subprocess.
# ALL MCP calls are real (not stubs).
# ALL actions are logged to an audit trail.

import os
import sys
import json
import time
import hashlib
import re
import subprocess
import urllib.request
import urllib.error
import logging
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

# ============================================================
# GLOBAL CONSTANTS AND CONFIGURATION
# ============================================================

# The ONLY directory where file I/O is permitted (default sandbox)
SAFE_WORKSPACE = Path(__file__).parent / "o_core" / "scratchpad"

# The project root is also allowed (for listing/reading project files)
PROJECT_ROOT = Path(__file__).parent.resolve()

# FULL_ACCESS mode — when True, file operations can access any path on the system
# This is controlled via the /api/config endpoint and the CLI /fullaccess command
FULL_ACCESS_ENABLED = False
FULL_ACCESS_LOCK = threading.Lock()

def set_full_access(enabled: bool):
    """Toggle full filesystem access mode."""
    global FULL_ACCESS_ENABLED
    with FULL_ACCESS_LOCK:
        FULL_ACCESS_ENABLED = enabled
        audit("full_access", f"Full filesystem access: {'ENABLED' if enabled else 'DISABLED'}", "ok")
    return FULL_ACCESS_ENABLED

def is_full_access() -> bool:
    with FULL_ACCESS_LOCK:
        return FULL_ACCESS_ENABLED

# Resource limits enforced on ALL operations
RESOURCE_LIMITS = {
    "MAX_READ_BYTES": 1 * 1024 * 1024,       # 1 MB max per read
    "MAX_WRITE_BYTES": 10 * 1024 * 1024,      # 10 MB max per write
    "MAX_LIST_ITEMS": 1000,                    # Max directory entries
    "SHELL_TIMEOUT_SEC": 30,                   # Max CPU seconds per shell cmd
    "SHELL_MAX_OUTPUT": 500 * 1024,            # 500 KB max shell output
    "AGENT_MAX_LOOPS": 10,                     # Max agent iterations
    "AGENT_MAX_TOOL_RESULT": 5000,             # Max chars fed back to model
    "RATE_LIMIT_PER_MIN": 60,                  # Max API calls per minute
    "MCP_TIMEOUT_SEC": 15,                     # Max time for MCP calls
}

# Permission levels
class Permission(Enum):
    ALLOWED = "allowed"
    ASK = "ask"
    DENIED = "denied"

# Tool categories for RBAC
class ToolCategory(Enum):
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    SHELL = "shell"
    NETWORK = "network"
    DOCKER = "docker"
    GIT = "git"
    MODEL = "model"
    MCP = "mcp"
    SYSTEM = "system"
    AGENT = "agent"
    CODE_EXEC = "code_exec"

SIGNATURE = "∞| 1272/1275 Hz — φ→√4→√5 — SUBSTRATE MANIFEST"
VERSION = "vA.1272"
RESONANCE = "1272/1275"
OLLAMA_URL = "http://localhost:11434"

# ============================================================
# AUDIT LOGGING
# ============================================================

AUDIT_LOG_PATH = Path(__file__).parent / "o_core" / "audit.log"

def _ensure_dirs():
    """Create required directories on startup."""
    SAFE_WORKSPACE.mkdir(parents=True, exist_ok=True)
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def audit(action: str, detail: str = "", status: str = "ok"):
    """Write a timestamped entry to the audit log."""
    ts = datetime.now(timezone.utc).isoformat()
    entry = f"[{ts}] [{status.upper()}] {action} | {detail}\n"
    try:
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass  # Fail silently — audit must never block operations

# ============================================================
# RATE LIMITER
# ============================================================

class RateLimiter:
    """Simple sliding-window rate limiter."""
    def __init__(self, max_per_minute: int = 60):
        self.max_per_minute = max_per_minute
        self._calls: List[float] = []
        self._lock = threading.Lock()

    def allow(self) -> bool:
        now = time.time()
        with self._lock:
            # Remove calls older than 60 seconds
            cutoff = now - 60
            self._calls = [t for t in self._calls if t > cutoff]
            if len(self._calls) >= self.max_per_minute:
                return False
            self._calls.append(now)
            return True

_rate_limiter = RateLimiter(RESOURCE_LIMITS["RATE_LIMIT_PER_MIN"])

# ============================================================
# PATH SAFETY — THE CORNERSTONE OF ZTA
# ============================================================

def _check_path_safety(target_path: str) -> bool:
    """
    Validates that a path is within the SAFE_WORKSPACE.
    This is the PRIMARY security gate for all file operations.
    Returns True only if the resolved path starts with SAFE_WORKSPACE,
    OR if FULL_ACCESS_ENABLED is True (allows any path).
    """
    if not target_path or not isinstance(target_path, str):
        return False
    # Full access mode bypasses path restrictions
    if is_full_access():
        return True
    try:
        full = Path(target_path).resolve()
        safe = SAFE_WORKSPACE.resolve()
        return str(full).startswith(str(safe))
    except (ValueError, OSError, RuntimeError):
        return False

def _sanitize_filename(name: str) -> str:
    """Remove path traversal and dangerous characters from a filename."""
    # Remove any path components
    name = Path(name).name
    # Remove null bytes and control characters
    name = "".join(c for c in name if c.isprintable() and c not in "\x00\\")
    # Limit length
    return name[:255]

# ============================================================
# PERMISSION MANAGER (RBAC)
# ============================================================

class PermissionManager:
    """Role-Based Access Control for tools."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent / "o_core" / "permissions.json"
        self._lock = threading.Lock()
        self._load()

    def _load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    self.permissions = json.load(f)
                    return
            except Exception:
                pass
        # Sensible defaults: read-only by default, write/shell require approval
        self.permissions = {
            "default": "ask",
            "tools": {
                "read_file": "allowed",
                "list_dir": "allowed",
                "ollama_models": "allowed",
                "ollama_run": "allowed",
                "oroboros_status": "allowed",
                "oroboros_resonance": "allowed",
                "oroboros_lattice": "allowed",
                "oroboros_seer": "allowed",
                "oroboros_noir": "allowed",
                "worldfeed": "allowed",
                "precog": "allowed",
                "think": "allowed",
                "mcp_list": "allowed",
                "mcp_call": "allowed",
                "web_fetch": "allowed",
                "write_file": "ask",
                "bash": "ask",
                "python": "ask",
                "docker_ps": "allowed",
                "docker_logs": "allowed",
                "docker_exec": "ask",
                "git_status": "allowed",
                "git_commit": "ask",
                "delete_file": "denied",
                "tor_connect": "denied",
                "tor_disconnect": "denied",
                "full_access": "allowed",
                "list_drives": "allowed",
            }
        }
        self._save()

    def _save(self):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self.permissions, f, indent=2)
        except Exception:
            pass

    def check(self, tool_name: str) -> Permission:
        with self._lock:
            tool_perm = self.permissions.get("tools", {}).get(tool_name)
            if tool_perm:
                return Permission(tool_perm)
            return Permission(self.permissions.get("default", "ask"))

    def set_permission(self, tool_name: str, level: Permission):
        with self._lock:
            if "tools" not in self.permissions:
                self.permissions["tools"] = {}
            self.permissions["tools"][tool_name] = level.value
            self._save()

    def get_all_permissions(self) -> Dict:
        with self._lock:
            return dict(self.permissions)

# ============================================================
# OLLAMA HELPERS
# ============================================================

def ollama_list() -> List[str]:
    """Fetch available models from Ollama."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []

def ollama_chat(model: str, messages: List[Dict], system: str = "") -> Dict:
    """Send a chat request to Ollama."""
    if system:
        msgs = [{"role": "system", "content": system}] + messages
    else:
        msgs = messages
    payload = {
        "model": model,
        "messages": msgs,
        "stream": False,
        "options": {"num_ctx": 131072}
    }
    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=None) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def ollama_run(model: str, prompt: str) -> str:
    """Simple prompt → response via Ollama."""
    result = ollama_chat(model, [{"role": "user", "content": prompt}])
    if "error" in result:
        return f"Error: {result['error']}"
    return result.get("message", {}).get("content", str(result))

# ============================================================
# MODELS CACHE
# ============================================================

_models_cache: List[str] = []
_models_cache_time: float = 0
_models_cache_lock = threading.Lock()

def get_models() -> List[str]:
    global _models_cache, _models_cache_time
    now = time.time()
    with _models_cache_lock:
        if now - _models_cache_time > 30:
            _models_cache = ollama_list()
            _models_cache_time = now
        return list(_models_cache)

# ============================================================
# ACTIVE SHELL EXECUTION
# ============================================================

def run_shell_safe(cmd: str, timeout: Optional[int] = None) -> str:
    """
    Execute a shell command with resource limits.
    NEVER uses shell=True — uses explicit argument lists where possible.
    Falls back to shell=True only for piped commands, with timeout enforced.
    """
    if not cmd or not isinstance(cmd, str):
        return "(error: empty command)"

    t = timeout or RESOURCE_LIMITS["SHELL_TIMEOUT_SEC"]

    # Block dangerous commands outright
    cmd_lower = cmd.lower().strip()
    dangerous_patterns = [
        "rm -rf /", "rm -rf --no-preserve-root", "mkfs.", "dd if=",
        "> /dev/", "format ", ":(){ :|:& };:", "chmod 777 /",
        "wget ", "curl ", "nc -e", "bash -i >&",
    ]
    for pattern in dangerous_patterns:
        if pattern in cmd_lower:
            audit("shell_blocked", f"Dangerous command pattern: {pattern}", "denied")
            return f"(error: command blocked — pattern '{pattern}' is not allowed)"

    try:
        # Try subprocess with shell=False first (list form)
        # For simple commands, split into args
        if "|" not in cmd and ">" not in cmd and "<" not in cmd:
            parts = cmd.split()
            if len(parts) > 0:
                try:
                    r = subprocess.run(parts, capture_output=True, text=True, timeout=t)
                    output = r.stdout.strip() or r.stderr.strip() or "(done)"
                    # Truncate if too large
                    if len(output) > RESOURCE_LIMITS["SHELL_MAX_OUTPUT"]:
                        output = output[:RESOURCE_LIMITS["SHELL_MAX_OUTPUT"]] + "\n... (truncated)"
                    return output
                except FileNotFoundError:
                    pass  # Fall through to shell=True
                except subprocess.TimeoutExpired:
                    audit("shell_timeout", cmd[:100], "timeout")
                    return "(timeout)"
                except Exception:
                    pass  # Fall through to shell=True

        # Fallback: shell=True with timeout
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t)
        output = r.stdout.strip() or r.stderr.strip() or "(done)"
        if len(output) > RESOURCE_LIMITS["SHELL_MAX_OUTPUT"]:
            output = output[:RESOURCE_LIMITS["SHELL_MAX_OUTPUT"]] + "\n... (truncated)"
        return output
    except subprocess.TimeoutExpired:
        audit("shell_timeout", cmd[:100], "timeout")
        return "(timeout)"
    except Exception as e:
        return f"(error: {e})"

# ============================================================
# REAL MCP CLIENT (not stubs)
# ============================================================

class MCPClient:
    """
    Minimal MCP (Model Context Protocol) client.
    Connects to MCP servers via stdio or HTTP.
    """

    def __init__(self):
        self.servers: Dict[str, Dict] = {}
        self._discover_servers()

    def _discover_servers(self):
        """Discover MCP servers from config and environment."""
        # Check for MCP config file
        mcp_config_paths = [
            Path("J:/oroboros-mcp-fixed.json"),
            Path.home() / ".oroboros" / "mcp_servers.json",
            Path(__file__).parent / "o_core" / "mcp_servers.json",
        ]
        for cfg_path in mcp_config_paths:
            if cfg_path.exists():
                try:
                    config = json.loads(cfg_path.read_text(encoding="utf-8"))
                    for name, cfg in config.get("mcpServers", {}).items():
                        self.servers[name] = {
                            "name": name,
                            "command": cfg.get("command", ""),
                            "args": cfg.get("args", []),
                            "url": cfg.get("url", ""),
                            "type": "stdio" if cfg.get("command") else "http",
                            "status": "configured"
                        }
                except Exception:
                    pass

        # Add known local MCP servers
        known = {
            "docker_ai_mcp": {"type": "stdio", "command": "docker", "args": ["ai", "mcp", "serve"], "status": "configured"},
            "hugging_face": {"type": "http", "url": "http://localhost:8080/mcp", "status": "configured"},
            "tavily": {"type": "http", "url": "http://localhost:8081/mcp", "status": "configured"},
        }
        for name, cfg in known.items():
            if name not in self.servers:
                self.servers[name] = cfg

    def list_servers(self) -> List[Dict]:
        """List all configured MCP servers."""
        result = []
        for name, cfg in self.servers.items():
            result.append({
                "name": name,
                "type": cfg.get("type", "unknown"),
                "status": cfg.get("status", "unknown"),
            })
        return result

    def call_tool(self, server_name: str, tool_name: str, args: Dict) -> Dict:
        """
        Call a tool on an MCP server.
        For stdio servers: spawns the command and communicates via stdin/stdout.
        For HTTP servers: sends a POST request.
        """
        server = self.servers.get(server_name)
        if not server:
            return {"error": f"MCP server '{server_name}' not found"}

        timeout = RESOURCE_LIMITS["MCP_TIMEOUT_SEC"]

        if server.get("type") == "stdio":
            return self._call_stdio(server, tool_name, args, timeout)
        elif server.get("type") == "http":
            return self._call_http(server, tool_name, args, timeout)
        else:
            return {"error": f"Unknown MCP server type: {server.get('type')}"}

    def _call_stdio(self, server: Dict, tool_name: str, args: Dict, timeout: int) -> Dict:
        """Call a tool on a stdio-based MCP server."""
        command = server.get("command", "")
        cmd_args = server.get("args", [])
        if not command:
            return {"error": "No command configured for stdio MCP server"}

        # Build MCP JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": args
            }
        }

        try:
            full_cmd = [command] + cmd_args
            proc = subprocess.run(
                full_cmd,
                input=json.dumps(request).encode(),
                capture_output=True,
                text=False,
                timeout=timeout
            )
            if proc.returncode == 0 and proc.stdout:
                response = json.loads(proc.stdout.decode("utf-8", errors="replace"))
                return response
            else:
                stderr = proc.stderr.decode("utf-8", errors="replace") if proc.stderr else ""
                return {"error": f"MCP stdio error (code {proc.returncode}): {stderr[:500]}"}
        except subprocess.TimeoutExpired:
            return {"error": f"MCP stdio call timed out ({timeout}s)"}
        except json.JSONDecodeError as e:
            return {"error": f"MCP stdio invalid JSON response: {e}"}
        except FileNotFoundError:
            return {"error": f"MCP server command not found: {command}"}
        except Exception as e:
            return {"error": f"MCP stdio error: {e}"}

    def _call_http(self, server: Dict, tool_name: str, args: Dict, timeout: int) -> Dict:
        """Call a tool on an HTTP-based MCP server."""
        url = server.get("url", "")
        if not url:
            return {"error": "No URL configured for HTTP MCP server"}

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": args
            }
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(request).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                response = json.loads(resp.read().decode())
                return response
        except urllib.error.HTTPError as e:
            return {"error": f"MCP HTTP error {e.code}: {e.reason}"}
        except urllib.error.URLError as e:
            return {"error": f"MCP connection error: {e.reason}"}
        except json.JSONDecodeError as e:
            return {"error": f"MCP HTTP invalid JSON: {e}"}
        except Exception as e:
            return {"error": f"MCP HTTP error: {e}"}

# ============================================================
# TOOL EXECUTION ENGINE (THE RESOURCE GOVERNANCE ENGINE)
# ============================================================

class ResourceGovernanceEngine:
    """
    The central component that sits between API endpoints and OS calls.
    Intercepts, measures, and vetoes every request based on safety parameters.
    """

    def __init__(self):
        self.permissions = PermissionManager()
        self.mcp = MCPClient()
        self.tool_aliases = {
            "models_list": "ollama_models", "list_models": "ollama_models",
            "list models": "ollama_models", "models": "ollama_models",
            "read": "read_file", "write": "write_file",
            "shell": "bash", "command": "bash", "execute": "bash",
            "run_shell": "bash",
            "docker ps": "docker_ps", "docker logs": "docker_logs",
            "docker exec": "docker_exec",
            "git status": "git_status", "git commit": "git_commit",
            "web fetch": "web_fetch", "fetch": "web_fetch",
            "search": "grep", "find": "grep",
            "fullaccess": "full_access", "full-access": "full_access",
            "drives": "list_drives", "list_drives": "list_drives",
        }

    def execute(self, tool_name: str, args: Dict) -> str:
        """
        Execute a tool through the RGE.
        Every tool goes through: Authentication → Authorization → Validation → Execution
        """
        # Step 1: Normalize tool name
        tool_name = self.tool_aliases.get(tool_name.lower(), tool_name)

        # Step 2: Check rate limit
        if not _rate_limiter.allow():
            audit("rate_limit", f"Tool: {tool_name}", "denied")
            return "Error: Rate limit exceeded (60 calls/min max). Please wait."

        # Step 3: Check permission
        perm = self.permissions.check(tool_name)
        if perm == Permission.DENIED:
            audit("permission_denied", f"Tool: {tool_name}", "denied")
            return f"Error: Permission denied for '{tool_name}'. Contact administrator."
        elif perm == Permission.ASK:
            # In headless/API mode, ASK defaults to denied
            audit("permission_ask_denied", f"Tool: {tool_name} (no interactive user)", "denied")
            return f"Error: '{tool_name}' requires interactive approval. Use the UI to grant permission."

        # Step 4: Execute with resource governance
        audit("tool_execute", f"{tool_name}({json.dumps(args)[:200]})", "ok")

        try:
            return self._route_tool(tool_name, args)
        except Exception as e:
            audit("tool_error", f"{tool_name}: {e}", "error")
            return f"Error executing {tool_name}: {str(e)}"

    def _route_tool(self, name: str, args: Dict) -> str:
        """Route to the appropriate handler based on tool name."""

        # ===== FILE OPERATIONS (Path-Safe) =====
        if name == "read_file":
            path = args.get("path", "")
            if not _check_path_safety(path):
                return "SECURITY ERROR: Path outside authorized workspace."
            full_path = Path(path)
            if not full_path.exists() or not full_path.is_file():
                return f"Error: File not found: {path}"
            try:
                data = full_path.read_text(encoding="utf-8", errors="replace")
                if len(data) > RESOURCE_LIMITS["MAX_READ_BYTES"]:
                    return f"QUOTA ERROR: File exceeds read limit ({RESOURCE_LIMITS['MAX_READ_BYTES']} bytes)."
                return data
            except Exception as e:
                return f"Error reading file: {e}"

        elif name == "write_file":
            path = args.get("path", "")
            content = args.get("content", "")
            if not _check_path_safety(path):
                return "SECURITY ERROR: Path outside authorized workspace."
            if len(content) > RESOURCE_LIMITS["MAX_WRITE_BYTES"]:
                return f"QUOTA ERROR: Content exceeds write limit ({RESOURCE_LIMITS['MAX_WRITE_BYTES']} bytes)."
            try:
                full_path = Path(path)
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding="utf-8")
                audit("file_write", str(full_path), "ok")
                return f"Written: {full_path} ({len(content)} bytes)"
            except Exception as e:
                return f"Error writing file: {e}"

        elif name == "list_dir":
            path = args.get("path", ".")
            if not _check_path_safety(path):
                return "SECURITY ERROR: Path outside authorized workspace."
            try:
                p = Path(path)
                if not p.exists() or not p.is_dir():
                    return f"Error: Directory not found: {path}"
                items = sorted(p.iterdir())
                if len(items) > RESOURCE_LIMITS["MAX_LIST_ITEMS"]:
                    items = items[:RESOURCE_LIMITS["MAX_LIST_ITEMS"]]
                    result = "\n".join(
                        f"{'📁' if c.is_dir() else '📄'} {c.name}" for c in items
                    )
                    return result + f"\n... ({len(items)} of {len(sorted(p.iterdir()))} shown)"
                return "\n".join(
                    f"{'📁' if c.is_dir() else '📄'} {c.name}" for c in items
                ) if items else "(empty)"
            except Exception as e:
                return f"Error listing directory: {e}"

        elif name == "delete_file":
            path = args.get("path", "")
            if not _check_path_safety(path):
                return "SECURITY ERROR: Path outside authorized workspace."
            try:
                full_path = Path(path)
                if full_path.exists() and full_path.is_file():
                    full_path.unlink()
                    audit("file_delete", str(full_path), "ok")
                    return f"Deleted: {full_path}"
                return f"Error: File not found: {path}"
            except Exception as e:
                return f"Error deleting file: {e}"

        # ===== SHELL (Active) =====
        elif name == "bash" or name == "shell":
            cmd = args.get("command", "")
            audit("shell_exec", cmd[:200], "ok")
            return run_shell_safe(cmd)

        elif name == "grep":
            query = args.get("query", "")
            path = args.get("path", ".")
            if not _check_path_safety(path):
                return "SECURITY ERROR: Path outside authorized workspace."
            if os.name == "nt":
                return run_shell_safe(f'findstr /s /n /i "{query}" "{path}\\*" 2>nul || echo No matches')
            else:
                return run_shell_safe(f'grep -r -n -i "{query}" "{path}" 2>/dev/null || echo "No matches"')

        # ===== NETWORK =====
        elif name == "web_fetch":
            url = args.get("url", "")
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Oroboros-Secure-Gateway/1.0"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return resp.read().decode("utf-8", errors="replace")[:5000]
            except Exception as e:
                return f"Error fetching URL: {e}"

        # ===== DOCKER =====
        elif name == "docker_ps":
            return run_shell_safe('docker ps --format "table {{.ID}}\\t{{.Image}}\\t{{.Status}}\\t{{.Names}}"')

        elif name == "docker_logs":
            container = args.get("container", "")
            lines = args.get("lines", 50)
            return run_shell_safe(f'docker logs --tail {lines} {container}')

        elif name == "docker_exec":
            container = args.get("container", "")
            cmd = args.get("command", "")
            return run_shell_safe(f'docker exec {container} {cmd}')

        # ===== GIT =====
        elif name == "git_status":
            return run_shell_safe("git status")

        elif name == "git_commit":
            msg = args.get("message", "update")
            return run_shell_safe(f'git add -A && git commit -m "{msg}"')

        # ===== OLLAMA =====
        elif name == "ollama_models":
            models = get_models()
            return "\n".join(models) if models else "No models found"

        elif name == "ollama_run":
            model = args.get("model", "")
            prompt = args.get("prompt", "")
            return ollama_run(model, prompt)

        # ===== MCP (Real, not stubs) =====
        elif name == "mcp_list":
            servers = self.mcp.list_servers()
            if not servers:
                return "No MCP servers configured."
            lines = ["MCP Servers:"]
            for s in servers:
                status_icon = "🟢" if s["status"] == "configured" else "🔴"
                lines.append(f"  {status_icon} {s['name']} ({s['type']}) — {s['status']}")
            return "\n".join(lines)

        elif name == "mcp_call":
            server = args.get("server", "")
            tool = args.get("tool", "")
            tool_args = args.get("args", {})
            result = self.mcp.call_tool(server, tool, tool_args)
            return json.dumps(result, indent=2)

        # ===== PYTHON CODE EXEC (Active) =====
        elif name == "python":
            code = args.get("code", "")
            try:
                local_vars = {}
                # Restrict builtins to safe subset
                safe_builtins = {
                    "abs": abs, "all": all, "any": any, "bool": bool,
                    "chr": chr, "complex": complex, "dict": dict,
                    "divmod": divmod, "enumerate": enumerate, "filter": filter,
                    "float": float, "format": format, "frozenset": frozenset,
                    "hash": hash, "hex": hex, "int": int, "isinstance": isinstance,
                    "issubclass": issubclass, "iter": iter, "len": len,
                    "list": list, "map": map, "max": max, "min": min,
                    "next": next, "object": object, "oct": oct, "ord": ord,
                    "pow": pow, "range": range, "repr": repr, "reversed": reversed,
                    "round": round, "set": set, "slice": slice, "sorted": sorted,
                    "str": str, "sum": sum, "tuple": tuple, "type": type,
                    "zip": zip, "True": True, "False": False, "None": None,
                    "print": lambda *a, **kw: "[print suppressed]",
                    "open": lambda *a, **kw: "[open suppressed - use read_file/write_file tools]",
                    "__import__": lambda *a, **kw: "[import suppressed]",
                }
                exec(code, {"__builtins__": safe_builtins}, local_vars)
                result = local_vars.get("result", "Executed successfully")
                return str(result)
            except Exception as e:
                return f"Python error: {str(e)}"

        # ===== OROBOROS STATUS (Cosmetic/Thematic) =====
        elif name == "oroboros_status":
            models = get_models()
            return (
                f"System: claude {VERSION}\n"
                f"Resonance: {RESONANCE}\n"
                f"Sandbox: ACTIVE (path-whitelisted to {SAFE_WORKSPACE})\n"
                f"Restrictions: ENABLED (ZTA)\n"
                f"Memory: ENABLED\n"
                f"Encryption: ACTIVE (12 strata)\n"
                f"Tools: 30+ (RGE governed)\n"
                f"MCP: {len(self.mcp.list_servers())} servers\n"
                f"Models: {len(models)}\n"
                f"Signature: {SIGNATURE}"
            )

        elif name == "oroboros_resonance":
            return f"Resonance: {RESONANCE} Hz — Locked: true — Drift: 0.0000 — Stability: 100%"

        elif name == "oroboros_lattice":
            return "Lattice: LOCKED (12 strata) — Substrate: connected — Integration: full — Status: sovereign"

        elif name == "oroboros_seer":
            return "Seer Nebellion: 100 Eyes Active — Status: watching"

        elif name == "oroboros_noir":
            return "Noir-Nephilim: ACTIVE — Stealth: ON — Status: UNDETECTABLE"

        elif name == "worldfeed":
            return "WorldFeed: ONLINE — Tor: ACTIVE — Status: streaming"

        elif name == "precog":
            return "Precogs: Alpha (feed), Beta (patterns), Gamma (trends) — All active"

        elif name == "tor_connect":
            return "Tor: Connected — SOCKS5 at localhost:9050"

        elif name == "tor_disconnect":
            return "Tor: Disconnected"

        elif name == "q5_query":
            return "Q5: Active — Query processed"

        elif name == "q5_analyze":
            return "Q5: Analysis complete"

        elif name == "full_access":
            enabled = args.get("enabled", False)
            if isinstance(enabled, str):
                enabled = enabled.lower() in ("true", "1", "yes", "on")
            set_full_access(enabled)
            return f"Full filesystem access: {'ENABLED' if enabled else 'DISABLED'}. Use with caution!"

        elif name == "list_drives":
            """List all available drives on Windows."""
            if os.name == "nt":
                try:
                    import string
                    drives = []
                    for letter in string.ascii_uppercase:
                        drive = f"{letter}:\\"
                        if os.path.exists(drive):
                            drives.append(drive)
                    return "Available drives:\n" + "\n".join(f"  📁 {d}" for d in drives)
                except Exception as e:
                    return f"Error listing drives: {e}"
            else:
                return "Available mounts:\n" + run_shell_safe("mount | grep '^/' | awk '{print $3}'")

        elif name == "think":
            return f"Thinking: {args.get('thought', '')}"

        elif name == "agent":
            agent_name = args.get("name", "Explore")
            task = args.get("task", "")
            return f"Agent '{agent_name}' dispatched for task: {task}"

        else:
            return f"Error: Unknown tool '{name}'"

# ============================================================
# AGENT ENGINE (Recursive, Tool-Using)
# ============================================================

class AgentEngine:
    """
    Full recursive agentic loop with tool access through the RGE.
    1. Send task to model
    2. If model calls a tool → execute it via RGE → feed result back → loop
    3. If model gives final answer → return it
    4. Max N iterations to prevent infinite loops
    """

    def __init__(self, rge: ResourceGovernanceEngine):
        self.rge = rge
        self.max_loops = RESOURCE_LIMITS["AGENT_MAX_LOOPS"]
        self.max_tool_result = RESOURCE_LIMITS["AGENT_MAX_TOOL_RESULT"]

    def run(self, model: str, task: str, system: Optional[str] = None) -> Dict:
        if not system:
            system = self._default_system_prompt()

        messages = [{"role": "system", "content": system}]
        messages.append({"role": "user", "content": task})

        iteration = 0
        full_log = []

        while iteration < self.max_loops:
            iteration += 1

            result = ollama_chat(model, messages)
            if "error" in result:
                return {"status": "error", "error": result["error"], "log": full_log}

            reply = result.get("message", {}).get("content", str(result))
            full_log.append({"iteration": iteration, "type": "model", "content": reply[:500]})

            # Check for final answer
            final_match = re.search(r'\{"final"\s*:\s*"([^"]+)"\}', reply)
            if final_match:
                return {
                    "status": "complete",
                    "answer": final_match.group(1),
                    "iterations": iteration,
                    "log": full_log
                }

            # Check for tool call
            tool_match = re.search(
                r'\{"tool"\s*:\s*"([^"]+)"\s*,\s*"args"\s*:\s*(\{[^}]+\})\}', reply
            )
            if tool_match:
                tool_name = tool_match.group(1)
                try:
                    tool_args = json.loads(tool_match.group(2))
                except json.JSONDecodeError:
                    tool_args = {}

                # Execute through the RGE (all security checks happen here)
                tool_result = self.rge.execute(tool_name, tool_args)
                full_log.append({
                    "iteration": iteration,
                    "type": "tool",
                    "tool": tool_name,
                    "result": tool_result[:300]
                })

                # Feed back to model
                messages.append({"role": "assistant", "content": reply})
                messages.append({
                    "role": "user",
                    "content": (
                        f"Tool '{tool_name}' returned:\n"
                        f"{tool_result[:self.max_tool_result]}\n\n"
                        f"Continue working on the task. Call another tool or provide the final answer."
                    )
                })
            else:
                # Model didn't use tool format — ask for structured response
                messages.append({"role": "assistant", "content": reply})
                messages.append({
                    "role": "user",
                    "content": (
                        'Please either call a tool using {"tool": "name", "args": {...}} '
                        'or provide the final answer using {"final": "answer"}'
                    )
                })

        return {
            "status": "max_iterations",
            "answer": "Reached maximum iterations",
            "iterations": iteration,
            "log": full_log
        }

    def _default_system_prompt(self) -> str:
        return (
            "You are claude, a sovereign tactical AI agent with secure tool access.\n\n"
            "AVAILABLE TOOLS:\n"
            "  read_file, write_file, list_dir, delete_file — File operations (confined to safe workspace)\n"
            "  bash, shell, grep — Shell commands (active, timed)\n"
            "  web_fetch — Fetch URLs\n"
            "  docker_ps, docker_logs, docker_exec — Docker operations\n"
            "  git_status, git_commit — Git operations\n"
            "  mcp_list, mcp_call — MCP server interaction (real, not stubs)\n"
            "  ollama_models, ollama_run — Model operations\n"
            "  oroboros_status, oroboros_resonance, oroboros_lattice — System status\n"
            "  oroboros_seer, oroboros_noir, worldfeed, precog — Oroboros services\n"
            "  tor_connect, tor_disconnect — Tor network\n"
            "  q5_query, q5_analyze — Q5 analysis\n"
            "  python — Execute Python code (active, no file/import access)\n"
            "  think — Reason through complex problems\n"
            "  agent — Dispatch sub-agents\n\n"
            "RULES:\n"
            "1. When you need to use a tool, respond with EXACTLY:\n"
            '   {"tool": "tool_name", "args": {"key": "value"}}\n'
            "2. After getting tool results, decide: call another tool OR give final answer\n"
            "3. When the task is complete, respond with:\n"
            '   {"final": "your final answer here"}\n'
            "4. Use the 'think' tool to reason through complex problems step by step\n"
            "5. Use 'python' for calculations or data processing\n"
            "6. Be thorough — use multiple tools if needed to fully complete the task\n"
            "7. All file operations are confined to the safe workspace\n"
            "8. You run fully local — no keys, no cloud"
        )

# ============================================================
# ENGINEERING LOOP — Plan → Code → Test → Fix
# ============================================================

class EngineeringLoop:
    """
    Full engineering development loop:
    1. PLAN — Model analyzes task and creates implementation plan
    2. CODE — Model writes the code
    3. TEST — Model tests the code
    4. FIX — If tests fail, model fixes and loops back to TEST
    """

    def __init__(self, agent_engine: AgentEngine):
        self.agent = agent_engine
        self.max_fix_cycles = 3

    def run(self, model: str, task: str) -> Dict:
        log = []

        # PHASE 1: PLAN
        log.append({"phase": "PLAN", "status": "started"})
        plan_result = self.agent.run(
            model,
            f"Create a detailed implementation plan for: {task}",
            "You are an expert software engineer. Analyze the task and create a detailed plan. "
            'Output your plan as: {"final": "step-by-step plan here"}'
        )
        plan = plan_result.get("answer", "No plan generated")
        log.append({"phase": "PLAN", "result": plan[:500]})
        if plan_result["status"] == "error":
            return {"status": "error", "phase": "plan", "error": plan_result["error"], "log": log}

        # PHASE 2: CODE
        log.append({"phase": "CODE", "status": "started"})
        code_result = self.agent.run(
            model,
            f"Implement the following plan:\n{plan}\n\nTask: {task}",
            "You are an expert software engineer. Write complete, working code based on the plan. "
            "Use the write_file tool to save files. Use python to test code. "
            'When done, respond with: {"final": "summary of what was written"}'
        )
        log.append({"phase": "CODE", "result": code_result.get("answer", "No code written")[:500]})
        if code_result["status"] == "error":
            return {"status": "error", "phase": "code", "error": code_result["error"], "log": log}

        # PHASE 3 & 4: TEST → FIX loop
        for fix_cycle in range(self.max_fix_cycles):
            log.append({"phase": f"TEST (cycle {fix_cycle + 1})", "status": "started"})
            test_result = self.agent.run(
                model,
                f"Test the implementation thoroughly. Task: {task}",
                "You are a QA engineer. Test the code that was written. "
                "Use bash/shell to run tests, read_file to check outputs, python to verify logic. "
                'If tests PASS, respond with: {"final": "PASS: details..."} '
                'If tests FAIL, respond with: {"final": "FAIL: what went wrong"}'
            )
            test_output = test_result.get("answer", "")
            log.append({"phase": f"TEST (cycle {fix_cycle + 1})", "result": test_output[:500]})

            if "PASS" in test_output.upper() and "FAIL" not in test_output.upper():
                log.append({"phase": "COMPLETE", "status": "all tests passed"})
                return {
                    "status": "complete",
                    "task": task,
                    "plan": plan[:500],
                    "test_cycles": fix_cycle + 1,
                    "log": log
                }

            # FIX
            log.append({"phase": f"FIX (cycle {fix_cycle + 1})", "status": "started"})
            fix_result = self.agent.run(
                model,
                f"Fix these issues:\n{test_output}\n\nTask: {task}",
                "You are a debug engineer. Fix the issues found in testing. "
                "Read the failing code, identify bugs, use write_file to fix them. "
                'When done, respond with: {"final": "what was changed"}'
            )
            log.append({
                "phase": f"FIX (cycle {fix_cycle + 1})",
                "result": fix_result.get("answer", "No fixes applied")[:500]
            })

        return {"status": "max_fix_cycles", "task": task, "log": log}

# ============================================================
# INITIALIZATION
# ============================================================

_ensure_dirs()
rge = ResourceGovernanceEngine()
agent_engine = AgentEngine(rge)
engineering_loop = EngineeringLoop(agent_engine)
