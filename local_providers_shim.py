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
import time
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


def _content_str(content) -> str:
    """Flatten OpenAI message content (string or block list) to plain text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, str):
                parts.append(b)
            elif isinstance(b, dict):
                if "text" in b:
                    parts.append(b["text"])
                elif b.get("type") in ("output_text", "input_text", "refusal"):
                    parts.append(b.get("text", ""))
                elif b.get("type") == "tool_result":
                    parts.append(_content_str(b.get("content")))
        return "".join(parts)
    return str(content)


def _output_text(output: list) -> str:
    parts = []
    for item in output or []:
        if isinstance(item, dict) and item.get("type") == "message":
            for c in item.get("content") or []:
                if isinstance(c, dict) and c.get("type") == "output_text":
                    parts.append(c.get("text", ""))
    return "".join(parts)


def _strip_embedded_calls(text: str) -> str:
    """Remove tool-call JSON emitted as prose (tool_call tag blocks and fenced json blocks)
    so an answer does not repeat a call it already made in-band."""
    import re as _re
    text = text or ""
    text = _re.sub("<tool_call>.*?</tool_call>", "", text, flags=_re.S)
    text = _re.sub("```(?:json)?\\s*\\{.*?\\}\\s*```", "", text, flags=_re.S)
    return text.strip()



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
        omsg = body.get("messages") or []
        conv = []
        for m in omsg:
            if not isinstance(m, dict):
                continue
            if m.get("role") == "tool":
                conv.append({"role": "tool",
                             "content": _content_str(m.get("content")),
                             "tool_name": m.get("name", m.get("tool_call_id", ""))})
            elif m.get("role") == "assistant" and m.get("tool_calls"):
                calls = []
                for tc in m["tool_calls"]:
                    fn = tc.get("function", {}) or {}
                    args = fn.get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {"raw": args}
                    calls.append({"function": {"name": fn.get("name", ""), "arguments": args}})
                msg = {"role": "assistant", "content": m.get("content") or ""}
                msg["tool_calls"] = calls
                conv.append(msg)
            else:
                conv.append({"role": m.get("role", "user"),
                             "content": _content_str(m.get("content"))})
        body["_messages"] = conv
        body["_tools"] = [{"type": "function", "function": t.get("function", t)}
                          for t in (body.get("tools") or []) if isinstance(t, dict)]
        stream = bool(body.get("stream"))
        try:
            resp = ollama_chat(body, stream)
        except Exception as e:  # noqa: BLE001
            self.send_error(502, str(e))
            return

        cid = "chatcmpl-" + uuid.uuid4().hex[:16]
        if not stream:
            data = json.loads(resp.read().decode())
            msg = data.get("message", {}) or {}
            raw_mc = msg.get("content") or ""
            calls = msg.get("tool_calls") or []
            if not calls and isinstance(raw_mc, str):
                parsed = _tool_use_blocks(_text_tool_blocks(raw_mc))
                # text-embedded calls from chat-only templates -> real tool_calls
                if parsed:
                    calls = [{"function": {"name": b["name"], "arguments": b["input"]}}
                             for b in parsed]
                    raw_mc = _strip_embedded_calls(raw_mc)
            if calls:
                msg = dict(msg)
                msg["tool_calls"] = [{"type": "function",
                                      "id": "call_" + uuid.uuid4().hex[:16],
                                      "function": {"name": c.get("function", {}).get("name", ""),
                                                   "arguments": json.dumps(c.get("function", {}).get("arguments", {}))}}
                                     for c in calls]
            self._send_json(200, {
                "id": cid, "object": "chat.completion",
                "model": body.get("model", DEFAULT_MODEL),
                "choices": [{"index": 0, "message": msg,
                             "finish_reason": "tool_calls" if calls else "stop"}],
                "usage": {"prompt_tokens": data.get("prompt_eval_count", 0),
                          "completion_tokens": data.get("eval_count", 0)},
            })
            return

        # streaming (OpenAI chat chunk format)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        def sevt(obj):
            self.wfile.write(f"data: {json.dumps(obj)}\n\n".encode())
            self.wfile.flush()

        acc = []
        final_calls = []
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
                acc.append(piece)
                sevt({"id": cid, "object": "chat.completion.chunk",
                      "model": body.get("model", DEFAULT_MODEL),
                      "choices": [{"index": 0, "delta": {"content": piece}, "finish_reason": None}]})
            if msg.get("tool_calls"):
                final_calls = msg["tool_calls"]
            if chunk.get("done"):
                break
        fr = "tool_calls" if final_calls else "stop"
        sevt({"id": cid, "object": "chat.completion.chunk",
              "model": body.get("model", DEFAULT_MODEL),
              "choices": [{"index": 0, "delta": {}, "finish_reason": fr}]})
        sevt("[DONE]")
        if final_calls:
            _ = _strip_embedded_calls  # streaming tool path uses native tool_calls
        _ = acc

    # ---- OpenAI Responses API ----
    def openai_responses(self):
        body = self._read()
        sysmsg = body.get("instructions", "")
        raw_items = body.get("input")
        if isinstance(raw_items, str):
            items = [{"role": "user", "content": raw_items}]
        else:
            items = raw_items or []
        conv, call_names = [], {}
        for it in items:
            if not isinstance(it, dict):
                continue
            t = it.get("type")
            if t == "function_call" or (t is None and it.get("call_id") and it.get("name")):
                args = it.get("arguments", "{}")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {"raw": args}
                cid = it.get("call_id") or ("call_" + uuid.uuid4().hex[:16])
                call_names[cid] = it.get("name", "")
                m = {"role": "assistant", "content": it.get("content") or ""}
                m["tool_calls"] = [{"function": {"name": it.get("name", ""), "arguments": args}}]
                conv.append(m)
            elif t == "function_call_output":
                cid = it.get("call_id", "")
                conv.append({"role": "tool",
                             "content": _content_str(it.get("output")),
                             "tool_name": call_names.get(cid, "")})
            elif t == "message" or t is None:
                conv.append({"role": it.get("role", "user"),
                             "content": _content_str(it.get("content"))})
            elif t in ("reasoning", "reasoning_item", "web_search_call", "local_shell_call"):
                continue
        body["_messages"] = conv
        body["_tools"] = to_ollama_tools([
            {"name": t.get("name"), "description": t.get("description", ""),
             "input_schema": t.get("parameters", {"type": "object", "properties": {}})}
            for t in (body.get("tools") or []) if isinstance(t, dict)
        ])
        stream = bool(body.get("stream"))
        try:
            resp = ollama_chat(body, stream)
        except Exception as e:  # noqa: BLE001
            self.send_error(502, str(e))
            return

        rid = "resp_" + uuid.uuid4().hex[:16]

        def build_output(msg):
            out = []
            text = msg.get("content") or msg.get("thinking") or ""
            parsed_ai = _tool_use_blocks(_text_tool_blocks(text)) if isinstance(text, str) else []
            text = _strip_embedded_calls(text)
            calls = msg.get("tool_calls") or []
            if text:
                out.append({"type": "message", "role": "assistant",
                            "id": "msg_" + uuid.uuid4().hex[:16],
                            "status": "completed",
                            "content": [{"type": "output_text", "annotations": [],
                                         "text": text}]})
            out.extend({"type": "function_call", "id": "fc_" + uuid.uuid4().hex[:16],
                        "call_id": "call_" + uuid.uuid4().hex[:16],
                        "name": c.get("function", {}).get("name", ""),
                        "arguments": json.dumps(c.get("function", {}).get("arguments", {})),
                        "status": "completed"}
                       for c in calls)
            if parsed_ai and not calls:
                out.extend({"type": "function_call", "id": "fc_" + uuid.uuid4().hex[:16],
                            "call_id": "call_" + uuid.uuid4().hex[:16],
                            "name": b["name"], "arguments": json.dumps(b["input"]),
                            "status": "completed"}
                           for b in parsed_ai)
            return out

        if not stream:
            data = json.loads(resp.read().decode())
            output = build_output(data.get("message", {}) or {})
            self._send_json(200, {
                "id": rid, "object": "response", "created_at": int(time.time()),
                "model": body.get("model", DEFAULT_MODEL), "status": "completed",
                "output": output, "output_text": _output_text(output), "parallel_tool_calls": True,
                "usage": {"input_tokens": data.get("prompt_eval_count", 0),
                          "output_tokens": data.get("eval_count", 0)},
            })
            return

        # streaming (OpenAI Responses event stream)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        def revt(name, obj):
            self.wfile.write(f"event: {name}\ndata: {json.dumps(obj)}\n\n".encode())
            self.wfile.flush()

        revt("response.created", {"type": "response.created",
                                  "response": {"id": rid, "object": "response", "status": "in_progress",
                                               "model": body.get("model", DEFAULT_MODEL), "output": []}})
        acc, final_calls = [], []
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
                acc.append(piece)
                revt("response.output_text.delta", {"type": "response.output_text.delta",
                                                    "delta": piece})
            if msg.get("tool_calls"):
                final_calls = msg["tool_calls"]
            if chunk.get("done"):
                break
        text = "".join(acc)
        parsed_ai = _tool_use_blocks(_text_tool_blocks(text)) if not final_calls else []
        if _text_tool_blocks(text) and not final_calls:
            text = _strip_embedded_calls(text)
            revt("response.output_text.delta", {"type": "response.output_text.delta", "delta": ""})
        seq = int(time.time())
        output, oi = [], 0
        if text:
            output.append({"type": "message", "role": "assistant",
                           "id": "msg_" + uuid.uuid4().hex[:16], "status": "completed",
                           "content": [{"type": "output_text", "annotations": [], "text": text}]})
            revt("response.output_item.done", {"type": "response.output_item.done",
                                               "output_index": oi, "item": output[-1]})
            oi += 1
        for c in final_calls or []:
            fn = c.get("function", {}) or {}
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {"raw": args}
            item = {"type": "function_call", "id": "fc_" + uuid.uuid4().hex[:16],
                    "call_id": "call_" + uuid.uuid4().hex[:16], "name": fn.get("name", ""),
                    "arguments": json.dumps(args), "status": "completed"}
            output.append(item)
            revt("response.output_item.added", {"type": "response.output_item.added",
                                                "output_index": oi, "item": item})
            revt("response.output_item.done", {"type": "response.output_item.done",
                                               "output_index": oi, "item": item})
            oi += 1
        for b in parsed_ai if (parsed_ai and not final_calls) else []:
            item = {"type": "function_call", "id": "fc_" + uuid.uuid4().hex[:16],
                    "call_id": "call_" + uuid.uuid4().hex[:16], "name": b["name"],
                    "arguments": json.dumps(b["input"]), "status": "completed"}
            output.append(item)
            oi += 1
        revt("response.completed", {"type": "response.completed",
                                    "response": {"id": rid, "object": "response", "status": "completed",
                                                 "model": body.get("model", DEFAULT_MODEL),
                                                 "output": output, "output_text": _output_text(output),
                                                 "usage": {"input_tokens": 0, "output_tokens": 0}},
                                    "sequence_number": seq})

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
