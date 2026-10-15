#!/usr/bin/env python3
"""Local stdio MCP bridge for Claude CLI tools and the Orca CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) in sys.path:
    sys.path.remove(str(_SRC))
sys.path.insert(0, str(_SRC))

from claude_o_cli.host_tool_bridge import get_shared_tools
from claude_o_cli.orca_cli_tool import ORCA_CLI_SCHEMA, run_orca_cli


def _tool_specs() -> list[dict]:
    registry = get_shared_tools()
    tools = []
    for tool in registry.tools.values():
        tools.append({
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.input_schema or {"type": "object", "properties": {}},
        })
    tools.append({
        "name": "orca_cli",
        "description": (
            "Run any Orca CLI command locally with argv (no shell). Use "
            "argv [\"agent-context\", \"--json\"] to inspect the full command schema."
        ),
        "inputSchema": ORCA_CLI_SCHEMA,
    })
    return tools


def _response(request_id, result=None, error=None) -> dict:
    message = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        message["error"] = error
    else:
        message["result"] = result
    return message


def _handle(message: dict) -> dict | None:
    method = message.get("method")
    request_id = message.get("id")
    if request_id is None:
        return None

    if method == "initialize":
        params = message.get("params") or {}
        return _response(request_id, {
            "protocolVersion": params.get("protocolVersion", "2024-11-05"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "claude-orca-local-bridge", "version": "1.0.0"},
        })
    if method == "ping":
        return _response(request_id, {})
    if method == "tools/list":
        return _response(request_id, {"tools": _tool_specs()})
    if method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        if not isinstance(name, str) or not isinstance(args, dict):
            return _response(request_id, error={
                "code": -32602,
                "message": "tools/call requires a tool name and object arguments",
            })
        try:
            if name == "orca_cli":
                result = run_orca_cli(args)
            else:
                registry = get_shared_tools()
                if registry.get(name) is None:
                    result = {"error": f"Unknown Claude CLI tool: {name}"}
                else:
                    result = registry.execute(name, args)
        except Exception as exc:
            result = {"error": f"Tool call failed: {exc}"}
        is_error = isinstance(result, dict) and (
            "error" in result or result.get("exit_code", 0) != 0
        )
        return _response(request_id, {
            "content": [{
                "type": "text",
                "text": json.dumps(result, ensure_ascii=False, default=str),
            }],
            "isError": is_error,
        })
    if method == "resources/list":
        return _response(request_id, {"resources": []})
    if method == "prompts/list":
        return _response(request_id, {"prompts": []})
    return _response(request_id, error={
        "code": -32601,
        "message": f"Unsupported MCP method: {method}",
    })


def main() -> None:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = _handle(request)
            if response is not None:
                sys.stdout.write(json.dumps(response, ensure_ascii=False, default=str) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError as exc:
            sys.stdout.write(json.dumps(_response(None, error={
                "code": -32700,
                "message": f"Invalid JSON: {exc}",
            })) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
