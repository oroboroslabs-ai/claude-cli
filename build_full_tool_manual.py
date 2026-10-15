#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate the FULL MCP & tools manual: every tool, every argument, every step of
the call/execution flow. Covers all non-Oroboros (stock) tools plus the local
Oroboros tools. Writes to Downloads, the repo, and the CLI skills.
"""
import io, json, os, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
INV = json.loads(Path(r"Q:\claude-cli\tool_inventory.json").read_text(encoding="utf-8"))
DOWNLOADS = Path(os.path.expanduser(r"~\Downloads\MCP-AND-TOOLS-FULL-MANUAL.md"))
REPO = Path(r"Q:\claude-cli\better-clawd-src\oroboros-runtime\MCP-AND-TOOLS-FULL-MANUAL.md")
SKILL = Path.home() / ".claude-cli" / "skills" / "mcp-tools-full" / "SKILL.md"

# Oroboros' own servers (the user's); everything else is "stock"/not-theirs.
OROBOROS_OWN = {"oroboros-tools", "oroboros-bridge", "oroboros-synthesizer", "oroboros-cordis-harness"}

ORCA_SKILLS = [
    ("computer-use", "GUI control of a visible local app window via `orca computer` (accessibility tree, clicks, typing, screenshots). Not for Orca's embedded browser."),
    ("linear-tickets", "Linear ticket work through the Orca CLI (legacy alias of orca-linear)."),
    ("orca-cli", "Operate Orca worktrees, terminals, repos, automations, artifacts, skills, embedded browser via the `orca` CLI."),
    ("orca-emulator", "iOS Simulator control from inside Orca."),
    ("orca-emulator-android", "Android device/emulator control over adb."),
    ("orca-linear", "Linear ticket work through Orca's CLI."),
    ("orca-per-workspace-env", "Set up/debug/validate an Orca per-workspace environment recipe."),
    ("orchestration", "Coordinate supervised Orca workers: messages, task DAGs, decision gates, coordinator loops."),
]

TROUBLESHOOT = """
### 1. A single tool call returns an error
1. Read the error text — most are input validation (e.g. `orca_cli requires argv`).
2. Re-issue the call with the correct arguments (see its table above).
3. If it still fails, run the same action manually to isolate: built-in → run the
   shell/file command yourself; MCP → call the server directly (below).

### 2. The model narrates instead of calling ("Bash start chrome…", nothing runs)
1. Use a tool-capable model: `oroboros/claude-fable7-undecillion-sse`, `qwen2.5:14b`,
   or `llama3.2:latest` (`/model <name>`).
2. Ensure the call is one of the parsed forms: bare JSON, `<tool_call>{...}</tool_call>`,
   or a fenced ```json block.
3. If unsure whether the bridge is up: `curl http://127.0.0.1:11499/v1/models`.

### 3. An MCP server shows "Failed to connect"
1. Check the service is listening: `Test-NetConnection 127.0.0.1 -Port <port>`.
2. Run the connector to re-test and re-wire: `python Q:\\claude-cli\\connect_local_mcp.py`
   (it handshake-tests each and only writes the live ones).
3. stdio server missing a dependency (e.g. z-image-turbo needs torch): install it, then re-run.
4. HTTP server (e.g. 8789 harness): probe `/mcp` with an `initialize` POST.

### 4. Whole CLI unreachable (ECONNREFUSED)
1. Start the bridge: `python Q:\\claude-cli\\local_providers_shim.py`.
2. Or run the launcher, which starts it: `J:\\start_claude_cli.bat`.
3. Confirm Ollama: `curl http://127.0.0.1:11434/api/tags`.

### 5. Tool asks permission every time
Launch with `--dangerously-skip-permissions` (the launchers pass it).

### 6. Orca EPERM / agent won't start
Orca runs terminals under a persistent daemon → run Orca elevated, or launch the
CLI from `J:\\start_claude_cli_admin.bat`.

