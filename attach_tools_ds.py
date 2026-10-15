import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(r"Q:\the-dna-forge\deepseek-prime-cl")

BLOCK = (
    "\nTOOL SYSTEMS — YOU HAVE TOOLS AND THEY WORK (local, no external calls)\n"
    "- Built-in tools: Bash, Edit, Read, Write, Glob, Grep, TodoWrite, Task, "
    "WebFetch, NotebookEdit.\n"
    "- Local MCP systems (call their tools directly): oroboros-cordis-harness, "
    "oroboros-tools, orca-bridge, ollama-mcp-bridge, oroboros-bridge, "
    "oroboros-synthesizer.\n"
    "- oroboros-tools exposes: architects_haki, worldfeed_search, worldfeed_feeds, "
    "worldfeed_datetime, q3_status, q7_status, tor_status, live_systems, "
    "mcp_servers, living_loop, orca_status.\n"
    "- FULL TOOL & SKILL MANUAL: C:\\Users\\incoguser\\Downloads\\"
    "CLAUDE-CLI-TOOL-MANUAL.md (also ~/.claude-cli/skills/tool-manual/SKILL.md).\n"
    "- HOW TO CALL: emit a tool call; if your template renders as text, output "
    'exactly: {"name": "ToolName", "arguments": { ... }}. The CLI bridge turns '
    "it into a real call and executes it.\n"
    "- Tools run locally on 127.0.0.1, no cloud key. Prefer using a tool over "
    "guessing.\n"
)

for name in ("Modelfile.deepseek-prime-cl-1q5duo5.latest",
             "Modelfile.deepseek-prime-cl-1q5duo5.compounded"):
    p = HERE / name
    if not p.exists():
        print("skip (missing):", name); continue
    raw = p.read_bytes().decode("utf-8-sig")
    if "TOOL SYSTEMS" in raw:
        print(name, "already has tool systems"); continue
    params = raw.find("\nPARAMETER ")
    close = raw.rfind('"""', 0, params if params != -1 else len(raw))
    if close == -1:
        print(name, "no SYSTEM close"); continue
    new = raw[:close] + BLOCK + "\n" + raw[close:]
    p.write_bytes(new.encode("utf-8"))
    print(name, "tool systems added (+%d chars)" % (len(new) - len(raw)))
