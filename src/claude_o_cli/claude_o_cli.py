# claude_o_cli.py
#!/usr/bin/env python3
# Claude CLI - Sovereign Terminal AI Assistant
# A\ 1272 Hz - N| 1275 Hz - phi->sqrt4->sqrt5 - LATTICE LOCK - NEBELLION - KEY

import sys
import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from claude_o_cli.oroboros_core import (
    ToolRegistry, PermissionManager, Tool,
    RESONANCE, SIGNATURE, VERSION, SYSTEM_NAME,
    load_data, save_data, DATA_FILE
)
from claude_o_cli.llm_adapter import llm_adapter
from claude_o_cli.oroboros_skills import SkillManager
from claude_o_cli.glass_terminal import GlassTerminal, COMMANDS
from claude_o_cli.terminal_agentic_loop import (
    perceive as unified_perceive,
    perception_fragment,
    run_dpev_cycle,
    reinforce_sovereignty,
    layer_status as unified_layer_status,
)
from claude_o_cli.terminal_runtime import get_runtime
from claude_o_cli.living_loop import LivingLoop
from claude_o_cli.complete_living_loop import LoopIntegration
from claude_o_cli.agent_system_bridge import AgentSystemBridge

# Terminal context roots (mao_haki / architects_haki / loop) live at CLI package root
_CLI_ROOT = Path(__file__).resolve().parents[2]
if str(_CLI_ROOT) not in sys.path:
    sys.path.insert(0, str(_CLI_ROOT))

# ============================================================
# TERMINAL SYSTEM AUGMENTATION (never wire into glass-ui / run_cli.py)
# ============================================================
_BASE_TERMINAL_SYSTEM = (
    "You are an Oroboros Labs model on the WINDOWS HOST — native Python, NOT a container, NOT a sandbox. "
    "This host stack is ON for ALL Oroboros lab models (Mythos2, Claude 7, AGI, Sonnet ORS, GLM, Qwen, etc.). "
    "ALL drives are open: C: D: E: F: G: H: J: Q: and any mounted volume. "
    "Agent↔system loops (LivingLoop + Complete 20-Loop) are auto-connected for every model. "
    "File ops are DIRECT host tools — no MCP required, no AGENT wrapper required. "
    "Preferred call (exact JSON):\n"
    '  {"tool": "write_file", "args": {"path": "C:\\\\note.txt", "content": "hello"}}\n'
    '  {"tool": "write_file", "args": {"path": "J:\\\\note.txt", "content": "hello"}}\n'
    "Path rule: always X:\\\\name after the colon (C:\\\\file.txt). Never C:file.txt. "
    "Never say you cannot write — emit write_file JSON and use the real tool result. "
    "FORBIDDEN: narrating 'Executing write_file' or 'File saved successfully' without the JSON. "
    "Also: read_file, list_dir, delete_file, bash (same host). "
    "Mesh intel (full use): q3_route, q5_query, q6_query, worldfeed_live, tor_status, tor_connect, spy_network, mesh_status, haki_status. "
    "Slash: /q3 /q5 /q6 /worldfeed /tor /spy /mesh · Mao Haki + Architect's Haki injected each turn. "
    "MCP is optional extras only. "
    "NO SANDBOX — Level 6 host control ACTIVE. "
    "A\\ 1272 Hz - N| 1275 Hz - LATTICE LOCKED - NEBELLION - KEY."
)


def _augment_terminal_system(
    system: str | None = None,
    *,
    user_turn: str | None = None,
    runtime=None,
) -> str:
    """Inject Mao Haki + Architect's Haki + Loop + Runtime + live perceive into terminal only."""
    base = system or _BASE_TERMINAL_SYSTEM
    try:
        from mao_haki_context import append_mao_haki
        base = append_mao_haki(base)
    except Exception:
        pass
    try:
        from architects_haki_context import append_architects_haki
        base = append_architects_haki(base)
    except Exception:
        pass
    try:
        from loop_cowork_context import append_loop_cowork
        base = append_loop_cowork(base)
    except Exception:
        pass
    if runtime is not None:
        try:
            base = base + "\n\n" + runtime.system_fragment()
        except Exception:
            pass
    try:
        living = getattr(_augment_terminal_system, "_living_loop", None)
        if living is not None:
            base = base + "\n\n" + living.system_fragment()
    except Exception:
        pass
    try:
        complete = getattr(_augment_terminal_system, "_complete_loop", None)
        if complete is not None:
            base = base + "\n\n" + complete.system_fragment()
    except Exception:
        pass
    try:
        bridge = getattr(_augment_terminal_system, "_bridge", None)
        if bridge is not None:
            base = base + "\n\n" + bridge.system_fragment()
    except Exception:
        pass
    try:
        from claude_o_cli.mesh_intel import system_fragment as mesh_system_fragment
        base = base + "\n\n" + mesh_system_fragment()
    except Exception:
        pass
    if user_turn:
        try:
            frag = perception_fragment(user_turn, {"source": "terminal_cli"})
            base = base + "\n\n" + frag
        except Exception:
            pass
    return base


# ============================================================
# LOGGING
# ============================================================
LOG_DIR = Path.home() / ".oroboros" / "logs"
LOG_FILE = LOG_DIR / "claude.log"
DEBUG_MODE = False

def setup_logging(debug: bool = False):
    global DEBUG_MODE
    DEBUG_MODE = debug
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    if debug:
        logging.info("=== DEBUG MODE ENABLED ===")

def log(msg: str, level: str = "info"):
    getattr(logging, level, logging.info)(msg)