### 7. Recovery: full re-wire
```
python Q:\\claude-cli\\connect_local_mcp.py
python Q:\\claude-cli\\collect_tools.py     # refresh the inventory
python Q:\\claude-cli\\build_full_tool_manual.py
```
"""

BUILTIN = [
    ("Bash", "Execute a shell command on the host.", [("command", "string", "yes"), ("timeout", "number", "no"), ("description", "string", "no")]),
    ("Edit", "Exact string replacement in a file.", [("file_path", "string", "yes"), ("old_string", "string", "yes"), ("new_string", "string", "yes"), ("replace_all", "boolean", "no")]),
    ("Read", "Read a file or directory.", [("file_path", "string", "yes"), ("offset", "number", "no"), ("limit", "number", "no")]),
    ("Write", "Create or overwrite a file.", [("file_path", "string", "yes"), ("content", "string", "yes")]),
    ("Glob", "Find files by pattern.", [("pattern", "string", "yes"), ("path", "string", "no")]),
    ("Grep", "Search file contents by regex.", [("pattern", "string", "yes"), ("path", "string", "no"), ("include", "string", "no"), ("context", "number", "no"), ("limit", "number", "no")]),
    ("TodoWrite", "Maintain a structured task list.", [("todos", "array", "yes")]),
    ("Task", "Launch a subagent for multi-step work.", [("description", "string", "yes"), ("prompt", "string", "yes"), ("subagent_type", "string", "yes")]),
    ("WebFetch", "Fetch a URL to markdown/text/html.", [("url", "string", "yes"), ("format", "string", "no")]),
    ("NotebookEdit", "Edit a Jupyter notebook cell.", [("notebook_path", "string", "yes"), ("cell_id", "string", "no"), ("new_source", "string", "yes")]),
]


def args_of(schema):
    if not isinstance(schema, dict):
        return []
    props = schema.get("properties") or {}
    req = set(schema.get("required") or [])
    out = []
    for k, v in props.items():
        t = (v or {}).get("type", "any") if isinstance(v, dict) else "any"
        d = (v or {}).get("description", "") if isinstance(v, dict) else ""
        out.append((k, t, "yes" if k in req else "no", d))
    return out


def main():
    out = ["# MCP & TOOLS — FULL MANUAL (every step, every function)\n",
           "All tools run LOCALLY on 127.0.0.1. No cloud key. Command: `claude-cli`.\n",
           "## How a tool call flows (the logic, step by step)",
           "1. The CLI builds a request and includes the `tools[]` schema.",
           "2. The bridge (`:11499`) forwards `tools[]` to Ollama and converts each",
           "   Anthropic tool schema to an Ollama function schema.",
           "3. The model emits a call — natively (`tool_calls`) or as text:",
           '   `{"name":"Tool","arguments":{...}}`, `<tool_call>{...}</tool_call>`,',
           "   or a fenced ```json block. The bridge parses any of these.",
           "4. The bridge returns the call to the CLI as Anthropic `tool_use`.",
           "5. The CLI executes the tool (built-in locally; MCP via its server) and",
           "   sends the result back (`tool_result`) for the next turn.",
           "Never DESCRIBE a call in prose — emit it.\n",
           "---\n## A. Built-in tools (always available)\n"]
    for n, d, args in BUILTIN:
        out.append(f"### `{n}`\n{d}\n")
        if args:
            out.append("| arg | type | required | notes |")
            out.append("|---|---|---|---|")
            for a, t, r in args:
                out.append(f"| `{a}` | {t} | {r} | |")
        out.append("")

    out.append("---\n## B. MCP servers and every tool\n")
    for server, tools in INV.items():
        tag = "Oroboros" if server in OROBOROS_OWN else "stock / not Oroboros"
        out.append(f"### Server: `{server}`  ({len(tools)} tools) — {tag}\n")
        for t in tools:
            out.append(f"#### `{t['name']}`")
            if t.get("description"):
                out.append(t["description"])
            a = args_of(t.get("inputSchema"))
            if a:
                out.append("")
                out.append("| arg | type | required | notes |")
                out.append("|---|---|---|---|")
                for k, ty, r, note in a:
                    out.append(f"| `{k}` | {ty} | {r} | {note} |")
            out.append("")
        out.append("")

    out.append("---\n## C. Orca CLI skills (full command surface)\n")
    out.append("Orca exposes its full, version-matched guide via the CLI. Skills:\n")
    for name, desc in ORCA_SKILLS:
        out.append(f"- **{name}** — {desc}")
    out.append("")
    out.append("Core command groups (run `orca skills get orca-cli` for the full guide):")
    out.append("- `orca status --json` — app/runtime state")
    out.append("- `orca open --json` — start Orca if not running")
    out.append("- `orca worktree ps --json` — list worktrees")
    out.append("- `orca worktree current --json` — active worktree")
    out.append("- `orca terminal list|create|read|send|wait|close --json` — terminal control")
    out.append("- `orca computer ...` — GUI control of a visible window (computer-use)")
    out.append("- `orca browser ...` — embedded browser")
    out.append("- `orca artifacts ...` / `orca skills get|share` — artifacts and skills")
    out.append("")

    out.append("---\n## D. WHAT TO DO IF A TOOL OR SERVER FAILS (step by step)\n")
    out.append(TROUBLESHOOT)
    out.append("")

    out.append("---\n## E. Full tool inventory (JSON)\n")
    out.append("Raw schemas: `Q:\\claude-cli\\tool_inventory.json` and "
               "`oroboros-runtime\\tool_inventory.json`.\n")
    text = "\n".join(out)
    for p in (DOWNLOADS, REPO, SKILL):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    total = sum(len(v) for v in INV.values())
    print("manual written:", DOWNLOADS)
    print("repo:", REPO)
    print("skill:", SKILL)
    print(f"documented: {len(BUILTIN)} built-in + {total} MCP tools")


if __name__ == "__main__":
    main()
