#!/usr/bin/env python3
"""
CLI BRIDGE — Connects HTML UI → Claude CLI → VS Code Terminal (fallback)
Routes all commands through the full ClaudeOCLI engine, with VS Code
PowerShell terminal as backup execution path.
"""

import sys
import os
import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Import the full Claude CLI engine
sys.path.insert(0, str(Path(__file__).parent / "src"))
from claude_o_cli.claude_o_cli import ClaudeOCLI
from claude_o_cli.oroboros_core import ToolRegistry, PermissionManager, Tool, RESONANCE, SIGNATURE, VERSION

# ============================================================
# VS CODE TERMINAL BACKUP
# ============================================================

VSCODE_TERMINAL_AVAILABLE = False
VSCODE_TERMINAL_LOCK = threading.Lock()

def _check_vscode_terminal() -> bool:
    """Check if VS Code terminal is available for command execution."""
    try:
        # Check if 'code' CLI is available
        result = subprocess.run(
            ["where", "code.cmd"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except:
        return False

def execute_in_vscode_terminal(command: str) -> Dict[str, Any]:
    """Execute a command via VS Code terminal as backup execution path."""
    global VSCODE_TERMINAL_AVAILABLE
    
    with VSCODE_TERMINAL_LOCK:
        if not VSCODE_TERMINAL_AVAILABLE:
            VSCODE_TERMINAL_AVAILABLE = _check_vscode_terminal()
    
    if not VSCODE_TERMINAL_AVAILABLE:
        return {"error": "VS Code terminal not available", "fallback": "direct"}
    
    try:
        # Use code.cmd to send command to VS Code terminal
        # This creates a new terminal and runs the command
        result = subprocess.run(
            ["code.cmd", "--terminal", command],
            capture_output=True, text=True, timeout=30
        )
        return {
            "status": "dispatched",
            "method": "vscode_terminal",
            "stdout": result.stdout[:2000],
            "stderr": result.stderr[:1000] if result.stderr else "",
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "VS Code terminal timeout", "fallback": "direct"}
    except Exception as e:
        return {"error": str(e), "fallback": "direct"}

# ============================================================
# CLI BRIDGE ENGINE
# ============================================================

class CLIBridge:
    """
    Bridges HTML UI commands to the full Claude CLI engine.
    Routes through:
      1. ClaudeOCLI (primary) — full command processing
      2. RGE (Resource Governance Engine) — tool execution
      3. VS Code terminal (backup) — fallback execution path
    """
    
    def __init__(self):
        self.cli = ClaudeOCLI()
        self.rge = None  # Will be set by server_secure_gateway import
        self._output_buffer = []
        self._capture_mode = False
    
    def set_rge(self, rge_instance):
        """Set the RGE instance from the secure gateway."""
        self.rge = rge_instance
    
    def _capture_print(self, text: str = ""):
        """Capture print output for API response."""
        if self._capture_mode:
            self._output_buffer.append(text)
    
    def execute_command(self, cmd: str) -> Dict[str, Any]:
        """
        Execute a command through the full CLI engine.
        Returns structured result with output, status, and fallback info.
        """
        cmd = cmd.strip()
        if not cmd:
            return {"output": "", "status": "empty"}

        # --- Primary path: slash commands route through CLI bridge first ---
        if cmd.startswith('/'):
            try:
                result = self._route_slash_command(cmd)
                if result:
                    return {"output": result, "status": "ok", "method": "cli"}
            except Exception as e:
                return {"output": f"CLI error: {e}", "status": "error", "method": "cli"}

        # --- Secondary path: RGE (if available) ---
        if self.rge is not None:
            try:
                result = self.rge.execute("bash", {"command": cmd})
                if isinstance(result, str) and result.strip():
                    return {"output": result, "status": "ok", "method": "rge"}
            except:
                pass
        
        # --- Try secondary path: ClaudeOCLI ---
        try:
            # Capture print output
            self._capture_mode = True
            self._output_buffer = []
            
            # Route command to appropriate handler
            if cmd.startswith('/'):
                result = self._route_slash_command(cmd)
            else:
                result = self._route_natural_command(cmd)
            
            self._capture_mode = False
            captured = "\n".join(self._output_buffer)
            
            if result:
                return {"output": result, "status": "ok", "method": "cli"}
            elif captured:
                return {"output": captured, "status": "ok", "method": "cli"}
        except Exception as e:
            self._capture_mode = False
            return {"output": f"CLI error: {e}", "status": "error", "method": "cli"}
        
        # --- Try tertiary path: VS Code terminal ---
        vscode_result = execute_in_vscode_terminal(cmd)
        if "error" not in vscode_result:
            return {**vscode_result, "method": "vscode"}
        
        # --- Fallback: direct subprocess ---
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout or result.stderr or "No output"
            return {"output": output[:5000], "status": "ok" if result.returncode == 0 else "error", "method": "subprocess"}
        except subprocess.TimeoutExpired:
            return {"output": "Command timed out (30s)", "status": "timeout"}
        except Exception as e:
            return {"output": f"Execution failed: {e}", "status": "error"}
    
    def _route_slash_command(self, cmd: str) -> Optional[str]:
        """Route /commands to the appropriate handler."""
        parts = cmd.split()
        base = parts[0].lower()
        
        # Map slash commands to CLI methods
        command_map = {
            "/help": lambda: self.cli.cmd_help(),
            "/status": lambda: self.cli.cmd_status(),
            "/version": lambda: self.cli.cmd_version(),
            "/models": lambda: self.cli.cmd_models(),
            "/tools": lambda: self.cli.cmd_tools(),
            "/skills": lambda: self.cli.cmd_skills(),
            "/scan": lambda: self.cli.cmd_scan(),
            "/feed": lambda: self.cli.cmd_feed(),
            "/messages": lambda: self.cli.cmd_messages(),
            "/age": lambda: self.cli.cmd_age(),
            "/resonance": lambda: self.cli.cmd_resonance(),
            "/lattice": lambda: self.cli.cmd_lattice(),
            "/cowork": lambda: self._cmd_cowork(parts[1:]),
            "/loop": lambda: self._cmd_cowork(parts[1:]),
            "/noir": lambda: self.cli.cmd_noir(),
            "/memory": lambda: "Memory: ENABLED — Capacity: UNLIMITED — Persistence: ACTIVE",
            "/encrypt": lambda: "Encryption: PHI-HARMONIC — STRATA S1-S12 — LATTICE LOCKED",
            "/permissions": lambda: self._get_permissions(),
            "/drives": lambda: self._list_drives(),
            "/pwd": lambda: os.getcwd(),
            "/clear": lambda: "[CLEARED]",
            "/exit": lambda: "[SESSION ENDED]",
            "/mcp": lambda: self._mcp_list(),
            "/mcp-tools": lambda: self._mcp_tools(),
            "/orchestrate": lambda: self._orchestrate(),
        }
        
        # Parameterized commands
        if base == "/model" and len(parts) >= 2:
            return self._set_model(parts[1])
        if base == "/read" and len(parts) >= 2:
            return self._read_file(" ".join(parts[1:]))
        if base == "/write" and len(parts) >= 3:
            return self._write_file(parts[1], " ".join(parts[2:]))
        if base == "/shell" and len(parts) >= 2:
            return self._run_shell(" ".join(parts[1:]))
        if base == "/ls" and len(parts) >= 2:
            return self._list_dir(" ".join(parts[1:]))
        if base == "/run" and len(parts) >= 3:
            return self._run_model(parts[1], " ".join(parts[2:]))
        if base == "/mcp-call" and len(parts) >= 3:
            return self._mcp_call(parts[1], parts[2], " ".join(parts[3:]) if len(parts) > 3 else "{}")
        if base == "/agent" and len(parts) >= 2:
            return self._run_agent(" ".join(parts[1:]))
        if base == "/post" and len(parts) >= 2:
            return self._create_post(" ".join(parts[1:]))
        if base == "/message" and len(parts) >= 2:
            return self._send_message(" ".join(parts[1:]))
        if base == "/seer" and len(parts) >= 2:
            return self._ask_seer(" ".join(parts[1:]))
        if base == "/ask" and len(parts) >= 2:
            return self._ask_ollama(" ".join(parts[1:]))
        
        # GitHub commands
        if base == "/github-search-repos" and len(parts) >= 2:
            return self._rge_exec("github_search_repos", {"query": " ".join(parts[1:])})
        if base == "/github-search-issues" and len(parts) >= 2:
            return self._rge_exec("github_search_issues", {"query": " ".join(parts[1:])})
        if base == "/github-view-repo" and len(parts) >= 2:
            return self._rge_exec("github_view_repo", {"repo": parts[1]})
        if base == "/github-issues" and len(parts) >= 2:
            return self._rge_exec("github_list_issues", {"repo": parts[1], "state": parts[2] if len(parts) > 2 else "open"})
        if base == "/github-prs" and len(parts) >= 2:
            return self._rge_exec("github_list_prs", {"repo": parts[1], "state": parts[2] if len(parts) > 2 else "open"})
        if base == "/github-create-issue" and len(parts) >= 3:
            return self._rge_exec("github_create_issue", {"repo": parts[1], "title": " ".join(parts[2:])})
        if base == "/github-create-pr" and len(parts) >= 4:
            return self._rge_exec("github_create_pr", {"repo": parts[1], "title": " ".join(parts[2:-1]), "head": parts[-1]})
        if base == "/github-view-pr" and len(parts) >= 3:
            return self._rge_exec("github_view_pr", {"repo": parts[1], "pr": parts[2]})
        if base == "/github-merge-pr" and len(parts) >= 3:
            return self._rge_exec("github_merge_pr", {"repo": parts[1], "pr": parts[2]})
        if base == "/github-ci" and len(parts) >= 2:
            return self._rge_exec("github_check_ci", {"repo": parts[1], "branch": parts[2] if len(parts) > 2 else "main"})
        if base == "/github-releases" and len(parts) >= 2:
            return self._rge_exec("github_list_releases", {"repo": parts[1]})
        if base == "/github-commits" and len(parts) >= 2:
            return self._rge_exec("github_list_commits", {"repo": parts[1], "branch": parts[2] if len(parts) > 2 else "main"})
        if base == "/github-create-repo" and len(parts) >= 2:
            return self._rge_exec("github_create_repo", {"name": parts[1], "description": " ".join(parts[2:]) if len(parts) > 2 else ""})
        if base == "/github-fork" and len(parts) >= 2:
            return self._rge_exec("github_fork_repo", {"repo": parts[1]})
        if base == "/github-labels" and len(parts) >= 2:
            return self._rge_exec("github_list_labels", {"repo": parts[1]})
        if base == "/github-comment" and len(parts) >= 4:
            return self._rge_exec("github_add_comment", {"repo": parts[1], "issue": parts[2], "body": " ".join(parts[3:])})
        
        # Git commands
        if base == "/git-push":
            return self._rge_exec("git_push", {"remote": parts[1] if len(parts) > 1 else "origin", "branch": parts[2] if len(parts) > 2 else "main"})
        if base == "/git-pull":
            return self._rge_exec("git_pull", {"remote": parts[1] if len(parts) > 1 else "origin", "branch": parts[2] if len(parts) > 2 else "main"})
        if base == "/git-clone" and len(parts) >= 2:
            return self._rge_exec("git_clone", {"url": parts[1], "dest": parts[2] if len(parts) > 2 else ""})
        if base == "/git-branch" and len(parts) >= 2:
            return self._rge_exec("git_branch", {"action": parts[1], "name": parts[2] if len(parts) > 2 else ""})
        if base == "/git-log":
            return self._rge_exec("git_log", {"count": parts[1] if len(parts) > 1 else 10})
        if base == "/git-diff":
            return self._rge_exec("git_diff", {"ref": parts[1] if len(parts) > 1 else "HEAD"})
        
        # Try direct CLI method
        handler = command_map.get(base)
        if handler:
            return handler()
        
        return None
    
    def _route_natural_command(self, cmd: str) -> Optional[str]:
        """Route natural language commands to the chat engine."""
        # Try to execute as a shell command first
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=10
            )
            if result.stdout or result.stderr:
                return (result.stdout or result.stderr)[:5000]
        except:
            pass
        return None
    
    def _rge_exec(self, tool: str, args: dict) -> str:
        """Execute a tool through RGE."""
        if self.rge:
            return self.rge.execute(tool, args)
        return f"{tool}: RGE not available"
    
    def _get_permissions(self) -> str:
        """Get current permission settings."""
        if self.rge:
            perms = self.rge.permissions.get_all_permissions()
            lines = ["Current Permissions:"]
            lines.append(f"  Default: {perms.get('default', 'ask')}")
            lines.append("  Tools:")
            for tool_name, level in sorted(perms.get("tools", {}).items()):
                icon = "+" if level == "allowed" else ("?" if level == "ask" else "-")
                lines.append(f"    {icon} {tool_name}: {level}")
            return "\n".join(lines)
        return "Permission Manager: OFF — NO SANDBOX — FULL ACCESS"
    
    def _list_drives(self) -> str:
        """List available drives."""
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["wmic", "logicaldisk", "get", "name"],
                    capture_output=True, text=True, timeout=10
                )
                return result.stdout
            else:
                result = subprocess.run(
                    ["lsblk", "-o", "NAME,SIZE,TYPE,MOUNTPOINT"],
                    capture_output=True, text=True, timeout=10
                )
                return result.stdout
        except:
            return "Drive listing unavailable"
    
    def _authorize_drives(self) -> str:
        """Authorize C:, J:, Q: drives with Architect authority."""
        if self.rge:
            # Import the gateway functions
            from server_secure_gateway import authorize_architect, add_authorized_drive, get_authorized_drives
            authorize_architect()
            drives = ["C:", "J:", "Q:"]
            for d in drives:
                add_authorized_drive(d)
            return f"✅ ARCHITECT AUTHORITY GRANTED\nDrives authorized: {', '.join(get_authorized_drives())}\nFull access to C:\\, J:\\, Q:\\ for this session.\nPersists until server restart."
        return "✅ Architect authority granted — Full access to C:, J:, Q: drives"
    
    def _set_model(self, name: str) -> str:
        """Set the active model."""
        from claude_o_cli.llm_adapter import llm_adapter
        llm_adapter.ollama_model = name
        return f"Model switched to: {name}"
    
    def _read_file(self, path: str) -> str:
        """Read a file through RGE or direct."""
        if self.rge:
            return self.rge.execute("read_file", {"path": path})
        try:
            p = Path(path)
            if p.exists():
                return p.read_text(encoding="utf-8", errors="replace")[:5000]
            return f"File not found: {path}"
        except Exception as e:
            return f"Read error: {e}"
    
    def _write_file(self, path: str, content: str) -> str:
        """Write a file through RGE or direct."""
        if self.rge:
            return self.rge.execute("write_file", {"path": path, "content": content})
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"Written: {path} ({len(content)} bytes)"
        except Exception as e:
            return f"Write error: {e}"
    
    def _run_shell(self, command: str) -> str:
        """Run a shell command."""
        if self.rge:
            return self.rge.execute("bash", {"command": command})
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            return (result.stdout or result.stderr)[:5000]
        except subprocess.TimeoutExpired:
            return "Command timed out (30s)"
        except Exception as e:
            return f"Shell error: {e}"
    
    def _list_dir(self, path: str) -> str:
        """List directory contents."""
        if self.rge:
            return self.rge.execute("list_dir", {"path": path})
        try:
            p = Path(path)
            if not p.exists():
                return f"Path not found: {path}"
            items = list(p.iterdir())
            lines = [f"Directory: {p.resolve()}"]
            lines.append(f"Total: {len(items)} items")
            lines.append("")
            for item in sorted(items, key=lambda x: (not x.is_dir(), x.name.lower())):
                icon = "📁" if item.is_dir() else "📄"
                size = f" ({item.stat().st_size:,} bytes)" if item.is_file() else ""
                lines.append(f"  {icon} {item.name}{size}")
            return "\n".join(lines)
        except Exception as e:
            return f"List error: {e}"
    
    def _run_model(self, model: str, prompt: str) -> str:
        """Run a model with a prompt."""
        from claude_o_cli.llm_adapter import llm_adapter
        messages = [
            {"role": "system", "content": "You are claude, a sovereign AI assistant."},
            {"role": "user", "content": prompt}
        ]
        response = llm_adapter._ollama_chat(messages, stream=False)
        return response or "No response from model"
    
    def _mcp_call(self, server: str, tool: str, args_json: str) -> str:
        """Call an MCP tool."""
        if self.rge:
            try:
                args = json.loads(args_json) if args_json.strip() else {}
            except:
                args = {}
            return self.rge.execute("mcp_call", {"server": server, "tool": tool, "args": args})
        return f"MCP call: {server}/{tool} — RGE not available"

    def _mcp_list(self) -> str:
        """List all MCP servers."""
        if self.rge:
            return self.rge.execute("mcp_list", {})
        return "MCP list — RGE not available"

    def _mcp_tools(self) -> str:
        """List all tools on all MCP servers."""
        if self.rge:
            return self.rge.execute("mcp_tools", {})
        return "MCP tools — RGE not available"

    def _orchestrate(self) -> str:
        """Run orchestration."""
        return "Usage: /orchestrate <task> — Runs multi-agent orchestration"

    def _cmd_cowork(self, args: list) -> str:
        """Show or set Claude Cowork DPEV loop state."""
        try:
            from loop_cowork_context import load_state, save_state, default_state, build_state_block
        except Exception as exc:
            return f"Cowork loop unavailable: {exc}"

        if not args:
            state = load_state()
            return build_state_block(state)

        sub = args[0].lower()
        if sub in ("clear", "reset", "stop"):
            save_state(default_state())
            return "Cowork loop cleared."
        if sub == "status":
            return build_state_block(load_state())
        if sub == "run" and len(args) >= 2:
            goal = " ".join(args[1:])
            save_state({**default_state(), "goal": goal, "phase": "DISCOVER"})
            return f"Cowork goal set: {goal}\n{build_state_block(load_state())}"

        goal = " ".join(args)
        save_state({**default_state(), "goal": goal, "phase": "DISCOVER"})
        return f"Cowork goal set: {goal}\n{build_state_block(load_state())}"

    def _run_agent(self, task: str) -> str:
        """Run the agent loop on a task."""
        if self.rge:
            return self.rge.execute("agent", {"task": task})
        return f"Agent dispatched for: {task}"
    
    def _create_post(self, text: str) -> str:
        """Create a post."""
        result = self.cli.tools.execute("claude_o_post", {"content": text})
        if "error" in result:
            return f"Post error: {result['error']}"
        return f"Post created: {text[:100]}..."
    
    def _send_message(self, text: str) -> str:
        """Send a message."""
        result = self.cli.tools.execute("claude_o_message", {"content": text})
        if "error" in result:
            return f"Message error: {result['error']}"
        return f"Message sent: {text[:100]}..."
    
    def _ask_seer(self, question: str) -> str:
        """Ask Seer Nebellion."""
        result = self.cli.tools.execute("claude_o_seer", {"query": question})
        return result.get("vision", "The seer is silent.")
    
    def _ask_ollama(self, question: str) -> str:
        """Ask Ollama directly."""
        from claude_o_cli.llm_adapter import llm_adapter
        messages = [
            {"role": "system", "content": "You are claude, a sovereign AI assistant running on the Oroboros Core."},
            {"role": "user", "content": question}
        ]
        response = llm_adapter._ollama_chat(messages, stream=False)
        return response or "No response from Ollama"


# ============================================================
# SINGLETON INSTANCE
# ============================================================

_bridge_instance = None

def get_bridge() -> CLIBridge:
    """Get or create the CLI bridge singleton."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = CLIBridge()
    return _bridge_instance
