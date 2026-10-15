#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared host-tool continue cycle — terminal CLI + local_api + Her'Oer + chat.

Single source of truth for:
  parse tool JSON → execute via host_tool_bridge → feed results → continue

Do not leave surfaces on one-shot tool append or demo ok:step executors.
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

TOOL_CALL_RE = re.compile(
    r'\{\s*"tool"\s*:\s*"([^"]+)"\s*,\s*"(?:args|params)"\s*:\s*(\{[\s\S]*?\})\s*\}'
)
# also accept the Anthropic/OpenAI shape: {"name": "...", "arguments": {...}}
TOOL_CALL_RE_ALT = re.compile(
    r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"arguments"\s*:\s*(\{[\s\S]*?\})\s*\}'
)

CONTINUE_PROMPT = (
    "TOOL RESULTS (verified host execution):\n```json\n{results}\n```\n\n"
    "Continue. Emit another {{\"tool\":...}} if needed, or give the final answer "
    "in plain language. Never claim success unless ok:true appears above. "
    "Do not restate the tool JSON as the final answer."
)


def parse_tool_calls(text: str) -> List[Dict[str, Any]]:
    """Extract host tool calls from model/entity text."""
    out: List[Dict[str, Any]] = []
    if not text:
        return out
    for m in TOOL_CALL_RE.finditer(text):
        try:
            out.append({"tool": m.group(1), "args": json.loads(m.group(2))})
        except Exception:
            out.append({"tool": m.group(1), "args": {}, "parseError": True})
    if not out:
        for m in TOOL_CALL_RE_ALT.finditer(text):
            try:
                out.append({"tool": m.group(1), "args": json.loads(m.group(2))})
            except Exception:
                out.append({"tool": m.group(1), "args": {}, "parseError": True})
    if out:
        return out
    t = text.strip()
    if t.startswith("{") and ('"tool"' in t or '"name"' in t):
        try:
            obj = json.loads(t)
            if isinstance(obj, dict) and (obj.get("tool") or obj.get("name")):
                out.append({
                    "tool": obj.get("tool") or obj.get("name"),
                    "args": obj.get("args") or obj.get("params") or obj.get("arguments") or {},
                })
        except Exception:
            tm = re.search(r'"(?:tool|name)"\s*:\s*"([^"]+)"', t)
            if tm:
                out.append({
                    "tool": tm.group(1),
                    "args": {},
                    "parseError": True,
                    "truncated": True,
                })
    return out


def _normalize_args(name: str, args: dict) -> dict:
    """Map Anthropic-style arg names onto the host tools' expected keys."""
    if not isinstance(args, dict):
        return {}
    a = dict(args)
    alias = {
        "file_path": "path", "filename": "path", "filepath": "path",
        "file": "path", "notebook_path": "path",
    }
    for src, dst in alias.items():
        if src in a and dst not in a:
            a[dst] = a.pop(src)
    return a


def _normalize_name(name: str) -> str:
    m = {
        "Read": "read_file", "read": "read_file",
        "Write": "write_file", "write": "write_file",
        "Edit": "write_file", "Bash": "bash", "bash": "bash",
        "Glob": "list_dir", "LS": "list_dir", "ls": "list_dir",
        "Grep": "bash", "Delete": "delete_file",
    }
    return m.get(name, name)


def execute_call(call: Dict[str, Any], *, source: str = "tool_cycle") -> Dict[str, Any]:
    """Run one call through shared host_tool_bridge."""
    name = call.get("tool") or ""
    args = call.get("args") or {}
    if call.get("parseError") or call.get("truncated"):
        return {
            "ok": False,
            "error": "Truncated or invalid tool JSON — re-emit complete call",
            "tool": name,
        }
    name = _normalize_name(name)
    args = _normalize_args(name, args)
    try:
        from claude_o_cli.host_tool_bridge import execute_host_tool
        return execute_host_tool(name, args if isinstance(args, dict) else {}, source=source)
    except Exception as e:
        return {"ok": False, "error": str(e), "tool": name}


def run_tool_continue(
    *,
    initial_reply: str,
    messages: List[Dict[str, str]],
    chat_once: Callable[[List[Dict[str, str]]], str],
    max_loops: int = 6,
    source: str = "tool_cycle",
    on_tool: Optional[Callable[[str, dict, dict], None]] = None,
) -> Dict[str, Any]:
    """Full continue loop. Tool JSON is never treated as a final answer."""
    reply = initial_reply or ""
    msgs = list(messages)
    tool_trace: List[Dict[str, Any]] = []
    rounds = 0

    for _ in range(max(1, max_loops)):
        calls = parse_tool_calls(reply)
        if not calls:
            break
        results = []
        for call in calls:
            tr = execute_call(call, source=source)
            entry = {"tool": call.get("tool"), "args": call.get("args") or {}, "result": tr}
            results.append(entry)
            ok = bool(tr.get("ok", True)) if isinstance(tr, dict) else True
            if isinstance(tr, dict) and tr.get("ok") is False:
                ok = False
            tool_trace.append({"tool": call.get("tool"), "ok": ok})
            if on_tool:
                try:
                    on_tool(str(call.get("tool") or ""), dict(call.get("args") or {}), tr)
                except Exception:
                    pass
        rounds += 1
        msgs.append({"role": "assistant", "content": reply})
        msgs.append({
            "role": "user",
            "content": CONTINUE_PROMPT.format(
                results=json.dumps(results, indent=2, default=str)[:6000]
            ),
        })
        try:
            reply = chat_once(msgs) or ""
        except Exception as e:
            return {
                "final": reply + f"\n\n[tool_cycle continue error: {e}]",
                "tool_trace": tool_trace,
                "tool_rounds": rounds,
                "error": str(e),
            }

    return {
        "final": reply,
        "tool_trace": tool_trace,
        "tool_rounds": rounds,
        "messages": msgs,
    }


def system_fragment() -> str:
    return (
        "TOOL CYCLE — SHARED (terminal · local_api · Her'Oer · local chat)\n"
        "- Tool JSON is NOT a final answer. Host executes → results feed back → continue.\n"
        "- Emit a call as either {\"tool\":\"bash\",\"args\":{...}} or "
        "{\"name\":\"Read\",\"arguments\":{...}}. Both are executed.\n"
        "- Tools: Bash, Read, Write, Edit, Glob, Grep (and MCP tools). "
        "Prefer the host tools.\n"
        "- Backend: claude_o_cli.host_tool_bridge (write_file|read_file|list_dir|delete_file|bash).\n"
        "- LivingLoop + Complete 20-Loop + supervisor autocorrect stay connected each turn.\n"
    )
