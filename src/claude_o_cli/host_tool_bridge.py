"""Shared host-tool backend for terminal CLI + HTML CLI UI + local chat 8787.

Canonical executor: claude_o_cli.oroboros_core.ToolRegistry (same as terminal chat).
Surfaces:
  - Terminal CLI (cmd_chat / AgenticRuntime)
  - HTML CLI UI (run_cli.py :5000 /api/host/tool + /api/chat tool loop)
  - Local chat (8787 /api/host/tool → this module via python)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

BRIDGE_LOG = Path(r"J:/anthropic-local-chat/host-tool-bridge.log.jsonl")
STATE_PATH = Path(r"J:/anthropic-local-chat/host-tool-bridge-state.json")

HOST_TOOL_NAMES = frozenset({
    "write_file", "read_file", "list_dir", "delete_file", "bash",
    "write", "read", "ls", "dir", "shell", "cmd", "powershell", "delete", "rm",
})

_ALIASES = {
    "write": "write_file",
    "read": "read_file",
    "ls": "list_dir",
    "dir": "list_dir",
    "shell": "bash",
    "cmd": "bash",
    "powershell": "bash",
    "delete": "delete_file",
    "rm": "delete_file",
}

_permissions = None
_tools = None
_event_count = 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def alias_tool(name: str) -> str:
    key = (name or "").strip()
    return _ALIASES.get(key.lower(), key)


def get_shared_permissions():
    global _permissions
    if _permissions is None:
        from claude_o_cli.oroboros_core import PermissionManager
        _permissions = PermissionManager()
    return _permissions


def get_shared_tools():
    """Singleton ToolRegistry — terminal CLI and HTTP surfaces share this code path."""
    global _tools
    if _tools is None:
        from claude_o_cli.oroboros_core import ToolRegistry
        _tools = ToolRegistry(get_shared_permissions())
        try:
            from claude_o_cli.mesh_intel import register_mesh_tools
            register_mesh_tools(_tools)
        except Exception:
            pass
    return _tools


def status(*, source: str = "status") -> dict:
    tools = get_shared_tools()
    names = [t["name"] for t in tools.list_tools()]
    return {
        "ok": True,
        "connected": True,
        "backend": "claude_o_cli.host_tool_bridge",
        "canonical": "oroboros_core.ToolRegistry",
        "sandbox": False,
        "container": False,
        "all_drives": True,
        "mcp_required": False,
        "agent_tags_required": False,
        "surfaces": [
            "terminal_cli",
            "html_cli_ui:5000",
            "local_chat:8787",
            "q_chat_anthropic_html",
            "mesh_intel",
        ],
        "mesh": {
            "q3": "http://127.0.0.1:8000",
            "q5": "http://127.0.0.1:8101",
            "q6": "mesh://q6_acquisition",
            "worldfeed": "http://127.0.0.1:8100",
            "tor": "socks5://127.0.0.1:9050",
            "spy_network": True,
            "mao_haki": True,
            "architects_haki": True,
        },
        "tools": names,
        "host_tools": sorted(n for n in names if n in (
            "write_file", "read_file", "list_dir", "delete_file", "bash"
        )),
        "mesh_tools": sorted(n for n in names if n in (
            "q3_route", "q5_query", "q6_query", "worldfeed_live", "tor_status", "tor_connect",
            "spy_network", "mesh_status", "q3", "route_q3", "q5", "q6", "worldfeed",
            "world_feed", "worldfeed_context", "tor", "spy", "mesh", "haki_status",
        )),
        "events": _event_count,
        "source": source,
        "state_file": str(STATE_PATH),
        "protocol": '{"tool":"write_file","args":{"path":"J:\\\\note.txt","content":"hello"}}',
        "at": _now(),
    }


def _log_event(record: dict) -> None:
    try:
        BRIDGE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with BRIDGE_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
        STATE_PATH.write_text(json.dumps({
            "ok": True,
            "last": record,
            "events": _event_count,
            "at": _now(),
        }, indent=2), encoding="utf-8")
    except Exception:
        pass


def execute_host_tool(
    tool: str,
    args: Optional[dict] = None,
    *,
    source: str = "unknown",
) -> dict:
    """Execute a host tool through the shared CLI ToolRegistry."""
    global _event_count
    name = alias_tool(tool)
    args = args or {}
    tools = get_shared_tools()
    raw = tools.execute(name, args)
    _event_count += 1

    if isinstance(raw, dict):
        out = dict(raw)
    else:
        out = {"ok": True, "result": raw}

    out.setdefault("tool", name)
    out["host"] = True
    out["sandbox"] = False
    out["backend"] = "claude_o_cli.host_tool_bridge"
    out["source"] = source
    out["connected_surfaces"] = ["terminal_cli", "html_cli_ui", "local_chat"]

    _log_event({
        "at": _now(),
        "source": source,
        "tool": name,
        "args_keys": sorted(list(args.keys())),
        "ok": out.get("ok", "error" not in out),
        "path": args.get("path"),
    })
    return out


def execute_payload(payload: dict, *, source: str = "unknown") -> dict:
    """Accept Express-sketch or CLI shapes."""
    if not isinstance(payload, dict):
        return {"ok": False, "error": "payload must be an object"}
    cmd = payload
    if isinstance(payload.get("message"), dict) and payload["message"].get("tool"):
        cmd = payload["message"]
    tool = cmd.get("tool") or payload.get("tool")
    args = cmd.get("args") or cmd.get("params") or payload.get("args") or payload.get("params") or {}
    if not tool:
        return {
            "ok": False,
            "error": 'Missing tool. Expected {"tool":"write_file","args":{...}}',
        }
    return execute_host_tool(str(tool), dict(args) if isinstance(args, dict) else {}, source=source)


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Shared Oroboros host tool bridge (CLI canonical)")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--tool", type=str, default="")
    parser.add_argument("--args", type=str, default="{}")
    parser.add_argument("--source", type=str, default="cli_argv")
    parser.add_argument("--stdin", action="store_true", help="Read JSON payload from stdin")
    parser.add_argument("--file", type=str, default="", help="Read JSON payload from a file")
    args = parser.parse_args(argv)

    if args.status:
        print(json.dumps(status(source=args.source), indent=2))
        return 0

    if args.file:
        payload = json.loads(Path(args.file).read_text(encoding="utf-8"))
        print(json.dumps(execute_payload(payload, source=args.source), indent=2, default=str))
        return 0

    if args.stdin:
        payload = json.loads(sys.stdin.read() or "{}")
        print(json.dumps(execute_payload(payload, source=args.source), indent=2, default=str))
        return 0

    if not args.tool:
        parser.error("provide --tool, --stdin, --file, or --status")
    tool_args = json.loads(args.args or "{}")
    print(json.dumps(execute_host_tool(args.tool, tool_args, source=args.source), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