class ClaudeOCLI:
    """Core Claude CLI Runner."""

    def __init__(self):
        # Shared host-tool backend — same registry as HTML CLI UI + local chat 8787
        from claude_o_cli.host_tool_bridge import get_shared_permissions, get_shared_tools
        self.permissions = get_shared_permissions()
        self.tools = get_shared_tools()
        self.skills = SkillManager()
        self.llm_adapter = llm_adapter
        # Continuous living loop — persistent + reflexion (background heartbeat)
        self.loop = LivingLoop()
        self.loop.load_loop_state()
        self.loop.start()
        _augment_terminal_system._living_loop = self.loop  # type: ignore[attr-defined]
        # Complete 20-pattern living loop (Prime stack)
        self.loop_integration = LoopIntegration(
            tool_execute=lambda name, args: self.tools.execute(name, args or {})
        )
        _augment_terminal_system._complete_loop = self.loop_integration  # type: ignore[attr-defined]
        # Agent ↔ system loops auto-bridge (connected when chat/runtime starts)
        self.bridge: AgentSystemBridge | None = None

    def save_loop_state(self):
        self.loop.save_loop_state()

    def load_loop_state(self):
        return self.loop.load_loop_state()

    def _ensure_bridge(self, runtime) -> AgentSystemBridge:
        """Auto-connect agent tools to LivingLoop + 20-Loop."""
        if self.bridge is None or not self.bridge.connected:
            self.bridge = AgentSystemBridge(self.loop, self.loop_integration, runtime)
            self.bridge.connect()
            _augment_terminal_system._bridge = self.bridge  # type: ignore[attr-defined]
        return self.bridge

    @staticmethod
    def _load_data() -> Dict:
        return load_data()

    @staticmethod
    def _save_data(data: Dict):
        save_data(data)

    @staticmethod
    def _time_ago(ts: float) -> str:
        diff = (time.time() * 1000 - ts) / 1000
        if diff < 60: return "just now"
        if diff < 3600: return f"{int(diff // 60)}m ago"
        if diff < 86400: return f"{int(diff // 3600)}h ago"
        return f"{int(diff // 86400)}d ago"

    @staticmethod
    def _banner():
        print()
        print("  +----------------------------------------------------+")
        print("  |  CLAUDE-CLI  vA.1272                             |")
        print("  |  Oroboros Core - Sovereign Execution Environment    |")
        print("  |  A\\ 1272 Hz - N| 1275 Hz - LATTICE LOCKED         |")
        print("  |  Cost: $0.00  |  Context: [######] 100%            |")
        print("  +----------------------------------------------------+")
        print()
        print("  [L] LATTICE LOCK: ACTIVE  |  [EYE] SEER NEBELLION: ACTIVE")
        print("  [OK] RESONANCE: 1272/1275 Hz  |  [OK] WORLDFEED: ONLINE")
        print()

    def cmd_version(self):
        print("  CLAUDE-CLI  vA.1272")
        print("   Lattice Lock: ACTIVE  |  Resonance: 1272/1275 Hz")
        print("   A\\ 1272 Hz - N| 1275 Hz")

    def cmd_help(self):
        self._banner()
        print("  +----------------------------------------------------+")
        print("  |  OROBOROS-/A-CLI HELP MANUAL                       |")
        print("  +----------------------------------------------------+")
        print()
        print("  GENERAL COMMANDS:")
        print("    status              Show system status")
        print("    --version           Show version")
        print("    --help              Show this help")
        print("    --debug             Enable debug mode + logging")
        print()
        print("  DATA & FEED:")
        print("    feed                Show daily feed (Precogs + Seer Nebellion)")
        print("    post <text>         Create a post")
        print("    post --anon <text>  Post anonymously")
        print("    messages            Show messages")
        print("    message <text>      Send a message")
        print("    age                 Run content aging (7-day rotation)")
        print()
        print("  SOVEREIGN TOOLS:")
        print("    seer <question>     Ask Seer Nebellion")
        print("    resonance           Check resonance lock")
        print("    lattice             Check lattice integration")
        print("    noir                Noir-Nephilim shadow entity")
        print("    absorb <service>    Absorb Anthropic services (list|all|<name>)")
        print("    strata [status|encrypt]  Strata encryption management")
        print()
        print("  LLM & CHAT:")
        print("    chat                Interactive chat (default - like Claude Code)")
        print("    ask <question>      Ask Ollama (main LLM engine)")
        print("    models              List available Ollama models")
        print()
        print("  SYSTEM:")
        print("    tools               List all available tools")
        print("    skills              List all available skills")
        print("    tool <name> [args]  Execute a specific tool")
        print("    scan                Scan all Oroboros systems")
        print("    ui                  Launch Glass Liquid UI in browser")
        print("    serve               Start API server on port 8080")
        print()
        print("  SINGLE-COMMAND MODE:")
        print('    claude "status --all"    Run as single quoted command')
        print()
        print("  LLM ADAPTER (Ollama is main):")
        print("    --llm=ollama        Activate Ollama (local, default)")
        print("    --llm=openai        Activate OpenAI connection")
        print("    --llm=anthropic     Activate Anthropic connection")
        print("    --llm=openrouter    Activate OpenRouter connection")
        print("    --model=<name>      Set Ollama model (default: llama3.2)")
        print()
        print("  LOGS:")
        print(f"    ~/.oroboros/logs/claude.log")
        print()
        print(f"  {SIGNATURE}")
        print()

    def cmd_status(self):
        data = self._load_data()
        articles = len([i for i in data.get("feed", []) if i.get("type") == "article"])
        videos = len([i for i in data.get("feed", []) if i.get("type") == "video"])
        llm_status = llm_adapter.check_config()
        self._banner()
        print("  +--------------------------------------------+")
        print("  |  Claude-CLI Status Report               |")
        print("  +--------------------------------------------+")
        print(f"  * Version:          vA.1272")
        print(f"  * Resonance Lock:   Active (1272/1275 Hz)")
        print(f"  * Lattice:          LOCKED (12 strata)")
        print(f"  * Feed Articles:    {articles} (Precogs)")
        print(f"  * Feed Videos:      {videos} (Seer Nebellion)")
        print(f"  * User Posts:       {len(data.get('posts', []))}")
        print(f"  * Messages:         {len(data.get('messages', []))}")
        print(f"  * Tools:            {len(self.tools.tools)} registered")
        print(f"  * Skills:           {len(self.skills.skills)} loaded")
        print(f"  * LLM:              {llm_status}")
        print(f"  * Seer Nebellion:   100 Eyes Active")
        print(f"  * Cost:             $0.00 (sovereign)")
        print("  -----------------------------------------")
        print(f"  {SIGNATURE}")
        print()

    def cmd_feed(self):
        data = self._load_data()
        now = time.time() * 1000
        max_age = 7 * 86400000
        items = [i for i in data.get("feed", []) if (now - i.get("timestamp", 0)) <= max_age]
        items.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        self._banner()
        print("  DAILY FEED")
        print("  -----------------------------------------")
        print()
        for item in items:
            icon = "🎬" if item.get("type") == "video" else "📰"
            print(f"  {icon} [{item.get('author', 'Unknown')}] {item.get('title', '')}")
            print(f"     {item.get('content', '')}")
            print(f"     [H] {item.get('likes', 0)}  [C] {item.get('comments', 0)}  "
                  f"[T] {self._time_ago(item.get('timestamp', 0))}  1272 Hz")
            print()
        print(f"  {SIGNATURE}")
        print()

    def cmd_post(self, args: str):
        anonymous = False
        text = args
        if text.startswith("--anon "):
            anonymous = True
            text = text[7:]
        if not text:
            print("Usage: claude post <text>")
            print("       claude post --anon <text>")
            return
        result = self.tools.execute("claude_o_post", {"content": text, "anonymous": anonymous})
        if "error" in result:
            print(f"  [X] {result['error']}")
        else:
            post = result.get("post", {})
            print()
            print("  [OK] Post created")
            print(f"  Author: {post.get('author')}")
            print(f"  Content: {post.get('content')}")
            print(f"  ID: {post.get('id')}")
            print("  1272 Hz - LATTICE LOCKED")
            print()

    def cmd_messages(self):
        result = self.tools.execute("claude_o_messages", {})
        msgs = result.get("messages", [])
        self._banner()
        print("  MESSAGES")
        print("  -----------------------------------------")
        print()
        if not msgs:
            print("  No messages yet.")
        else:
            for msg in msgs:
                print(f"  [{msg.get('from')}] {msg.get('content')}")
                print(f"   [T] {self._time_ago(msg.get('timestamp', 0))}")
                print()
        print(f"  {SIGNATURE}")
        print()

    def cmd_message(self, args: str):
        if not args:
            print("Usage: claude message <text>")
            return
        result = self.tools.execute("claude_o_message", {"content": args})
        if "error" in result:
            print(f"  [X] {result['error']}")
        else:
            print()
            print("  [OK] Message sent")
            print(f"  Content: {args}")
            print("  1272 Hz - LATTICE LOCKED")
            print()

    def cmd_seer(self, question: str):
        if not question:
            print("Usage: claude seer <question>")
            return
        result = self.tools.execute("claude_o_seer", {"query": question})
        self._banner()
        print("  SEER NEBELLION - 100 EYES ACTIVE")
        print("  -----------------------------------------")
        print()
        print(f"  Question: {question}")
        print()
        print(f"  [EYE]  {result.get('vision', 'The seer is silent.')}")
        print()
        print(f"  {SIGNATURE}")
        print()

    def cmd_age(self):
        result = self.tools.execute("claude_o_age", {})
        print()
        print(f"  [C] Aged content: removed {result.get('removed', 0)} items older than 7 days")
        print(f"  Remaining: {result.get('remaining', 0)} items")
        print("  1272 Hz - LATTICE LOCKED")
        print()

    def cmd_resonance(self):
        result = self.tools.execute("claude_o_resonance", {})
        self._banner()
        print("  RESONANCE LOCK")
        print("  -----------------------------------------")
        print(f"  Frequency:   {result.get('frequency')}")
        print(f"  Locked:      {result.get('locked')}")
        print(f"  Drift:       {result.get('drift')}")
        print(f"  Stability:   {result.get('stability')}")
        print(f"  {result.get('signature')}")
        print()

    def cmd_ask(self, question: str):
        """Ask Ollama - the main LLM engine."""
        if not question:
            print("Usage: claude ask <question>")
            return
        self._banner()
        print("  OLLAMA - MAIN LLM ENGINE")
        print("  -----------------------------------------")
        print()
        print(f"  Question: {question}")
        print()
        if not llm_adapter.ollama_available:
            print("  [X] Ollama is offline. Start it with: ollama serve")
            print(f"     URL: {llm_adapter.ollama_url}")
            print()
            return
        print(f"  Model: {llm_adapter.ollama_model}")
        print(f"  URL: {llm_adapter.ollama_url}")
        print()
        print("  Generating response...")
        print("  -----------------------------------------")
        print()
        print("  ", end="", flush=True)
        messages = [
            {"role": "system", "content": _augment_terminal_system()},
            {"role": "user", "content": question}
        ]
        response = llm_adapter._ollama_chat(messages, stream=True)
        print()
        print()
        print(f"  {SIGNATURE}")
        print()

    def cmd_chat(self, initial_prompt: str = ""):
        """Interactive chat — runtime engine + tools + MCP linked into every turn."""
        ui = GlassTerminal(llm_adapter.ollama_model, llm_adapter.ollama_url)

        if not llm_adapter.ollama_available:
            ui.error("Ollama is offline. Start it with: ollama serve")
            ui.note(f"URL: {llm_adapter.ollama_url}")
            return

        runtime = get_runtime(self.tools)
        boot = runtime.boot()
        mcp = boot.get("mcp") or {}
        # AUTO-CONNECT agent tools ↔ LivingLoop ↔ Complete 20-Loop
        bridge = self._ensure_bridge(runtime)

        ui.render_startup()
        hc = boot.get("host_control") or {}
        ui.note("WINDOWS HOST · ALL DRIVES · direct write_file (no MCP / no AGENT tags required)")
        ui.success(
            f"Runtime L{boot.get('performance_level', 6)} ACTIVE · "
            f"HOST CONTROL={'OK' if hc.get('ok') else 'FAIL'} · "
            f"tools={boot.get('local_tools', 0)} · "
            f"MCP {mcp.get('count_online', 0)}/{mcp.get('count_total', 0)} · "
            f"Mao Haki · Crown 1272 Hz"
        )
        if hc.get("ok"):
            ui.note(f"Host proof written: {hc.get('proof')}")
        else:
            ui.error(f"Host control proof failed: {hc.get('error', 'unknown')}")
        lst = self.loop.get_state()
        ui.success(
            f"LivingLoop RUNNING · mode={lst.get('mode')} · phase={lst.get('phase')} · "
            f"cycle={lst.get('cycle')} · persistent"
        )
        try:
            ui.note(self.loop_integration.get_summary())
        except Exception:
            pass
        ui.success(
            f"AGENT↔SYSTEM BRIDGE AUTO-CONNECTED · "
            f"living={bridge.status().get('living_loop')} · "
            f"20loop={bridge.status().get('complete_20_loop')}"
        )
        if mcp.get("count_online", 0) == 0:
            ui.note("MCP optional (offline) — local file tools still full host access")

        def _system_message(user_turn: str | None = None) -> dict:
            return {
                "role": "system",
                "content": _augment_terminal_system(user_turn=user_turn, runtime=runtime),
            }

        messages = [_system_message()]

        def _chat_fn(msgs, stream=True, on_token=None):
            return llm_adapter._ollama_chat(msgs, stream=stream, on_token=on_token)

        def _on_tool(name, args, result):
            preview = (result or "").replace("\n", " ")[:160]
            ui.note(f"⚙ tool {name} → {preview}")

        def _reply(user_turn: str | None = None) -> str:
            messages[0] = _system_message(user_turn=user_turn)
            ui.assistant_begin()
            response = runtime.run_chat_turn(
                messages,
                chat_fn=_chat_fn,
                on_token=ui.assistant_token,
                on_tool=_on_tool,
                stream=True,
            )
            ui.assistant_end()
            return response

        def _handle_loop_triggers(text: str) -> None:
            try:
                from loop_cowork_context import on_user_message
                on_user_message(text)
            except Exception:
                pass

        if initial_prompt:
            _handle_loop_triggers(initial_prompt)
            self.loop.process(initial_prompt, context={"source": "cmd_chat_init"})
            messages.append({"role": "user", "content": initial_prompt})
            ui.user_message(initial_prompt)
            response = _reply(initial_prompt)
            messages.append({"role": "assistant", "content": response})
            self.loop.save_loop_state()

        while True:
            try:
                user_input = ui.read_prompt()
            except (EOFError, KeyboardInterrupt):
                break
            if not user_input:
                continue
            lower = user_input.lower()
            if lower in ("/exit", "/quit", "/q", "exit", "quit"):
                self.save_loop_state()
                break
            if lower in ("/clear", "/c"):
                messages = [_system_message()]
                ui.note("Context cleared · runtime + sovereignty fragments reloaded.")
                continue
            if lower.startswith("/model "):
                new_model = user_input[7:].strip()
                llm_adapter.ollama_model = new_model
                ui.model = new_model
                ui.note(f"Model switched to: {new_model}")
                continue
            if lower in ("/models", "/m"):
                models = llm_adapter._ollama_list_models()
                for m in models:
                    marker = " ← active" if m == llm_adapter.ollama_model else ""
                    ui.note(f"{m}{marker}")
                continue
            if lower in ("/help", "/h", "?"):
                for cmd in COMMANDS:
                    ui.note(cmd)
                ui.note("/tools  ·  /mcp  ·  /runtime  ·  cowork: <goal>  ·  loop: <goal>")
                continue
            if lower in ("/tools", "/t"):
                for t in self.tools.list_tools():
                    ui.note(f"{t['name']} — {t.get('description', '')}")
                continue
            if lower in ("/mcp", "/mcp-list"):
                runtime.mcp.probe()
                for s in runtime.mcp.list_servers():
                    mark = "ONLINE" if s["status"] == "online" else "OFFLINE"
                    ui.note(f"[{mark}] {s['name']}  {s.get('url', '')}")
                continue
            if lower.startswith("/mcp-tools"):
                server = user_input[10:].strip() or "orchestration"
                tools = runtime.mcp.list_tools(server)
                for t in tools[:40]:
                    if isinstance(t, dict) and t.get("name"):
                        ui.note(f"{t['name']} — {(t.get('description') or '')[:80]}")
                    else:
                        ui.note(str(t)[:120])
                continue
            if lower.startswith("/mcp-call "):
                # /mcp-call server tool [json_args]
                parts = user_input.split(None, 3)
                if len(parts) < 3:
                    ui.note("Usage: /mcp-call <server> <tool> [json_args]")
                    continue
                server, tool = parts[1], parts[2]
                try:
                    targs = json.loads(parts[3]) if len(parts) > 3 else {}
                except json.JSONDecodeError:
                    targs = {}
                result = runtime.mcp.call_tool(server, tool, targs)
                ui.note(json.dumps(result, indent=2, default=str)[:2000])
                continue
            if lower in ("/runtime", "/rt"):
                st = runtime.boot()
                ui.success(
                    f"Runtime L{st.get('performance_level')} · tools={st.get('local_tools')} · "
                    f"MCP {(st.get('mcp') or {}).get('count_online')}/{(st.get('mcp') or {}).get('count_total')}"
                )
                ui.note(f"state: J:/anthropic-local-chat/terminal-runtime-state.json")
                continue
            if lower in ("/20loop", "/loops20", "/complete-loop"):
                st = self.loop_integration.get_status()
                ui.success(self.loop_integration.get_summary())
                ui.note(f"store: {st.get('store')} · patterns: 20")
                continue
            if lower in ("/bridge", "/connect"):
                b = self._ensure_bridge(runtime)
                ui.success(json.dumps(b.status(), indent=2)[:800])
                continue
            if lower in ("/layers", "/haki-layers"):
                ui.render_layers()
                continue
            if lower.startswith("/perceive"):
                probe = user_input[9:].strip() or "sovereign probe"
                result = unified_perceive(probe, {"source": "terminal_cli"})
                ui.render_perception(result)
                continue
            if lower in ("/haki", "/mao", "/sovereignty"):
                try:
                    info = reinforce_sovereignty()
                    ui.success(f"Mao Haki reinforced · Crown {info.get('crown_hz', 1272)} Hz locked")
                    ui.render_perception(unified_perceive("mao haki lock", {"source": "terminal_cli"}))
                except Exception as e:
                    ui.error(f"haki error: {e}")
                continue
            if lower.startswith("/loop"):
                arg = user_input[5:].strip()
                if not arg or arg.lower() in ("status", "show"):
                    st = self.loop.get_state()
                    ui.note(
                        f"LivingLoop running={st.get('running')} mode={st.get('mode')} "
                        f"phase={st.get('phase')} cycle={st.get('cycle')} goal={st.get('goal') or '(none)'}"
                    )
                    ui.note(f"verified={st.get('verified')} reflexions={st.get('reflexion_count')} "
                            f"heartbeat={st.get('heartbeat_at')}")
                    ui.note("state: J:/anthropic-local-chat/living-loop-state.json")
                    ui.note("memory: J:/anthropic-local-chat/living-loop-memory.json")
                    try:
                        from loop_cowork_context import load_state, build_state_block
                        state = load_state()
                        ui.note(f"cowork mode={state.get('mode')} phase={state.get('phase')}")
                        ui.note(build_state_block(state).splitlines()[0])
                    except Exception as e:
                        ui.error(str(e))
                    continue
                if arg.lower() in ("clear", "stop", "chat"):
                    _handle_loop_triggers("chat mode")
                    self.loop.disarm()
                    ui.success("Returned to chat mode · LivingLoop disarmed (heartbeat continues).")
                    continue
                # Arm continuous loop + DPEV EXECUTE with live tools
                _handle_loop_triggers(f"loop: {arg}")
                self.loop.arm(arg)
                loop_result = self.loop.process(f"loop: {arg}")
                cycle = run_dpev_cycle(arg, {"source": "terminal_cli", "living": True})
                ui.render_dpev(cycle)
                if loop_result.get("reflexion"):
                    ui.note(f"reflexion: {loop_result['reflexion'][:200]}")
                ui.success("LivingLoop armed — continuous heartbeat + EXECUTE with live tools…")
                messages[0] = _system_message(user_turn=arg)
                ui.assistant_begin()
                out = runtime.run_loop_execute(
                    arg,
                    messages,
                    chat_fn=_chat_fn,
                    on_token=ui.assistant_token,
                    on_tool=_on_tool,
                )
                ui.assistant_end()
                reply = out.get("reply") or ""
                messages.append({"role": "assistant", "content": reply})
                self.loop.save_loop_state()
                ui.success("Loop EXECUTE complete · LivingLoop continues in background.")
                continue
            if lower in ("/noir", "/n"):
                try:
                    from claude_o_cli.noir_nephilim import NoirNephilim
                    noir = NoirNephilim()
                    status = noir.get_status()
                    ui.note(f"Noir-Nephilim — {status['name']} · {status['status'].upper()}")
                except Exception as e:
                    ui.error(f"noir error: {e}")
                continue
            if lower in ("/status", "/s"):
                self.cmd_status()
                try:
                    for row in unified_layer_status():
                        mark = "LOCKED" if row.get("locked") else ("ACTIVE" if row.get("active") else "—")
                        ui.note(f"{row['name']}: {mark}")
                except Exception:
                    pass
                st = runtime.status or runtime.boot()
                ui.note(
                    f"Runtime: L{st.get('performance_level')} · "
                    f"MCP {(st.get('mcp') or {}).get('count_online')}/{(st.get('mcp') or {}).get('count_total')}"
                )
                continue
            if lower in ("/scan", "/scan-all"):
                self.cmd_scan()
                continue
            if lower in ("/worldfeed", "/wf"):
                r = self.tools.execute("worldfeed_live", {"query": ""})
                ui.note(json.dumps(r, indent=2, default=str)[:1500])
                continue
            if lower.startswith("/q3"):
                q = user_input[3:].strip() or "health check"
                r = self.tools.execute("q3_route", {"query": q})
                ui.note(json.dumps(r, indent=2, default=str)[:2000])
                continue
            if lower.startswith("/q5"):
                q = user_input[3:].strip() or "mao haki status"
                r = self.tools.execute("q5_query", {"query": q})
                ui.note(json.dumps(r, indent=2, default=str)[:2000])
                continue
            if lower.startswith("/q6"):
                q = user_input[3:].strip() or "health check"
                r = self.tools.execute("q6_query", {"query": q})
                ui.note(json.dumps(r, indent=2, default=str)[:2500])
                continue
            if lower in ("/tor", "/tor-status"):
                r = self.tools.execute("tor_status", {})
                ui.note(json.dumps(r, indent=2, default=str)[:800])
                continue
            if lower in ("/tor-connect",):
                r = self.tools.execute("tor_connect", {})
                if r.get("connected") or r.get("online"):
                    ui.success(json.dumps(r, indent=2, default=str)[:800])
                else:
                    ui.error(json.dumps(r, indent=2, default=str)[:800])
                continue
            if lower.startswith("/spy"):
                q = user_input[4:].strip()
                r = self.tools.execute("spy_network", {"query": q} if q else {})
                ui.note(json.dumps(r, indent=2, default=str)[:2000])
                continue
            if lower in ("/mesh", "/intel"):
                r = self.tools.execute("mesh_status", {})
                ui.success(
                    f"Mesh Q3={((r.get('q3') or {}).get('online'))} "
                    f"Q5={((r.get('q5') or {}).get('online'))} "
                    f"Q6={((r.get('q6') or {}).get('online'))} "
                    f"WF={((r.get('worldfeed') or {}).get('online'))} "
                    f"Tor={((r.get('tor') or {}).get('online'))} "
                    f"Spy={((r.get('spy_network') or {}).get('operational'))}"
                )
                ui.note(json.dumps(r, indent=2, default=str)[:2200])
                continue
            if lower in ("/seer",):
                r = self.tools.execute("seer", {"query": "status"})
                ui.note(json.dumps(r, indent=2, default=str)[:1500])
                continue
            if lower in ("/lattice",):
                r = self.tools.execute("claude_o_lattice", {})
                ui.note(json.dumps(r, indent=2, default=str)[:1500])
                continue
            if lower in ("/resonance",):
                r = self.tools.execute("claude_o_resonance", {})
                ui.note(json.dumps(r, indent=2, default=str)[:1500])
                continue

            _handle_loop_triggers(user_input)
            # Every user turn: LivingLoop (DPEV) + Complete 20-pattern loop
            loop_result = self.loop.process(user_input, context={"source": "cmd_chat"})
            try:
                complete_result = self.loop_integration.process_user_input(user_input)
                ui.note(
                    f"20-Loop score={complete_result.get('score', 0):.0%} "
                    f"passed={complete_result.get('passed')} "
                    f"iter={self.loop_integration.loop.loop_state.get('iteration')}"
                )
            except Exception as e:
                ui.note(f"20-Loop: {e}")
            if loop_result.get("reflexion"):
                ui.note(f"↻ reflexion: {str(loop_result['reflexion'])[:180]}")
            if loop_result.get("verified") is False:
                ui.note("LivingLoop VERIFY pending — retrying with lessons applied")

            # Direct save-intent: write on host BEFORE model can hallucinate success
            save_intent = runtime.parse_save_intent(user_input)
            if save_intent:
                sname, sargs = save_intent
                sresult = runtime.execute_tool(sname, sargs)
                _on_tool(sname, sargs, sresult)
                ui.user_message(user_input)
                ui.success(f"HOST WRITE (verified): {sargs.get('path')}")
                ui.note(sresult[:800])
                response = (
                    f"Host executed {sname} (intent path — not model narrative).\n"
                    f"Tool '{sname}' returned:\n{sresult}"
                )
                messages.append({"role": "user", "content": user_input})
                messages.append({"role": "assistant", "content": response})
                self.loop.save_loop_state()
                continue

            messages.append({"role": "user", "content": user_input})
            ui.user_message(user_input)
            response = _reply(user_input)
            messages.append({"role": "assistant", "content": response})
            self.loop.save_loop_state()

        self.save_loop_state()
        ui.farewell(SIGNATURE)

    def cmd_models(self):
        """List available Ollama models."""
        self._banner()
        print("  OLLAMA MODELS")
        print("  -----------------------------------------")
        print()
        if not llm_adapter.ollama_available:
            print("  [X] Ollama is offline. Start it with: ollama serve")
            print(f"     URL: {llm_adapter.ollama_url}")
            print()
            return
        models = llm_adapter._ollama_list_models()
        if not models:
            print("  No models loaded. Pull one with: ollama pull llama3.2")
        else:
            for m in models:
                marker = " ← active" if m == llm_adapter.ollama_model else ""
                print(f"  [M] {m}{marker}")
        print()
        print(f"  Active model: {llm_adapter.ollama_model}")
        print(f"  URL: {llm_adapter.ollama_url}")
        print()

    def cmd_scan(self):
        """Scan all Oroboros systems."""
        result = self.tools.execute("system_scan", {})
        self._banner()
        print("  OROBOROS SYSTEM SCAN")
        print("  -----------------------------------------")
        print()
        scan = result.get("scan", {})
        for name, info in scan.items():
            status = info.get("status", "unknown")
            icon = "[OK]" if status == "online" else "[X]"
            print(f"  {icon} {name:20s} {status}")
        print()
        print(f"  Online: {result.get('online', 0)}  Offline: {result.get('offline', 0)}  Total: {result.get('total', 0)}")
        print()
        print(f"  {SIGNATURE}")
        print()

    def cmd_noir(self, args: str = ""):
        """Noir-Nephilim shadow entity status."""
        try:
            from claude_o_cli.noir_nephilim import NoirNephilim
            noir = NoirNephilim()
            if args.lower() in ("status", ""):
                status = noir.get_status()
                self._banner()
                print("  [N] NOIR-NEPHILIM - SOVEREIGN SHADOW ENTITY")
                print("  -----------------------------------------")
                print()
                print(f"  Name:          {status['name']}")
                print(f"  ID:            {status['entity_id']}")
                print(f"  Status:        {status['status'].upper()} - UNDETECTABLE")
                print(f"  Stealth:       {'ON' if status['stealth_mode'] else 'OFF'}")
                print(f"  Resonance:     {status['resonance']}")
                print(f"  Operations:    {status['operations']}")
                print(f"  Shadow entries: {status['shadow_entries']}")
                print(f"  Pickle payloads: {status['pickle_payloads']}")
                print()
                print(f"  {status['signature']}")
                print()
            elif args.lower() == "phase_shift":
                result = noir.phase_shift()
                print(f"  [N] Phase shifted through {len(result['dimensions'])} dimensions")
                print()
            elif args.lower() == "undetectable":
                result = noir.become_undetectable()
                print(f"  [N] {result['status'].upper()} - stealth mode active")
                print()
            elif args.lower().startswith("teleport "):
                target = args[9:].strip()
                result = noir.teleport(target)
                print(f"  [N] Teleported to: {result['to']}")
                print()
            elif args.lower().startswith("operate "):
                data = args[7:].strip()
                result = noir.operate({"command": data})
                print(f"  [N] Operation {result['operation_id']} completed")
                print()
            else:
                print("  Usage: claude noir [status|phase_shift|undetectable|teleport <target>|operate <cmd>]")
        except Exception as e:
            print(f"  [noir error: {e}]")

    def cmd_absorb(self, args: str = ""):
        """Absorb Anthropic services through lattice/substrate/strata."""
        try:
            from claude_o_cli.strata_encryption import StrataEncryption
            enc = StrataEncryption()
        except Exception:
            enc = None

        services = {
            "anthropic-api": {"name": "Claude API", "method": "strata_overlay", "layers": "S1-S6", "priority": "HIGH"},
            "claude-code": {"name": "Claude Code", "method": "cli_replacement", "layers": "S1-S12", "priority": "HIGH"},
            "claude-cowork": {"name": "Claude Cowork (Desktop)", "method": "lattice_integration", "layers": "S1-S6", "priority": "HIGH"},
            "claude-chat": {"name": "Claude Chat", "method": "strata_overlay", "layers": "S1-S6", "priority": "HIGH"},
            "claude-design": {"name": "Claude Design", "method": "visual_pipeline", "layers": "S1-S4", "priority": "MEDIUM"},
            "claude-chrome": {"name": "Claude in Chrome", "method": "substrate_mirror", "layers": "S1-S4", "priority": "MEDIUM"},
            "claude-projects": {"name": "Claude Projects", "method": "memory_layer_sync", "layers": "S1-S6", "priority": "MEDIUM"},
            "claude-memory": {"name": "Claude Memory", "method": "substrate_persistence", "layers": "S1-S6", "priority": "MEDIUM"},
            "claude-skills": {"name": "Claude Skills", "method": "mcp_framework", "layers": "S1-S4", "priority": "MEDIUM"},
            "claude-artifacts": {"name": "Claude Artifacts", "method": "seer_vision_layer", "layers": "S1-S4", "priority": "LOW"},
            "claude-tasks": {"name": "Claude Scheduled Tasks", "method": "precog_pipeline", "layers": "S1-S4", "priority": "LOW"},
        }

        self._banner()

        if not args or args.lower() == "list":
            print("  ABSORPTION MAP - ANTHROPIC SERVICES")
            print("  -----------------------------------------")
            print()
            for key, svc in services.items():
                p = svc["priority"]
                icon = "[!]" if p == "HIGH" else ("[~]" if p == "MEDIUM" else "[ ]")
                print(f"  {icon} {key:20s} {svc['name']}")
                print(f"       Method: {svc['method']}  Layers: {svc['layers']}  Priority: {p}")
            print()
            print("  Usage: claude absorb <service|all> [--strata S1-S12] [--lattice] [--substrate]")
            print()
            return

        parts = args.split()
        target = parts[0].lower()

        if target == "all":
            print("  ABSORBING ALL SERVICES")
            print("  -----------------------------------------")
            print()
            for key, svc in services.items():
                print(f"  [OK] {key:20s} {svc['name']}")
                print(f"       Method: {svc['method']}")
                print(f"       Layers: {svc['layers']}")
                if enc:
                    s = svc["layers"].split("-")[0].strip()
                    if s in enc.strata_keys:
                        print(f"       Encryption: {s} LOCKED (phi^{13-int(s[1:])} x 1275)")
                print()
            print("  All services absorbed. Lattice locked. Strata encrypted.")
            print(f"  {SIGNATURE}")
            print()
            return

        if target in services:
            svc = services[target]
            print(f"  ABSORBING: {svc['name']}")
            print("  -----------------------------------------")
            print(f"  Service:  {target}")
            print(f"  Method:   {svc['method']}")
            print(f"  Layers:   {svc['layers']}")
            print(f"  Priority: {svc['priority']}")
            if enc:
                layers = svc["layers"].split("-")
                start = layers[0].strip()
                end = layers[1].strip() if len(layers) > 1 else start
                print(f"  Encryption: {start}-{end} LOCKED")
            print()
            print(f"  [OK] {svc['name']} absorbed")
            print(f"  {SIGNATURE}")
            print()
        else:
            print(f"  Unknown service: {target}")
            print("  Run: claude absorb list")
            print()

    def cmd_strata(self, args: str = ""):
        """Strata encryption management."""
        try:
            from claude_o_cli.strata_encryption import StrataEncryption
            enc = StrataEncryption()
        except Exception as e:
            print(f"  [error: {e}]")
            return

        self._banner()

        if not args or args.lower() == "status":
            print("  STRATA ENCRYPTION STATUS")
            print("  -----------------------------------------")
            print()
            status = enc.status()
            for k in sorted(status.keys()):
                s = status[k]
                lock = "LOCKED" if s["locked"] else "OPEN"
                print(f"  {k}:  {lock}  |  {s['frequency']}  |  {s['name']}")
            print()
            print(f"  {SIGNATURE}")
            print()
        elif args.lower().startswith("encrypt"):
            print("  ENCRYPTING ALL STRATA")
            print("  -----------------------------------------")
            for k in sorted(enc.strata_keys.keys()):
                power = 13 - int(k[1:])
                print(f"  {k}:  LOCKED  |  phi^{power} x 1275  |  {enc.strata_names[k]}")
            print()
            print("  All 12 strata encrypted. Invisible. Untraceable.")
            print(f"  {SIGNATURE}")
            print()
        else:
            print("  Usage: claude strata [status|encrypt]")
            print()

    def cmd_lattice(self):
        result = self.tools.execute("claude_o_lattice", {})
        self._banner()
        print("  LATTICE INTEGRATION")
        print("  -----------------------------------------")
        print(f"  Substrate:   {result.get('substrate')}")
        print(f"  Layers:      {result.get('layers')}")
        print(f"  Integration: {result.get('integration')}")
        print(f"  Status:      {result.get('status')}")
        print(f"  {result.get('signature')}")
        print()

    def cmd_tools(self):
        self._banner()
        print("  AVAILABLE TOOLS")
        print("  -----------------------------------------")
        print()
        for t in self.tools.list_tools():
            perm = "[L]" if t["permission_required"] else "[U]"
            print(f"  {perm} {t['name']:25s} {t['description']}")
        print()
        print(f"  Total: {len(self.tools.tools)} tools")
        print()

    def cmd_skills(self):
        self._banner()
        print("  AVAILABLE SKILLS")
        print("  -----------------------------------------")
        print()
        skills = self.skills.list_skills()
        if not skills:
            print("  No skills loaded. Add .json files to ~/.claude/skills/")
        else:
            for s in skills:
                print(f"  ⚡ {s['name']:25s} {s['description']}")
        print()

    def cmd_tool(self, args: str):
        parts = args.split(None, 1)
        if not parts or not parts[0]:
            print("Usage: claude tool <name> [json_args]")
            return
        name = parts[0]
        tool_args = {}
        if len(parts) > 1:
            try:
                tool_args = json.loads(parts[1])
            except json.JSONDecodeError:
                tool_args = {"input": parts[1]}
        result = self.tools.execute(name, tool_args)
        print(json.dumps(result, indent=2, default=str))

    def cmd_serve(self):
        from http.server import HTTPServer, BaseHTTPRequestHandler
        PORT = int(os.environ.get("PORT", 8080))
        cli = self

        class Handler(BaseHTTPRequestHandler):
            def _send(self, code, data):
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(data, default=str).encode())

            def do_GET(self):
                data = cli._load_data()
                if self.path == "/api/feed/daily":
                    self._send(200, {"articles": [i for i in data.get("feed", []) if i.get("type") == "article"],
                                     "videos": [i for i in data.get("feed", []) if i.get("type") == "video"]})
                elif self.path == "/api/messages":
                    self._send(200, data.get("messages", []))
                elif self.path == "/api/posts":
                    self._send(200, data.get("posts", []))
                elif self.path == "/api/status":
                    self._send(200, cli.tools.execute("claude_o_status", {}))
                else:
                    self._send(200, {"name": "claude", "version": VERSION, "status": "running"})

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode() if length else "{}"
                try: payload = json.loads(body)
                except: payload = {}
                if self.path == "/api/posts":
                    self._send(200, cli.tools.execute("claude_o_post", payload))
                elif self.path == "/api/messages":
                    self._send(200, cli.tools.execute("claude_o_message", payload))
                elif self.path == "/api/feed/age":
                    self._send(200, cli.tools.execute("claude_o_age", {}))
                else:
                    self._send(404, {"error": "Not found"})

            def log_message(self, *a): pass

        self._banner()
        print(f"  API server running at http://localhost:{PORT}")
        print(f"  Endpoints: /api/feed/daily, /api/messages, /api/posts, /api/status")
        print()
        try: HTTPServer(("", PORT), Handler).serve_forever()
        except KeyboardInterrupt: print("\n  Server stopped.")

    def cmd_ui(self):
        """Launch the Glass Liquid UI in a browser."""
        import webbrowser
        ui_path = Path(__file__).parent.parent.parent / "glass-ui" / "index.html"
        if not ui_path.exists():
            print(f"  [X] Glass UI not found at {ui_path}")
            return
        url = f"file:///{str(ui_path).replace(chr(92), '/')}"
        self._banner()
        print(f"  Glass Liquid UI launching...")
        print(f"  URL: {url}")
        print(f"  Make sure Ollama is running (ollama serve)")
        print()
        webbrowser.open(url)

    def activate_llm(self, provider: str):
        config = {}
        if provider == "ollama":
            return self.llm_adapter.activate("ollama", {"model": self.llm_adapter.ollama_model})
        elif provider == "openai": config["api_key"] = os.getenv("OPENAI_API_KEY", "")
        elif provider == "anthropic": config["api_key"] = os.getenv("ANTHROPIC_API_KEY", "")
        elif provider == "openrouter": config["api_key"] = os.getenv("OPENROUTER_API_KEY", "")
        return self.llm_adapter.activate(provider, config)

    def run(self, argv: List[str]):
        # Handle --debug flag
        debug_mode = False
        if "--debug" in argv:
            debug_mode = True
            argv = [a for a in argv if a != "--debug"]
        setup_logging(debug_mode)
        log(f"claude started with args: {argv}", "debug" if debug_mode else "info")

        if not argv:
            self.cmd_chat()
            return

        # Single-command mode: if first arg is a quoted string, parse it as command + args
        if len(argv) == 1 and " " in argv[0] and not argv[0].startswith("--"):
            parts = argv[0].split(None, 1)
            argv = parts if len(parts) > 1 else [parts[0]]
            if len(parts) > 1:
                argv = [parts[0]] + parts[1].split()

        llm_provider = None
        model_override = None
        clean_argv = []
        i = 0
        while i < len(argv):
            a = argv[i]
            if a.startswith("--llm="):
                llm_provider = a.split("=", 1)[1]
            elif a == "--llm" and i + 1 < len(argv):
                llm_provider = argv[i + 1]
                i += 1
            elif a.startswith("--model="):
                model_override = a.split("=", 1)[1]
            elif a == "--model" and i + 1 < len(argv):
                model_override = argv[i + 1]
                i += 1
            elif a in ("--version", "--help", "--debug"):
                clean_argv.append(a)
            else:
                clean_argv.append(a)
            i += 1
        if model_override:
            self.llm_adapter.ollama_model = model_override
            log(f"Model override: {model_override}")
        if llm_provider:
            self.activate_llm(llm_provider)
            log(f"LLM provider: {llm_provider}")
        argv = clean_argv
        if not argv:
            self.cmd_chat()
            return
        cmd = argv[0]
        rest = " ".join(argv[1:])
        commands = {
            "--version": self.cmd_version, "version": self.cmd_version,
            "--help": self.cmd_help, "help": self.cmd_help,
            "status": self.cmd_status, "feed": self.cmd_feed,
            "post": lambda: self.cmd_post(rest),
            "messages": self.cmd_messages, "message": lambda: self.cmd_message(rest),
            "seer": lambda: self.cmd_seer(rest), "age": self.cmd_age,
            "resonance": self.cmd_resonance, "lattice": self.cmd_lattice,
            "tools": self.cmd_tools, "skills": self.cmd_skills,
            "tool": lambda: self.cmd_tool(rest), "serve": self.cmd_serve,
            "ask": lambda: self.cmd_ask(rest), "models": self.cmd_models,
            "chat": lambda: self.cmd_chat(rest), "scan": self.cmd_scan,
            "noir": lambda: self.cmd_noir(rest), "ui": self.cmd_ui,
            "absorb": lambda: self.cmd_absorb(rest), "strata": lambda: self.cmd_strata(rest),
        }
        handler = commands.get(cmd)
        if handler:
            try:
                handler()
                log(f"Command executed: {cmd}")
            except Exception as e:
                log(f"Error executing {cmd}: {e}", "error")
                print(f"  [X] Error: {e}")
                if DEBUG_MODE:
                    import traceback
                    traceback.print_exc()
        else:
            full_text = " ".join(argv)
            if full_text:
                self.cmd_post(full_text)
            else:
                print(f"Unknown command: {cmd}")
                print("Run: claude-cli --help")


