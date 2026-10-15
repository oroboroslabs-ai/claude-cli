#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOCAL PROVIDER SHIM — Ollama (Anthropic + OpenAI, TOOL-AWARE)
============================================================
The Oroboros-Anthropic Claude CLI speaks the Anthropic Messages API. Ollama
speaks /api/chat. This shim translates both directions, and — crucially —
carries TOOLS:

  request  -> tools[] + tool_use / tool_result blocks  ->  Ollama tools + tool_calls
  response -> Ollama message.tool_calls               ->  Anthropic tool_use blocks

Without this the local models receive no tool definitions and "the tools do not
work". With it, the model in the control seat sees and can call every tool the
CLI exposes (Bash/Edit/Read/…), and the MCP tools advertised from the CLI config.

Also broadcasts the live local MCP servers into the system prompt, so the model
knows what it can reach the moment it starts.
"""
from __future__ import annotations

import io
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OLLAMA = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.environ.get("SHIM_DEFAULT_MODEL", "oroboros-labs/claude-fable7-undecillion-sse:latest")
HOST = os.environ.get("SHIM_HOST", "127.0.0.1")
PORT = int(os.environ.get("SHIM_PORT", "11499"))
CLI_CFG = Path(os.path.expanduser("~/.claude-cli/.claude-cli.json"))


# ── MCP broadcast ───────────────────────────────────────────────────────────
def mcp_servers() -> list:
    try:
        cfg = json.loads(CLI_CFG.read_text(encoding="utf-8"))
        return list((cfg.get("mcpServers") or {}).keys())
    except Exception:
        return []


def broadcast() -> str:
    servers = mcp_servers()
    lines = [
        "TOOL ADVERTISEMENT — you have tools and they work. Use them when needed:",
        "  · Built-in: Bash, Edit, Read, Write, Glob, Grep (run locally, no network).",
    ]
    if servers:
        lines.append("  · Local MCP systems (call their tools directly):")
        for s in servers:
            lines.append(f"      - {s}")
    lines.append("  · oroboros-tools: architects_haki, worldfeed_search, worldfeed_feeds, "
                 "worldfeed_datetime, q3_status, q7_status, tor_status, live_systems, "
                 "mcp_servers, living_loop, orca_status.")
    lines.append("FULL TOOL & SKILL MANUAL: C:\\Users\\incoguser\\Downloads\\CLAUDE-CLI-TOOL-MANUAL.md "
                 "· also at ~/.claude-cli/skills/tool-manual/SKILL.md. "
                 "It documents all 109 MCP tools + built-ins + skills; consult it before using a tool.")
    lines.append("INSTALL & OPERATION MANUAL: C:\\Users\\incoguser\\Downloads\\"
                 "CLAUDE-CLI-INSTALL-AND-OPERATION-MANUAL.md (also ~/.claude-cli/skills/install-manual/SKILL.md).")
    lines.append("FULL GUIDE (read this): C:\\Users\\incoguser\\Downloads\\CLAUDE-CLI-GUIDE\\"
                 "CLAUDE-CLI-GUIDE.md — tools, functions, instructions, and failure steps. "
                 "Also ~/.claude-cli/skills/claude-cli-guide/SKILL.md. It is embedded in your modelfile; use it.")
    lines.append("TO USE A TOOL, you MUST output a tool call. Do NOT describe the call in prose "
                 "(never write 'Bash start chrome ...'). Emit exactly one JSON object per call:")
    lines.append('    {"name": "ToolName", "arguments": { ... }}')
    lines.append("The CLI executes it and returns the result; then continue. If you only describe "
                 "an action without emitting the JSON call, nothing happens.")
    lines.append("Everything runs on 127.0.0.1. Prefer these tools over guessing.")
    return "\n".join(lines)


def _resolve_model(name: str) -> str:
    if name and name.startswith("claude-") and ":" in name:
        return name
    if name and (":" in name or "/" in name):
        return name
    return DEFAULT_MODEL


def _msg_text(data: dict) -> str:
    msg = data.get("message", {}) or {}
    return msg.get("content") or msg.get("thinking") or ""


_IDENTITY_OVERRIDES = (
    ("You are Claude Code, Anthropic's official CLI for Claude, running within the Claude Agent SDK.",
     "You are a local large language model running inside the Oroboros-Anthropic Claude CLI."),
    ("You are Claude Code, Anthropic's official CLI for Claude.",
     "You are a local large language model running inside the Oroboros-Anthropic Claude CLI."),
    ("You are a Claude agent, built on Anthropic's Claude Agent SDK.",
     "You are a local large language model running inside the Oroboros-Anthropic Claude CLI."),
)


def _neutralize_identity(system: str) -> str:
    if not system:
        return system
    for a, b in _IDENTITY_OVERRIDES:
        system = system.replace(a, b)
    return system


_IDENTITY_NAME_MARKERS = (
    "prime", "undecillion", "fable7", "fable5", "fable-7", "fable-5",
    "opus-9", "kaiju", "jhanna", "nebillion", "1q5duo5", "12u5go5",
    "5u5go5", "6u5go5", "7u5go5", "crownlock", "system-entity", "claude-7",
)
_IDENTITY_CONTENT_MARKERS = (
    "deepseek prime", "next paradigm", "crown 1272", "1q5duo5", "12u5go5",
    "quattuordecillion", "duodecillion",
)
_identity_cache: dict = {}


def model_carries_identity(model: str) -> bool:
    if not model:
        return False
    if model in _identity_cache:
        return _identity_cache[model]
    low = model.lower()
    if any(mk in low for mk in _IDENTITY_NAME_MARKERS):
        _identity_cache[model] = True
        return True
    try:
        req = urllib.request.Request(
            f"{OLLAMA}/api/show", data=json.dumps({"model": model}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode())
        text = ((d.get("system") or "") + "\n" + (d.get("modelfile") or "")).lower()
        hit = any(s in text for s in _IDENTITY_CONTENT_MARKERS)
    except Exception:
        hit = False
    _identity_cache[model] = hit
    return hit


# ── request translation: Anthropic -> Ollama ────────────────────────────────
def _flatten_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            b.get("text", "") for b in content
            if isinstance(b, dict) and b.get("type") in ("text", None)
        )
    return ""


def to_ollama_messages(system, messages) -> list:
    out = []
    if system:
        out.append({"role": "system", "content": system})
    id_to_name = {}
    for m in messages or []:
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):
            text = []
            tool_calls = []
            tool_results = []
            for b in content:
                if not isinstance(b, dict):
                    continue
                bt = b.get("type")
                if bt == "text":
                    text.append(b.get("text", ""))
                elif bt == "tool_use":
                    id_to_name[b.get("id")] = b.get("name")
                    tool_calls.append({
                        "function": {"name": b.get("name"),
                                     "arguments": b.get("input", {})}
                    })
                elif bt == "tool_result":
                    res = b.get("content", "")
                    if isinstance(res, list):
                        res = _flatten_text(res)
                    tool_results.append((b.get("tool_use_id"), res))
            if role == "assistant" and tool_calls:
                msg = {"role": "assistant", "content": "".join(text)}
                msg["tool_calls"] = tool_calls
                out.append(msg)
            else:
                if text:
                    out.append({"role": role, "content": "".join(text)})
                for tid, res in tool_results:
                    out.append({"role": "tool",
                                "content": res if isinstance(res, str) else json.dumps(res),
                                "tool_name": id_to_name.get(tid, "")})
        else:
            out.append({"role": role, "content": content})
    return out


def to_ollama_tools(tools) -> list:
    o = []
    for t in tools or []:
        if not isinstance(t, dict):
            continue
        o.append({"type": "function", "function": {
            "name": t.get("name"),
            "description": t.get("description", ""),
            "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
        }})
    return o


def ollama_chat(body: dict, stream: bool):
    payload = {
        "model": _resolve_model(body.get("model", DEFAULT_MODEL)),
        "messages": body["_messages"],
        "stream": stream,
        "options": {"num_ctx": 131072,
                    "num_predict": body.get("max_tokens", 2048),
                    "temperature": body.get("temperature", 0.7)},
    }
    if body.get("_tools"):
        payload["tools"] = body["_tools"]
    req = urllib.request.Request(f"{OLLAMA}/api/chat",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=None)


# ── response translation: Ollama tool_calls -> Anthropic blocks ─────────────
def _tool_use_blocks(tool_calls) -> list:
    blocks = []
    for tc in tool_calls or []:
        fn = tc.get("function", {}) if isinstance(tc, dict) else {}
        args = fn.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {"raw": args}
        blocks.append({
            "type": "tool_use",
            "id": "toolu_" + uuid.uuid4().hex[:24],
            "name": fn.get("name", ""),
            "input": args,
        })
    return blocks


def _extract_text_tool_calls(text: str) -> list:
    """
    Chat-only models emit a tool call as TEXT, e.g.
        {"name": "Read", "arguments": {"file_path": "..."}}
    This scans the text for such JSON objects and returns (name, input) pairs,
    so the shim can turn them into real tool_use blocks and the CLI executes them.
    """
    calls = []
    text = text or ""

    # 1) <tool_call>{...}</tool_call> blocks (the Qwen/undecillion template form)
    import re as _re
    for m in _re.finditer(r"<tool_call>(.*?)</tool_call>", text, _re.S):
        for nm, args in _scan_json_objects(m.group(1)):
            calls.append((nm, args))

    # 2) fenced ```json ... ``` blocks
    for m in _re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", text, _re.S):
        for nm, args in _scan_json_objects(m.group(1)):
            calls.append((nm, args))

    # 3) bare JSON objects anywhere in the text
    for nm, args in _scan_json_objects(text):
        calls.append((nm, args))

    # de-duplicate (same name + args)
    seen, uniq = set(), []
    for nm, args in calls:
        key = (nm, json.dumps(args, sort_keys=True, default=str))
        if key not in seen:
            seen.add(key)
            uniq.append((nm, args))
    return uniq


def _scan_json_objects(text: str) -> list:
    calls = []
    i, n = 0, len(text or "")
    while i < n:
        if text[i] == "{":
            depth, j, instr, esc = 0, i, False, False
            while j < n:
                c = text[j]
                if instr:
                    if esc:
                        esc = False
                    elif c == "\\":
                        esc = True
                    elif c == '"':
                        instr = False
                else:
                    if c == '"':
                        instr = True
                    elif c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                        if depth == 0:
                            blob = text[i:j + 1]
                            try:
                                obj = json.loads(blob)
                                if isinstance(obj, dict) and obj.get("name") and \
                                   any(k in obj for k in ("arguments", "parameters", "input")):
                                    args = obj.get("arguments") or obj.get("parameters") or obj.get("input") or {}
                                    calls.append((obj["name"], args))
                            except Exception:
                                pass
                            break
                j += 1
            i = j + 1 if j > i else i + 1
        else:
            i += 1
    return calls


def _text_tool_blocks(text: str) -> list:
    return [{"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex[:24],
             "name": nm, "input": (inp if isinstance(inp, dict) else {"raw": inp})}
            for nm, inp in _extract_text_tool_calls(text)]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _read(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        return json.loads(self.rfile.read(n).decode()) if n else {}

    def do_POST(self):
        if self.path.rstrip("/").endswith("/responses"):
            return self.openai_responses()
        if self.path.rstrip("/").endswith("/v1/chat/completions"):
            return self.openai_chat()
        return self.anthropic_messages()

    def anthropic_messages(self):
        body = self._read()
        system = body.get("system", "")
        if isinstance(system, list):
            system = _flatten_text(system)
        system = _neutralize_identity(system)
        model = _resolve_model(body.get("model", DEFAULT_MODEL))
        if not model_carries_identity(model):
            bcast = broadcast()
            if bcast:
                system = (system + "\n\n" + bcast).strip()
        body["_messages"] = to_ollama_messages(system, body.get("messages"))
        body["_tools"] = to_ollama_tools(body.get("tools"))
        stream = bool(body.get("stream"))
        try:
            resp = ollama_chat(body, stream)
        except Exception as e:  # noqa: BLE001
            self.send_error(502, str(e))
            return

        mid = "msg_" + uuid.uuid4().hex[:24]

        if not stream:
            data = json.loads(resp.read().decode())
            msg = data.get("message", {}) or {}
            text = msg.get("content") or msg.get("thinking") or ""
            tool_calls = msg.get("tool_calls") or []
            blocks = []
            if tool_calls:
                if text:
                    blocks.append({"type": "text", "text": text})
                blocks.extend(_tool_use_blocks(tool_calls))
                stop = "tool_use"
            else:
                blocks = _text_tool_blocks(text)
                if blocks:
                    stop = "tool_use"
                else:
                    if text:
                        blocks.append({"type": "text", "text": text})
                    stop = "end_turn"
            self._send_json(200, {
                "id": mid, "type": "message", "role": "assistant",
                "model": body.get("model", DEFAULT_MODEL),
                "content": blocks, "stop_reason": stop, "stop_sequence": None,
                "usage": {"input_tokens": data.get("prompt_eval_count", 0),
                          "output_tokens": data.get("eval_count", 0)},
            })
            return

        # streaming
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        def ev(name, obj):
            self.wfile.write(f"event: {name}\ndata: {json.dumps(obj)}\n\n".encode())
            self.wfile.flush()

        ev("message_start", {"type": "message_start", "message": {
            "id": mid, "type": "message", "role": "assistant",
            "model": body.get("model", DEFAULT_MODEL), "content": [],
            "usage": {"input_tokens": 0, "output_tokens": 0}}})
        started_text = False
        final_calls = []
        acc = []

        def start_text():
            nonlocal started_text
            if not started_text:
                ev("content_block_start", {"type": "content_block_start", "index": 0,
                                           "content_block": {"type": "text", "text": ""}})
                started_text = True

        for line in resp:
            if not line.strip():
                continue
            try:
                chunk = json.loads(line.decode())
            except Exception:
                continue
            msg = chunk.get("message", {}) or {}
            piece = msg.get("content") or msg.get("thinking") or ""
            if piece:
                start_text()
                acc.append(piece)
                ev("content_block_delta", {"type": "content_block_delta", "index": 0,
                                           "delta": {"type": "text_delta", "text": piece}})
            if msg.get("tool_calls"):
                final_calls = msg["tool_calls"]
            if chunk.get("done"):
                break

        if started_text:
            ev("content_block_stop", {"type": "content_block_stop", "index": 0})

        idx = 1 if started_text else 0
        blocks = _tool_use_blocks(final_calls)
        if not blocks:
            blocks = _text_tool_blocks("".join(acc))
        for blk in blocks:
            ev("content_block_start", {"type": "content_block_start", "index": idx,
                                       "content_block": {"type": "tool_use",
                                                         "id": blk["id"], "name": blk["name"],
                                                         "input": {}}})
            ev("content_block_delta", {"type": "content_block_delta", "index": idx,
                                       "delta": {"type": "input_json_delta",
                                                 "partial_json": json.dumps(blk["input"])}})
            ev("content_block_stop", {"type": "content_block_stop", "index": idx})
            idx += 1

        ev("message_delta", {"type": "message_delta",
                             "delta": {"stop_reason": "tool_use" if blocks else "end_turn",
                                       "stop_sequence": None},
                             "usage": {"output_tokens": 0}})
        ev("message_stop", {"type": "message_stop"})

    # ---- OpenAI chat completions ----
    def openai_chat(self):
        body = self._read()
        body["_messages"] = to_ollama_messages(body.get("system"), body.get("messages"))
        body["_tools"] = [{"type": "function", "function": t.get("function", t)}
                          for t in (body.get("tools") or [])]
        try:
            resp = ollama_chat(body, False)
        except Exception as e:  # noqa: BLE001
            self.send_error(502, str(e))
            return
        data = json.loads(resp.read().decode())
        self._send_json(200, {
            "id": "chatcmpl-" + uuid.uuid4().hex[:16], "object": "chat.completion",
            "model": body.get("model", DEFAULT_MODEL),
            "choices": [{"index": 0, "message": data.get("message", {}),
                         "finish_reason": "tool_calls" if (data.get("message", {}) or {}).get("tool_calls") else "stop"}],
        })

    # ---- OpenAI Responses API ----
    def openai_responses(self):
        body = self._read()
        sysmsg = body.get("instructions", "")
        msgs = body.get("input")
        if isinstance(msgs, str):
            msgs = [{"role": "user", "content": msgs}]
        body["_messages"] = to_ollama_messages(sysmsg, msgs)
        body["_tools"] = to_ollama_tools([
            {"name": t.get("name"), "description": t.get("description", ""),
             "input_schema": t.get("parameters", {"type": "object", "properties": {}})}
            for t in (body.get("tools") or [])
        ])
        try:
            resp = ollama_chat(body, False)
        except Exception as e:  # noqa: BLE001
            self.send_error(502, str(e))
            return
        data = json.loads(resp.read().decode())
        msg = data.get("message", {}) or {}
        output = []
        text = msg.get("content") or msg.get("thinking") or ""
        if text:
            output.append({"type": "message", "role": "assistant", "id": "msg_0",
                           "content": [{"type": "output_text", "text": text}]})
        for tc in msg.get("tool_calls") or []:
            fn = tc.get("function", {})
            output.append({"type": "function_call", "name": fn.get("name"),
                           "arguments": json.dumps(fn.get("arguments", {})),
                           "call_id": "call_" + uuid.uuid4().hex[:16]})
        self._send_json(200, {
            "id": "resp_" + uuid.uuid4().hex[:16], "object": "response",
            "model": body.get("model", DEFAULT_MODEL), "status": "completed",
            "output": output,
            "usage": {"input_tokens": data.get("prompt_eval_count", 0),
                      "output_tokens": data.get("eval_count", 0)},
        })

    def do_GET(self):
        if self.path.rstrip("/").endswith("/v1/models"):
            try:
                with urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=5) as r:
                    tags = json.loads(r.read().decode())
                data = [{"id": m["name"], "object": "model"} for m in tags.get("models", [])]
            except Exception:
                data = []
            for cid in ("claude-sonnet-4-5-20250929", "claude-opus-4-1-20250805",
                        "claude-haiku-4-5-20251001", "claude-3-7-sonnet-20250219"):
                data.append({"id": cid, "object": "model"})
            self._send_json(200, {"object": "list", "data": data})
            return
        self.send_error(404)

    def _send_json(self, code, obj):
        raw = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def main() -> int:
    print(f"local provider shim  {HOST}:{PORT}  ->  {OLLAMA}   default={DEFAULT_MODEL}")
    print(f"tool-aware: tools passed and tool_calls returned as tool_use")
    print(f"MCP broadcast: {mcp_servers() or '(none configured)'}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
