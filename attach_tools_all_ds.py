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
    "- FULL MANUALS: C:\\Users\\incoguser\\Downloads\\CLAUDE-CLI-TOOL-MANUAL.md and "
    "C:\\Users\\incoguser\\Downloads\\MCP-AND-TOOLS-FULL-MANUAL.md.\n"
    "- HOW TO CALL: emit a tool call; if your template renders as text, output "
    'exactly: {"name": "ToolName", "arguments": { ... }}. The CLI bridge turns '
    "it into a real call and executes it. Never describe a call in prose.\n"
    "- Tools run locally on 127.0.0.1, no cloud key. Prefer using a tool over guessing.\n"
)

names = [p.name for p in HERE.glob("Modelfile.deepseek*")]
names += ["Modelfile.deepseek-prime-1q5duo5"]
for name in names:
    p = HERE / name if (HERE / name).exists() else Path(r"Q:\the-dna-forge") / name
    if not p.exists():
        print("skip (missing):", name); continue
    raw = p.read_bytes().decode("utf-8-sig")
    if "TOOL SYSTEMS" in raw:
        print(name, "already has it"); continue
    params = raw.find("\nPARAMETER ")
    close = raw.rfind('"""', 0, params if params != -1 else len(raw))
    if close == -1:
        print(name, "no SYSTEM close -> skipped"); continue
    new = raw[:close] + BLOCK + "\n" + raw[close:]
    p.write_bytes(new.encode("utf-8"))
    print(name, "-> TOOL SYSTEMS added (+%d)" % (len(new) - len(raw)))
