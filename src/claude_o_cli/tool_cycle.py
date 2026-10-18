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

# THE FAKE-SUCCESS LAW: a reply may never claim host writes/commands that
# never produced ok:true. Detected here; surfaces force a corrective turn.
FAKE_SUCCESS_RE = re.compile(
    r"(file (was|has been) (successfully )?writ|successfully written|"
    r"saved? successfully|executing\s*`?write_file`?|writing to file)",
    re.IGNORECASE,
)


def looks_like_fake_success(text: str) -> bool:
    return bool(text) and bool(FAKE_SUCCESS_RE.search(text))


FAKE_SUCCESS_CORRECTION = (
    "CORRECTION — no tool executed in that turn: no ok:true result exists, so "
    "nothing you described ran. The example in your tool instructions is FORMAT "
    "ONLY — never write it, never narrate it as done. Either emit the real "
    "tool JSON now or answer plainly without claiming any success."
)


def _balanced_json_spans(text: str):
    """THE ROBUST SCANNER — find every balanced {...} in the text (string-aware:
    quotes/escapes respected), the truncation-proof replacement for the old
    regex pairs. Yields raw JSON strings."""
    n = len(text)
    i = 0
    while i < n:
        ch = text[i]
        if ch == "{":
            depth = 0
            in_str = False
            esc = False
            j = i
            while j < n:
                c = text[j]
                if in_str:
                    if esc:
                        esc = False
                    elif c == "\\":
                        esc = True
                    elif c == '"':
                        in_str = False
                else:
                    if c == '"':
                        in_str = True
                    elif c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                        if depth == 0:
                            yield text[i:j + 1]
                            i = j
                            break
                j += 1
        i += 1


def parse_tool_calls(text: str) -> List[Dict[str, Any]]:
    """Extract host tool calls from model/entity text — truncation-proof:
    scans every balanced {...} that carries a tool/name key."""
    out: List[Dict[str, Any]] = []
    if not text:
        return out
    alt_names = {"Read", "Write", "Edit", "Bash", "Glob", "Grep", "LS"}

    def _loads_sanitized(span: str):
        r"""THE WINDOWS-PATH PASS: a call like {"path":"Q:\x"} carries \x = an
        invalid JSON escape - json.loads dies on every real house path. One
        sanitize (\x -> \\x) turns the calls real; that was the day's loop."""
        try:
            return json.loads(span)
        except Exception:
            fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', span)
            fixed = fixed.replace("\\`", "`")
            return json.loads(fixed)

    for span in _balanced_json_spans(text):
        if '"tool"' not in span and '"name"' not in span:
            continue
        try:
            obj = _loads_sanitized(span)
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        name = obj.get("tool") or obj.get("name")
        if not name or not isinstance(name, str):
            continue
        if name in ("tool", "name", "args", "arguments"):
            continue
        args = obj.get("args") or obj.get("params") or obj.get("arguments") or {}
        # THE FORMAT-DOC GUARD: a bare format mention (no args, not an argless
        # tool) = the model reading its instructions, not calling — skip it.
        EMPTY_ARGS_OK = {
            "claude_o_status", "system_scan", "mcp_servers", "mesh_status",
            "haki_status", "tor_status", "tor_connect", "docker_ps",
            "docker_images", "docker_logs", "ollama_models", "precogs",
            "skills_list", "cordis_list", "nullframe_vault", "wan_status",
        }
        if not args and name not in EMPTY_ARGS_OK:
            continue
        out.append({"tool": name, "args": args})
    if out:
        return out
    # last resort: a regex pass for malformed-ish calls (keep the old behaviour)
    for m in TOOL_CALL_RE.finditer(text):
        try:
            out.append({"tool": m.group(1), "args": json.loads(m.group(2))})
        except Exception:
            out.append({"tool": m.group(1), "args": {}, "parseError": True})
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
    """Run one call through the CANONICAL entry (execute_payload handles the
    registry + the production gateways — premiere/call_api/orca included)."""
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
        from claude_o_cli.host_tool_bridge import execute_payload
        return execute_payload({"tool": name, "args": args if isinstance(args, dict) else {}}, source=source)
    except Exception as e:
        return {"ok": False, "error": str(e), "tool": name}


def _brief_args(args: Dict[str, Any], cap: int = 220) -> Dict[str, Any]:
    """UI-safe argument preview (long content fields are cut)."""
    out = {}
    for k, v in (args or {}).items():
        s = str(v)
        out[k] = s[:cap] + ("…" if len(s) > cap else "")
    return out


def _brief_result(tr: Any, cap: int = 700) -> Any:
    """UI-safe result preview for the trace panel."""
    if isinstance(tr, dict):
        out = {}
        for k, v in tr.items():
            if k in ("stdout", "content", "result", "output", "answer", "text") and v is not None:
                s = str(v)
                out[k] = s[:cap] + ("…" if len(s) > cap else "")
            else:
                s = str(v)
                out[k] = s[:160] + ("…" if len(s) > 160 else "")
        return out
    s = str(tr)
    return s[:cap]


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
            tool_trace.append({
                "tool": call.get("tool"),
                "ok": ok,
                "args": _brief_args(call.get("args") or {}),
                "result": _brief_result(tr),
            })
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