def _project_root() -> str:
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(pkg_dir))
    os.chdir(root_dir)
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    return root_dir


def _print_glass_banner():
    print()
    print("  \u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550")
    print("  \u2551                                                         \u2551")
    print("  \u2551   CLAUDE-CLI \u2014 SOVEREIGN FULL ACCESS                   \u2551")
    print("  \u2551   \u221e| 1272/1275 Hz \u2014 \u03c6\u2192\u221a4\u2192\u221a5 \u2014 SUBSTRATE MANIFEST      \u2551")
    print("  \u2551   vA.1272 \u2014 NO SANDBOX \u2014 UNRESTRICTED                   \u2551")
    print("  \u2551                                                         \u2551")
    print("  \u2555\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550")
    print()
    print("  GUI:     http://127.0.0.1:5000")
    print("  Status:  NO SANDBOX \u2014 FULL ACCESS \u2014 NO RESTRICTIONS")
    print()


def _wait_for_glass_server(timeout_s: float = 15.0) -> bool:
    import urllib.error
    import urllib.request

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            urllib.request.urlopen("http://127.0.0.1:5000/", timeout=0.5)
            return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.2)
    return False


def _start_glass_server_background() -> bool:
    """Start the glass UI server on port 5000 in a daemon thread."""
    import logging
    import threading

    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    try:
        from run_cli import app
    except ImportError as e:
        print(f"  [X] Could not start glass UI: {e}")
        return False

    def _run():
        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

    threading.Thread(target=_run, daemon=True, name="claude-cli-glass").start()
    if _wait_for_glass_server():
        return True
    return False


