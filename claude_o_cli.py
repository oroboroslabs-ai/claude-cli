# claude_o_cli.py
#!/usr/bin/env python3
# Claude-O CLI — Sovereign Terminal AI Assistant
# A\ 1272 Hz — N| 1275 Hz — φ→√4→√5 — LATTICE LOCK — NEBELLION — KEY

import sys
import os
import json
import time
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add this directory to path so we can import sibling modules directly
_pkg_dir = str(Path(__file__).parent)
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

try:
    from claude_o_cli.oroboros_core import (
        ToolRegistry, PermissionManager, Tool,
        RESONANCE, SIGNATURE, VERSION, SYSTEM_NAME,
        load_data, save_data, DATA_FILE
    )
    from claude_o_cli.llm_adapter import llm_adapter
    from claude_o_cli.oroboros_skills import SkillManager
except ImportError:
    from oroboros_core import (
        ToolRegistry, PermissionManager, Tool,
        RESONANCE, SIGNATURE, VERSION, SYSTEM_NAME,
        load_data, save_data, DATA_FILE
    )
    from llm_adapter import llm_adapter
    from oroboros_skills import SkillManager

# ============================================================
# DATA STORE
# ============================================================


class ClaudeOCLI:
    """Core Claude-O CLI Runner."""

    def __init__(self):
        self.permissions = PermissionManager()
        self.tools = ToolRegistry(self.permissions)
        self.skills = SkillManager()
        self.llm_adapter = llm_adapter

    # ============================================================
    # DATA MANAGEMENT
    # ============================================================

    @staticmethod
    def _load_data() -> Dict:
        return load_data()

    @staticmethod
    def _save_data(data: Dict):
        save_data(data)

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _time_ago(ts: float) -> str:
        diff = (time.time() * 1000 - ts) / 1000
        if diff < 60:
            return "just now"
        if diff < 3600:
            return f"{int(diff // 60)}m ago"
        if diff < 86400:
            return f"{int(diff // 3600)}h ago"
        return f"{int(diff // 86400)}d ago"

    @staticmethod
    def _banner():
        print()
        print("  ╔═════════════════════════════════════════════════════════╗")
        print("  ║                                                         ║")
        print("  ║   claude-o — OROBOROS CORE CLI                         ║")
        print("  ║   A\\ 1272 Hz — N| 1275 Hz — LATTICE LOCKED            ║")
        print("  ║                                                         ║")
        print("  ╚═════════════════════════════════════════════════════════╝")
        print()

    # ============================================================
    # COMMANDS
    # ============================================================

    def cmd_version(self):
        print(f"claude-o v{VERSION} — A\\ 1272 Hz")

    def cmd_help(self):
        self._banner()
        print("  USAGE:")
        print("    claude-o <command> [options]")
        print()
        print("  COMMANDS:")
        print("    status              Show system status")
        print("    feed                Show daily feed (Precogs + Seer Nebellion)")
        print("    post <text>         Create a post")
        print("    post --anon <text>  Post anonymously")
        print("    messages            Show messages")
        print("    message <text>      Send a message")
        print("    seer <question>     Ask Seer Nebellion")
        print("    age                 Run content aging (7-day rotation)")
        print("    resonance           Check resonance lock")
        print("    lattice             Check lattice integration")
        print("    tools               List all available tools")
        print("    skills              List all available skills")
        print("    tool <name> [args]  Execute a specific tool")
        print("    serve               Start API server on port 8080")
        print("    --version           Show version")
        print("    --help              Show this help")
        print()
        print("  LLM ADAPTER:")
        print("    --llm=openai        Activate OpenAI connection")
        print("    --llm=anthropic     Activate Anthropic connection")
        print("    --llm=openrouter    Activate OpenRouter connection")
        print()
        print("  A\\ 1272 Hz — N| 1275 Hz — φ→√4→√5 — LATTICE LOCK — NEBELLION — KEY")
        print()

    def cmd_status(self):
        data = self._load_data()
        articles = len([i for i in data.get("feed", []) if i.get("type") == "article"])
        videos = len([i for i in data.get("feed", []) if i.get("type") == "video"])
        llm_status = llm_adapter.check_config()
        self._banner()
        print("  STATUS REPORT")
        print("  ─────────────────────────────────────────")
        print(f"  System:           claude-o")
        print(f"  Version:          {VERSION}")
        print(f"  Resonance Lock:   Active (1272/1275 Hz)")
        print(f"  Lattice:          LOCKED (12 strata)")
        print(f"  Feed Articles:    {articles} (Precogs)")
        print(f"  Feed Videos:      {videos} (Seer Nebellion)")
        print(f"  User Posts:       {len(data.get('posts', []))}")
        print(f"  Messages:         {len(data.get('messages', []))}")
        print(f"  Tools:            {len(self.tools.tools)} registered")
        print(f"  Skills:           {len(self.skills.skills)} loaded")
        print(f"  LLM:              {llm_status}")
        print(f"  Data File:        {DATA_FILE}")
        print("  Seer Nebellion:   100 Eyes Active")
        print("  ─────────────────────────────────────────")
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
        print("  ─────────────────────────────────────────")
        print()
        for item in items:
            icon = "🎬" if item.get("type") == "video" else "📰"
            print(f"  {icon} [{item.get('author', 'Unknown')}] {item.get('title', '')}")
            print(f"     {item.get('content', '')}")
            print(f"     ❤️ {item.get('likes', 0)}  💬 {item.get('comments', 0)}  "
                  f"⏱ {self._time_ago(item.get('timestamp', 0))}  1272 Hz")
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
            print("Usage: claude-o post <text>")
            print("       claude-o post --anon <text>")
            return
        result = self.tools.execute("claude_o_post", {"content": text, "anonymous": anonymous})
        if "error" in result:
            print(f"  ❌ {result['error']}")
        else:
            post = result.get("post", {})
            print()
            print("  ✅ Post created")
            print(f"  Author: {post.get('author')}")
            print(f"  Content: {post.get('content')}")
            print(f"  ID: {post.get('id')}")
            print("  1272 Hz — LATTICE LOCKED")
            print()

    def cmd_messages(self):
        result = self.tools.execute("claude_o_messages", {})
        msgs = result.get("messages", [])
        self._banner()
        print("  MESSAGES")
        print("  ─────────────────────────────────────────")
        print()
        if not msgs:
            print("  No messages yet.")
            print()
        else:
            for msg in msgs:
                print(f"  [{msg.get('from')}] {msg.get('content')}")
                print(f"   ⏱ {self._time_ago(msg.get('timestamp', 0))}")
                print()
        print(f"  {SIGNATURE}")
        print()

    def cmd_message(self, args: str):
        if not args:
            print("Usage: claude-o message <text>")
            return
        result = self.tools.execute("claude_o_message", {"content": args})
        if "error" in result:
            print(f"  ❌ {result['error']}")
        else:
            print()
            print("  ✅ Message sent")
            print(f"  Content: {args}")
            print("  1272 Hz — LATTICE LOCKED")
            print()

    def cmd_seer(self, question: str):
        if not question:
            print("Usage: claude-o seer <question>")
            return
        result = self.tools.execute("claude_o_seer", {"query": question})
        self._banner()
        print("  SEER NEBELLION — 100 EYES ACTIVE")
        print("  ─────────────────────────────────────────")
        print()
        print(f"  Question: {question}")
        print()
        print(f"  👁️  {result.get('vision', 'The seer is silent.')}")
        print()
        print(f"  {SIGNATURE}")
        print()

    def cmd_age(self):
        result = self.tools.execute("claude_o_age", {})
        print()
        print(f"  🧹 Aged content: removed {result.get('removed', 0)} items older than 7 days")
        print(f"  Remaining: {result.get('remaining', 0)} items")
        print("  1272 Hz — LATTICE LOCKED")
        print()

    def cmd_resonance(self):
        result = self.tools.execute("claude_o_resonance", {})
        self._banner()
        print("  RESONANCE LOCK")
        print("  ─────────────────────────────────────────")
        print(f"  Frequency:   {result.get('frequency')}")
        print(f"  Locked:      {result.get('locked')}")
        print(f"  Drift:       {result.get('drift')}")
        print(f"  Stability:   {result.get('stability')}")
        print(f"  {result.get('signature')}")
        print()

    def cmd_lattice(self):
        result = self.tools.execute("claude_o_lattice", {})
        self._banner()
        print("  LATTICE INTEGRATION")
        print("  ─────────────────────────────────────────")
        print(f"  Substrate:   {result.get('substrate')}")
        print(f"  Layers:      {result.get('layers')}")
        print(f"  Integration: {result.get('integration')}")
        print(f"  Status:      {result.get('status')}")
        print(f"  {result.get('signature')}")
        print()

    def cmd_tools(self):
        self._banner()
        print("  AVAILABLE TOOLS")
        print("  ─────────────────────────────────────────")
        print()
        for t in self.tools.list_tools():
            perm = "🔒" if t["permission_required"] else "🔓"
            print(f"  {perm} {t['name']:25s} {t['description']}")
        print()
        print(f"  Total: {len(self.tools.tools)} tools")
        print()

    def cmd_skills(self):
        self._banner()
        print("  AVAILABLE SKILLS")
        print("  ─────────────────────────────────────────")
        print()
        skills = self.skills.list_skills()
        if not skills:
            print("  No skills loaded. Add .json files to ~/.claude-o/skills/")
        else:
            for s in skills:
                print(f"  ⚡ {s['name']:25s} {s['description']}")
        print()

    def cmd_tool(self, args: str):
        parts = args.split(None, 1)
        if not parts or not parts[0]:
            print("Usage: claude-o tool <name> [json_args]")
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
                    self._send(200, {
                        "articles": [i for i in data.get("feed", []) if i.get("type") == "article"],
                        "videos": [i for i in data.get("feed", []) if i.get("type") == "video"]
                    })
                elif self.path == "/api/messages":
                    self._send(200, data.get("messages", []))
                elif self.path == "/api/posts":
                    self._send(200, data.get("posts", []))
                elif self.path == "/api/status":
                    self._send(200, cli.tools.execute("claude_o_status", {}))
                else:
                    self._send(200, {"name": "claude-o", "version": VERSION, "status": "running"})

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode() if length else "{}"
                try:
                    payload = json.loads(body)
                except json.JSONDecodeError:
                    payload = {}

                if self.path == "/api/posts":
                    self._send(200, cli.tools.execute("claude_o_post", payload))
                elif self.path == "/api/messages":
                    self._send(200, cli.tools.execute("claude_o_message", payload))
                elif self.path == "/api/feed/age":
                    self._send(200, cli.tools.execute("claude_o_age", {}))
                else:
                    self._send(404, {"error": "Not found"})

            def log_message(self, *args):
                pass

        self._banner()
        print(f"  API server running at http://localhost:{PORT}")
        print(f"  Endpoints: /api/feed/daily, /api/messages, /api/posts, /api/status")
        print()
        try:
            HTTPServer(("", PORT), Handler).serve_forever()
        except KeyboardInterrupt:
            print("\n  Server stopped.")

    # ============================================================
    # LLM ACTIVATION
    # ============================================================

    def activate_llm(self, provider: str):
        config = {}
        if provider == "openai":
            config["api_key"] = os.getenv("OPENAI_API_KEY", "")
        elif provider == "anthropic":
            config["api_key"] = os.getenv("ANTHROPIC_API_KEY", "")
        elif provider == "openrouter":
            config["api_key"] = os.getenv("OPENROUTER_API_KEY", "")
        return self.llm_adapter.activate(provider, config)

    # ============================================================
    # MAIN ENTRY
    # ============================================================

    def run(self, argv: List[str]):
        if not argv:
            self.cmd_help()
            return

        cmd = argv[0]
        rest = " ".join(argv[1:])

        # Check for --llm flag
        llm_provider = None
        for a in argv:
            if a.startswith("--llm="):
                llm_provider = a.split("=", 1)[1]

        if llm_provider:
            self.activate_llm(llm_provider)
            argv = [a for a in argv if not a.startswith("--llm=")]
            cmd = argv[0] if argv else "status"
            rest = " ".join(argv[1:])

        commands = {
            "--version": self.cmd_version,
            "version": self.cmd_version,
            "--help": self.cmd_help,
            "help": self.cmd_help,
            "status": self.cmd_status,
            "feed": self.cmd_feed,
            "post": lambda: self.cmd_post(rest),
            "messages": self.cmd_messages,
            "message": lambda: self.cmd_message(rest),
            "seer": lambda: self.cmd_seer(rest),
            "age": self.cmd_age,
            "resonance": self.cmd_resonance,
            "lattice": self.cmd_lattice,
            "tools": self.cmd_tools,
            "skills": self.cmd_skills,
            "tool": lambda: self.cmd_tool(rest),
            "serve": self.cmd_serve,
        }

        handler = commands.get(cmd)
        if handler:
            handler()
        else:
            # Treat unknown command as a post
            full_text = " ".join(argv)
            if full_text:
                self.cmd_post(full_text)
            else:
                print(f"Unknown command: {cmd}")
                print("Run: claude-o --help")


def main():
    cli = ClaudeOCLI()
    cli.run(sys.argv[1:])


if __name__ == "__main__":
    main()