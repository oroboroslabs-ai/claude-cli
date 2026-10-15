#!/usr/bin/env python3
"""Smoke test — terminal runtime engine (tools + MCP + boot)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from claude_o_cli.oroboros_core import ToolRegistry, PermissionManager
from claude_o_cli.terminal_runtime import AgenticRuntime, get_runtime
from claude_o_cli.claude_o_cli import _augment_terminal_system


def main() -> int:
    tools = ToolRegistry(PermissionManager())
    rt = get_runtime(tools)
    boot = rt.boot()
    assert boot.get("ok") and boot.get("booted")
    assert boot.get("local_tools", 0) >= 20
    assert "mcp_call" in (boot.get("tool_names") or [])
    print("boot", boot.get("performance_level"), "tools", boot.get("local_tools"),
          "mcp", (boot.get("mcp") or {}).get("count_online"), "/", (boot.get("mcp") or {}).get("count_total"))

    frag = rt.system_fragment()
    assert "RUNTIME ENGINE" in frag or "RUNTIME ACTIVE" in frag
    assert '{"tool"' in frag or '"tool"' in frag

    sys_prompt = _augment_terminal_system(user_turn="runtime smoke", runtime=rt)
    assert "TERMINAL RUNTIME" in sys_prompt or "RUNTIME ACTIVE" in sys_prompt
    assert "LIVE PERCEPTION" in sys_prompt or "ARCHITECT" in sys_prompt or "MAO" in sys_prompt.upper()
    print("augment len", len(sys_prompt))

    call = rt.extract_tool_call('Sure.\n{"tool": "mcp_list", "args": {}}\n')
    assert call and call[0] == "mcp_list"
    print("extract", call[0])
    agent = rt.extract_tool_call('[AGENT:write_file:{"path": "J:/anthropic-local-chat/x.txt", "content": "hi"}]')
    assert agent and agent[0] == "write_file"
    print("extract AGENT", agent[0])
    assert (boot.get("host_control") or {}).get("ok") is True
    print("host_control", boot.get("host_control", {}).get("proof"))

    result = rt.execute_tool("mcp_list", {})
    data = json.loads(result)
    assert "servers" in data
    print("mcp_list servers", len(data["servers"]))

    # If orchestration online, call system_status
    online = (boot.get("mcp") or {}).get("online") or {}
    if online.get("orchestration"):
        out = rt.execute_tool("mcp_call", {
            "server": "orchestration",
            "tool": "system_status",
            "args": {},
        })
        print("mcp_call system_status", out[:240].replace("\n", " "))
        assert "OROBOROS" in out or "result" in out or "content" in out
        assert "HTTP Error 400" not in out
    else:
        print("orchestration offline — skip live mcp_call (start-mcp-lab.ps1)")

    # Local tool still works
    r = rt.execute_tool("list_dir", {"path": str(ROOT)})
    assert "items" in r or "path" in r
    print("list_dir ok")

    print("RUNTIME_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