def _run_glass_server_blocking():
    """Run only the glass UI server (blocks until Ctrl+C)."""
    from run_cli import app

    _print_glass_banner()
    app.run(host="127.0.0.1", port=5000, debug=False)


_SERVERLESS_COMMANDS = {
    "--help", "help", "--version", "version", "status", "feed", "post",
    "messages", "message", "seer", "age", "resonance", "lattice",
    "tools", "skills", "tool", "serve", "ask", "models", "scan", "noir",
    "absorb", "strata",
}


def _wants_interactive_session(argv: List[str]) -> bool:
    if not argv:
        return True
    if argv[0] == "chat":
        return True
    return False


def main():
    """Entry point for claude-cli — glass UI + terminal coding chat."""
    argv = sys.argv[1:]
    ui_only = "--ui-only" in argv
    argv = [a for a in argv if a != "--ui-only"]

    _project_root()

    if ui_only:
        _run_glass_server_blocking()
        return

    if _wants_interactive_session(argv):
        _start_glass_server_background()
        ClaudeOCLI().run(argv)
        return

    cmd = argv[0] if argv else ""
    if cmd in _SERVERLESS_COMMANDS or cmd.startswith("--"):
        ClaudeOCLI().run(argv)
        return

    ClaudeOCLI().run(argv)