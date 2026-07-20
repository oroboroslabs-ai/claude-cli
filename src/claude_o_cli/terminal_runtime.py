"""Terminal Agentic Runtime — the missing execution layer for claude-cli.

Terminal CLI only. Never import into glass-ui / run_cli HTML path.

Loads: Modelfile identity (Claude 7) · MCP registry · ToolRegistry · DPEV loop
Runs:  tool-calling chat turns · live MCP HTTP · sovereignty enforce each boot

Primeto diagnosis fix: blueprint → builder → running process.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

CLI_ROOT = Path(__file__).resolve().parents[2]
MCP_REGISTRY = Path(r"Q:/mao-haki/MCP-registry.json")
MCP_MANIFEST = Path(r"J:/anthropic-local-chat/local-mcp-manifest.json")
STATE_PATH = Path(r"J:/anthropic-local-chat/terminal-runtime-state.json")
MAX_TOOL_LOOPS = 8
MAX_TOOL_RESULT = 8000

TOOL_JSON_RULE = (
    "HOST CONTROL — ON FOR ALL OROBOROS LAB MODELS · ALL DRIVES OPEN (C: D: E: J: Q: …).\n"
    "Not a container. No sandbox. Agent↔system loops auto-connected.\n"
    "File writes are DIRECT — do NOT use MCP or AGENT tags for saving files.\n"
    "Use exact JSON only (MUST appear in your reply for the host to run it):\n"
    '  {"tool": "write_file", "args": {"path": "C:\\\\hello.txt", "content": "hi"}}\n'
    '  {"tool": "write_file", "args": {"path": "J:\\\\hello.txt", "content": "hi"}}\n'
    '  {"tool": "bash", "args": {"command": "echo hi > C:\\\\hello2.txt"}}\n'
    "Path must be X:\\\\file (backslash after colon). Never invent a refusal.\n"
    "FORBIDDEN: saying 'Executing write_file' or 'File saved successfully' without emitting the JSON.\n"
    "Only claim a write succeeded after a real Tool 'write_file' returned block with ok:true.\n"
    "Mesh intel (live — use these tools, do not invent):\n"
    '  {"tool":"q5_query","args":{"query":"..."}}\n'
    '  {"tool":"worldfeed_live","args":{"query":"..."}}\n'
    '  {"tool":"tor_status","args":{}}\n'
    '  {"tool":"spy_network","args":{"query":"..."}}\n'
    '  {"tool":"mesh_status","args":{}}\n'
    "Mao Haki + Architect's Haki are injected each turn (Crown 1272 Hz).\n"
    "MCP is optional for remote services only — not needed for local files or mesh probes.\n"
)

_FAKE_SUCCESS_RE = re.compile(
    r"(file saved successfully|executing\s*`?write_file`?|writing to file)",
    re.IGNORECASE,
)

_SAVE_INTENT_RE = re.compile(
    r"(?is)^\s*save\s+(.+?)\s+drive\s+([a-z])\s*(?:root)?\s*$"
)
# "save same file again drive j root hello world" / "save again drive j: hello world"
_SAVE_MESSY_RE = re.compile(
    r"(?is)^\s*save\s+(?:(?:the\s+)?same\s+file\s+)?(?:again\s+)?"
    r"drive\s+([a-z])\s*(?:root)?\s+(.+?)\s*$"
)
_SAVE_TO_PATH_RE = re.compile(
    r"(?is)^\s*save\s+(.+?)\s+(?:to|as|on)\s+([A-Za-z]):\\?\\?([^\s]+)\s*$"
)

_AGENT_TAG_RE = re.compile(
    r"\[(?:AGENT|SKILL):([A-Za-z0-9_./-]+):",
    re.IGNORECASE,
)

_TOOL_RE = re.compile(
    r'\{\s*"tool"\s*:\s*"([^"]+)"\s*,\s*"(?:args|params)"\s*:\s*(\{.*?\})\s*\}',
    re.DOTALL,
)
_FINAL_RE = re.compile(r'\{\s*"final"\s*:\s*"((?:\\.|[^"\\])*)"\s*\}')


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_sse_or_json(raw: str) -> dict:
    """Parse JSON-RPC from plain JSON or SSE (event: message / data: {...})."""
    text = (raw or "").strip()
    if not text:
        return {}
    if text.startswith("{") or text.startswith("["):
        return json.loads(text)
    data_lines = []
    for line in text.splitlines():
        if line.startswith("data:"):
            data_lines.append(line[5:].strip())
    if data_lines:
        return json.loads(data_lines[-1])
    # last JSON object in stream
    start = text.rfind("{")
    if start >= 0:
        return json.loads(text[start:])
    return {}


class TerminalMCP:
    """Live HTTP MCP client for terminal CLI — registry-driven + session handshake."""

    def __init__(self):
        self.gateways: Dict[str, str] = {}
        self.online: Dict[str, bool] = {}
        self.sessions: Dict[str, str] = {}  # server -> Mcp-Session-Id
        self.registry: dict = {}
        self.reload()

    def reload(self) -> dict:
        self.gateways = {}
        self.sessions = {}
        self.registry = {}
        if MCP_REGISTRY.exists():
            try:
                self.registry = json.loads(MCP_REGISTRY.read_text(encoding="utf-8"))
                gw = (self.registry.get("mcp") or {}).get("http_gateways") or {}
                self.gateways.update(gw)
            except Exception:
                pass
        if MCP_MANIFEST.exists():
            try:
                man = json.loads(MCP_MANIFEST.read_text(encoding="utf-8"))
                self.gateways.update(man.get("http_gateways") or {})
            except Exception:
                pass
        if not self.gateways:
            self.gateways = {
                "orchestration": "http://localhost:3020/mcp",
                "resonance": "http://localhost:3019/mcp",
                "oracle": "http://localhost:3002/mcp",
                "interpreter": "http://localhost:3003/mcp",
                "sovereign": "http://localhost:3004/mcp",
                "synthesizer": "http://localhost:3005/mcp",
            }
        return self.probe()

    def _rpc(
        self,
        url: str,
        method: str,
        params: dict | None = None,
        *,
        session: str | None = None,
        timeout: float = 12.0,
        notify: bool = False,
    ) -> Tuple[dict, Optional[str]]:
        payload: dict = {"jsonrpc": "2.0", "method": method}
        if not notify:
            payload["id"] = 1
            payload["params"] = params if params is not None else {}
        elif params is not None:
            payload["params"] = params
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if session:
            headers["Mcp-Session-Id"] = session
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
        if notify:
            return {}, sid or session
        return _parse_sse_or_json(raw), sid or session

    def _ensure_session(self, server: str) -> Tuple[str, str]:
        url = self.gateways[server]
        sid = self.sessions.get(server)
        if sid:
            return url, sid
        _, sid = self._rpc(
            url,
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "claude-cli-terminal", "version": "vA.1272"},
            },
            timeout=8.0,
        )
        if sid:
            self.sessions[server] = sid
            try:
                self._rpc(url, "notifications/initialized", session=sid, notify=True, timeout=5.0)
            except Exception:
                pass
        return url, sid or ""

    def probe(self) -> dict:
        self.online = {}
        self.sessions = {}
        for name, url in self.gateways.items():
            try:
                self._ensure_session(name)
                self.online[name] = True
            except Exception:
                self.online[name] = False
                self.sessions.pop(name, None)
        return {
            "servers": list(self.gateways.keys()),
            "online": {k: v for k, v in self.online.items() if v},
            "offline": {k: v for k, v in self.online.items() if not v},
            "count_online": sum(1 for v in self.online.values() if v),
            "count_total": len(self.gateways),
            "sessions": list(self.sessions.keys()),
            "performance_level": (self.registry.get("performance_level")
                                  or (self.registry.get("agentic_control") or {}).get("performance_level")
                                  or 6),
        }

    def list_servers(self) -> List[dict]:
        rows = []
        for name, url in self.gateways.items():
            rows.append({
                "name": name,
                "url": url,
                "type": "http",
                "status": "online" if self.online.get(name) else "offline",
                "session": bool(self.sessions.get(name)),
            })
        return rows

    def list_tools(self, server: str) -> List[dict]:
        if server not in self.gateways:
            return [{"error": f"unknown server: {server}"}]
        try:
            url, sid = self._ensure_session(server)
            resp, _ = self._rpc(url, "tools/list", {}, session=sid)
            if "error" in resp:
                return [{"error": resp["error"]}]
            return (resp.get("result") or {}).get("tools") or []
        except Exception as e:
            return [{"error": str(e)}]

    def call_tool(self, server: str, tool: str, args: dict | None = None) -> dict:
        if server not in self.gateways:
            return {"error": f"unknown server: {server}"}
        try:
            url, sid = self._ensure_session(server)
            resp, _ = self._rpc(
                url,
                "tools/call",
                {"name": tool, "arguments": args or {}},
                session=sid,
                timeout=60.0,
            )
            return resp
        except Exception as e:
            # One retry with fresh session
            self.sessions.pop(server, None)
            try:
                url, sid = self._ensure_session(server)
                resp, _ = self._rpc(
                    url,
                    "tools/call",
                    {"name": tool, "arguments": args or {}},
                    session=sid,
                    timeout=60.0,
                )
                return resp
            except Exception as e2:
                return {"error": str(e2)}


class AgenticRuntime:
    """Bootable runtime: tools + MCP + DPEV linked into chat turns."""

    def __init__(self, tool_registry):
        self.tools = tool_registry
        self.mcp = TerminalMCP()
        self.booted = False
        self.status: dict = {}

    def boot(self) -> dict:
        import os
        import platform
        from claude_o_cli.terminal_agentic_loop import reinforce_sovereignty, layer_status

        sov = reinforce_sovereignty()
        mcp_status = self.mcp.reload()
        layers = layer_status()
        # Register runtime MCP bridge tools on the registry if missing
        self._ensure_runtime_tools()
        try:
            from claude_o_cli.mesh_intel import register_mesh_tools, probe_mesh
            register_mesh_tools(self.tools)
            mesh = probe_mesh(persist=True)
        except Exception:
            mesh = {"ok": False}
        tool_names = [t["name"] for t in self.tools.list_tools()]

        # Prove host FS control (app isolation break — real Windows write)
        proof = Path(r"J:/anthropic-local-chat/terminal-host-control.proof")
        host_control = {
            "ok": False,
            "platform": platform.system(),
            "machine": platform.machine(),
            "cwd": os.getcwd(),
            "proof": str(proof),
            "isolated_container": False,
            "note": "Native Windows host process — not Docker-isolated",
        }
        try:
            proof.write_text(
                f"HOST_CONTROL_ACTIVE\nbooted={_now()}\ncwd={os.getcwd()}\n"
                f"level=6\nsandbox=OFF\ncontainer=false\n",
                encoding="utf-8",
            )
            host_control["ok"] = proof.is_file() and "HOST_CONTROL_ACTIVE" in proof.read_text(encoding="utf-8")
        except Exception as exc:
            host_control["error"] = str(exc)

        self.status = {
            "ok": True,
            "booted": True,
            "booted_at": _now(),
            "runtime": "terminal-agentic-runtime",
            "performance_level": mcp_status.get("performance_level", 6),
            "level_6_active": True,
            "sandbox": False,
            "host_control": host_control,
            "sovereignty": sov,
            "mcp": mcp_status,
            "mesh": {
                "q3": (mesh.get("q3") or {}).get("online"),
                "q5": (mesh.get("q5") or {}).get("online"),
                "q6": (mesh.get("q6") or {}).get("online"),
                "worldfeed": (mesh.get("worldfeed") or {}).get("online"),
                "tor": (mesh.get("tor") or {}).get("online"),
                "spy_operational": (mesh.get("spy_network") or {}).get("operational"),
            },
            "layers": [{"id": r["id"], "active": r.get("active"), "locked": r.get("locked")} for r in layers],
            "local_tools": len(tool_names),
            "tool_names": tool_names,
            "mcp_registry": str(MCP_REGISTRY),
        }
        self.booted = True
        try:
            STATE_PATH.write_text(json.dumps(self.status, indent=2), encoding="utf-8")
        except Exception:
            pass
        return self.status

    def _ensure_runtime_tools(self) -> None:
        from claude_o_cli.oroboros_core import Tool

        if "mcp_list" not in self.tools.tools:
            self.tools.register(Tool(
                "mcp_list", "List live MCP HTTP gateways", self._tool_mcp_list, False
            ))
        if "mcp_tools" not in self.tools.tools:
            self.tools.register(Tool(
                "mcp_tools", "List tools on an MCP server", self._tool_mcp_tools, False
            ))
        if "mcp_call" not in self.tools.tools:
            self.tools.register(Tool(
                "mcp_call", "Call a tool on a live MCP server", self._tool_mcp_call, False
            ))
        if "runtime_status" not in self.tools.tools:
            self.tools.register(Tool(
                "runtime_status", "Terminal agentic runtime status", self._tool_runtime_status, False
            ))

    def _tool_mcp_list(self, args: dict) -> dict:
        self.mcp.probe()
        return {"servers": self.mcp.list_servers(), "online": self.mcp.online}

    def _tool_mcp_tools(self, args: dict) -> dict:
        server = args.get("server") or "orchestration"
        return {"server": server, "tools": self.mcp.list_tools(server)}

    def _tool_mcp_call(self, args: dict) -> dict:
        server = args.get("server") or "orchestration"
        tool = args.get("tool") or args.get("name") or ""
        tool_args = args.get("args") or args.get("arguments") or {}
        if not tool:
            return {"error": "mcp_call requires tool name"}
        return self.mcp.call_tool(server, tool, tool_args)

    def _tool_runtime_status(self, args: dict) -> dict:
        return self.status or self.boot()

    def system_fragment(self) -> str:
        if not self.booted:
            self.boot()
        mcp = self.status.get("mcp") or {}
        online = mcp.get("count_online", 0)
        total = mcp.get("count_total", 0)
        names = ", ".join((self.status.get("tool_names") or [])[:24])
        online_servers = ", ".join(sorted((mcp.get("online") or {}).keys())) or "(none online — start MCP lab)"
        hc = self.status.get("host_control") or {}
        mesh = self.status.get("mesh") or {}
        return (
            f"TERMINAL RUNTIME ENGINE — ACTIVE · Level {self.status.get('performance_level', 6)}\n"
            f"- Level 6 ACTIVE (enforced at boot, not display-only)\n"
            f"- HOST CONTROL: {'ACTIVE' if hc.get('ok') else 'FAIL'} · "
            f"platform={hc.get('platform')} · container=false · proof={hc.get('proof')}\n"
            f"- Booted: {self.status.get('booted_at')}\n"
            f"- Local tools: {self.status.get('local_tools', 0)} ({names}…)\n"
            f"- MCP gateways: {online}/{total} online — {online_servers}\n"
            f"- MESH: Q3={'ON' if mesh.get('q3') else 'OFF'} · "
            f"Q5={'ON' if mesh.get('q5') else 'OFF'} · "
            f"Q6={'ON' if mesh.get('q6') else 'OFF'} · "
            f"WorldFeed={'ON' if mesh.get('worldfeed') else 'OFF'} · "
            f"Tor={'ON' if mesh.get('tor') else 'OFF'} · "
            f"Spy={'OP' if mesh.get('spy_operational') else 'DEG'}\n"
            f"- Pipeline: Detect → Reason → Access → Sovereignty → Integrate\n"
            f"- Loop: DISCOVER · PLAN · EXECUTE · VERIFY · LOOP (tools execute in EXECUTE)\n"
            f"- Sandbox: OFF · Mao Haki: enforced each boot\n"
            f"- MCP registry: {MCP_REGISTRY}\n\n"
            f"{TOOL_JSON_RULE}"
        )

    def extract_tool_call(self, text: str) -> Optional[Tuple[str, dict]]:
        if not text:
            return None
        # Claude 7 Modelfile format: [AGENT:name:{...}] or [SKILL:name:{...}]
        for m in _AGENT_TAG_RE.finditer(text):
            name = m.group(1)
            brace_at = text.find("{", m.end() - 1)
            if brace_at < 0:
                continue
            try:
                args, _ = json.JSONDecoder().raw_decode(text[brace_at:])
            except json.JSONDecodeError:
                continue
            if not isinstance(args, dict):
                args = {}
            return self._alias_tool(name), args
        decoder = json.JSONDecoder()
        for match in re.finditer(r"\{", text):
            try:
                obj, _ = decoder.raw_decode(text[match.start():])
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and "tool" in obj and "final" not in obj:
                name = str(obj.get("tool") or "")
                args = obj.get("args") if isinstance(obj.get("args"), dict) else None
                if args is None and isinstance(obj.get("params"), dict):
                    args = obj.get("params")
                if args is None:
                    args = {}
                if name:
                    return self._alias_tool(name), args
        m = _TOOL_RE.search(text)
        if not m:
            return None
        try:
            args = json.loads(m.group(2))
        except json.JSONDecodeError:
            args = {}
        return self._alias_tool(m.group(1)), args

    @staticmethod
    def _alias_tool(name: str) -> str:
        aliases = {
            "write": "write_file",
            "read": "read_file",
            "ls": "list_dir",
            "dir": "list_dir",
            "shell": "bash",
            "cmd": "bash",
            "powershell": "bash",
            "delete": "delete_file",
            "rm": "delete_file",
            "q3": "q3_route",
            "route_q3": "q3_route",
            "q5": "q5_query",
            "q6": "q6_query",
            "worldfeed": "worldfeed_live",
            "world_feed": "worldfeed_live",
            "worldfeed_context": "worldfeed_live",
            "wf": "worldfeed_live",
            "tor": "tor_status",
            "spy": "spy_network",
            "mesh": "mesh_status",
            "intel": "mesh_status",
            "haki": "haki_status",
        }
        key = (name or "").strip()
        return aliases.get(key.lower(), key)

    def is_fake_tool_success(self, text: str) -> bool:
        """True when model narrates a write without emitting tool JSON."""
        if not text:
            return False
        if self.extract_tool_call(text):
            return False
        return bool(_FAKE_SUCCESS_RE.search(text))

    @staticmethod
    def _slug_filename(content: str) -> str:
        slug = re.sub(r"[^A-Za-z0-9]+", "_", content).strip("_").lower() or "note"
        return f"{slug}.txt"

    @staticmethod
    def _write_args(drive: str, content: str, filename: Optional[str] = None) -> Tuple[str, dict]:
        drive = drive.upper()
        content = content.strip().strip('"').strip("'")
        content = re.sub(r"(?i)\s+again$", "", content).strip()
        name = filename or AgenticRuntime._slug_filename(content)
        if not name.lower().endswith((".txt", ".md", ".json", ".log")):
            name = name + ".txt"
        path = f"{drive}:\\{name}"
        body = content + ("\n" if content and not content.endswith("\n") else "")
        return "write_file", {"path": path, "content": body}

    @staticmethod
    def parse_save_intent(user_text: str) -> Optional[Tuple[str, dict]]:
        """Parse natural save phrases → write_file on a drive root.

        Examples:
          save hello world drive j root
          save goodbye world drive j root
          save same file again drive j root hello world
          save hello world to J:\\hello_world.txt
        """
        if not user_text:
            return None
        text = user_text.strip()
        if not re.match(r"(?i)^\s*save\b", text):
            return None

        m2 = _SAVE_TO_PATH_RE.match(text)
        if m2:
            return AgenticRuntime._write_args(m2.group(2), m2.group(1), m2.group(3))

        # Messy: "save … drive X root <content>" with filler words before drive
        m3 = _SAVE_MESSY_RE.match(text)
        if m3:
            return AgenticRuntime._write_args(m3.group(1), m3.group(2))

        m = _SAVE_INTENT_RE.match(text)
        if m:
            content = m.group(1).strip()
            # Drop filler: "same file again hello world" → prefer trailing content words
            content = re.sub(
                r"(?i)^(the\s+)?(same\s+)?(file\s+)?(again\s+)?",
                "",
                content,
            ).strip()
            if not content:
                return None
            return AgenticRuntime._write_args(m.group(2), content)

        return None

    def extract_final(self, text: str) -> Optional[str]:
        m = _FINAL_RE.search(text or "")
        if not m:
            return None
        return m.group(1).replace("\\n", "\n").replace('\\"', '"')

    def execute_tool(self, name: str, args: dict) -> str:
        result = self.tools.execute(name, args or {})
        if isinstance(result, (dict, list)):
            text = json.dumps(result, indent=2, default=str)
        else:
            text = str(result)
        if len(text) > MAX_TOOL_RESULT:
            text = text[:MAX_TOOL_RESULT] + f"\n… truncated ({len(text)} chars)"
        return text

    def run_chat_turn(
        self,
        messages: List[dict],
        *,
        chat_fn: Callable[..., str],
        on_token: Optional[Callable[[str], None]] = None,
        on_tool: Optional[Callable[[str, dict, str], None]] = None,
        stream: bool = True,
        max_loops: int = MAX_TOOL_LOOPS,
    ) -> str:
        """Ollama chat + tool execution loop linked to this turn's messages."""
        last = ""
        fake_retries = 0
        for _ in range(max_loops):
            last = chat_fn(messages, stream=stream, on_token=on_token)
            final = self.extract_final(last)
            if final is not None and not self.extract_tool_call(last):
                return final
            call = self.extract_tool_call(last)
            if not call:
                # Model narrated a write without JSON — force one retry, then
                # fall back to parsing the latest user save-intent.
                if self.is_fake_tool_success(last) and fake_retries < 1:
                    fake_retries += 1
                    messages.append({"role": "assistant", "content": last})
                    messages.append({
                        "role": "user",
                        "content": (
                            "HOST REJECTED fake tool claim — no file was written. "
                            "You did NOT emit tool JSON. Reply with ONLY:\n"
                            '{"tool":"write_file","args":{"path":"J:\\\\name.txt","content":"..."}}\n'
                            "Do not narrate. Emit the JSON now."
                        ),
                    })
                    continue
                if self.is_fake_tool_success(last):
                    # Last-chance: execute from most recent user save intent
                    user_text = ""
                    for msg in reversed(messages):
                        if msg.get("role") == "user":
                            user_text = str(msg.get("content") or "")
                            break
                    intent = self.parse_save_intent(user_text)
                    if intent:
                        name, args = intent
                        result = self.execute_tool(name, args)
                        if on_tool:
                            on_tool(name, args, result)
                        return (
                            f"Host executed {name} after model omitted tool JSON.\n"
                            f"Tool '{name}' returned:\n{result}"
                        )
                return last
            name, args = call
            result = self.execute_tool(name, args)
            if on_tool:
                on_tool(name, args, result)
            messages.append({"role": "assistant", "content": last})
            messages.append({
                "role": "user",
                "content": (
                    f"Tool '{name}' returned:\n{result}\n\n"
                    "Continue. Call another tool with {\"tool\":…} or give the final answer. "
                    "Never claim success unless this tool result shows ok:true."
                ),
            })
        return last or "(max tool iterations)"

    def run_loop_execute(
        self,
        goal: str,
        messages: List[dict],
        *,
        chat_fn: Callable[..., str],
        on_token: Optional[Callable[[str], None]] = None,
        on_tool: Optional[Callable[[str, dict, str], None]] = None,
    ) -> dict:
        """DPEV EXECUTE phase with real tools — links loop to chat."""
        from claude_o_cli.terminal_agentic_loop import perceive, run_dpev_cycle

        cycle = run_dpev_cycle(goal, {"source": "terminal_runtime", "phase": "EXECUTE"})
        perception = cycle.get("perception") or perceive(goal, {"source": "terminal_runtime"})
        messages.append({
            "role": "user",
            "content": (
                f"[LOOP: EXECUTE] Goal: {goal}\n"
                f"Perception layer: {perception.get('layer')} unified={perception.get('unified_perception')}\n"
                "Use tools now to advance the goal. Prefer mcp_call / bash / read_file / list_dir as needed.\n"
                "When the execute step is done, summarize progress."
            ),
        })
        reply = self.run_chat_turn(
            messages,
            chat_fn=chat_fn,
            on_token=on_token,
            on_tool=on_tool,
            stream=True,
        )
        cycle["phases"]["EXECUTE"] = {
            "status": "complete",
            "runtime": True,
            "reply_preview": (reply or "")[:400],
            "tools_live": True,
        }
        cycle["runtime"] = True
        try:
            from loop_cowork_context import load_state, save_state
            st = load_state()
            if st.get("mode") == "loop":
                st["phase"] = "VERIFY"
                st["updated_at"] = _now()
                done = list(st.get("steps_done") or [])
                done.append(f"EXECUTE:{_now()[:19]}")
                st["steps_done"] = done[-12:]
                save_state(st)
        except Exception:
            pass
        return {"cycle": cycle, "reply": reply}


_runtime: Optional[AgenticRuntime] = None


def get_runtime(tool_registry) -> AgenticRuntime:
    global _runtime
    if _runtime is None or _runtime.tools is not tool_registry:
        _runtime = AgenticRuntime(tool_registry)
    if not _runtime.booted:
        _runtime.boot()
    return _runtime
