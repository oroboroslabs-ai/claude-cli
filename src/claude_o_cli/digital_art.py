"""Digital xxoo / block-art for Claude CLI terminal — Claude Code-style welcome."""
from __future__ import annotations

from typing import Iterable, List

# Claude mascot (logo without white outline) — X = body, @ = eye, . = empty
CLAUDE_MASCOT = [
    "......XXXXXX......",
    "...XXXXXXXXXXXX...",
    "..XXXXXXXXXXXXXX..",
    "..XXX@XXXX@XXXXX..",
    "..XXXXXXXXXXXXXX..",
    "...XX........XX...",
    "...XX........XX...",
    "...XX........XX...",
    "...XX........XX...",
]

# Compact mascot for inline / watermark use
CLAUDE_MASCOT_SM = [
    "..XXXX..",
    ".XXXXXX.",
    "XX@XX@XX",
    ".XXXXXX.",
    ".X....X.",
    ".X....X.",
]

# Welcome scene — Claude Code-style dot frame + night sky + mascot + moon
WELCOME_FRAME_WIDTH = 72
WELCOME_DOT_LINE = "." * WELCOME_FRAME_WIDTH

# Layer keys: . empty  X mascot  @ eye  * star  M moon  o cloud  - ground
WELCOME_SCENE = [
    ".  *         ooooooo                              **    *          .",
    ".                  XXXXXX                              MMMMMMM       .",
    ".                 XXXXXXXX                            MMMMMMMMM     .",
    ".    *            XXXXXXXX         ooo               MMMMMMMMM     .",
    ".                 XX@XX@XXX              *             MMMMMMM      .",
    ".                  XXXXXXXX                              MMMMM       .",
    ".        ooooo       XX  XX                                MMM        .",
    ".                     XX  XX                                         .",
    ".  ----------------------------------------------------------------  .",
]

# Full-width interface chrome matching glass UI screenshot
DIGITAL_HEADER = (
    "◆ CLAUDE-CLI  vA.1272",
    "● ZTA: ACTIVE    ● RGE: GOVERNING    ● Audit: LOGGING",
    "A\\ 1272 Hz — N| 1275 Hz — φ→√4→√5 — CLAUDE — KEY",
)

TABS = ("Chat", "Files", "MCP", "Agent")

COMMAND_CHIPS = (
    "/exit", "/clear", "/model <name>", "/models", "/permissions", "/help",
    "/status", "/tools", "/worldfeed", "/seer", "/lattice", "/resonance", "/noir",
)

# Back-compat alias used by cmd_chat help
COMMANDS = COMMAND_CHIPS


def _paint_mascot_line(line: str, *, dim: bool = False) -> str:
    """Return rich markup for one mascot/scene line."""
    parts: List[str] = []
    for ch in line:
        if ch == "X":
            parts.append("[dim orange]X[/]" if dim else "[orange]X[/]")
        elif ch == "@":
            parts.append("[black on orange]@[/]" if not dim else "[dim]@[/]")
        elif ch == "M":
            parts.append("[dim white]M[/]" if dim else "[white]M[/]")
        elif ch == "*":
            parts.append("[white]*[/]")
        elif ch == "o":
            parts.append("[dim warm_grey]o[/]")
        elif ch == "-":
            parts.append("[warm_grey]-[/]")
        elif ch == ".":
            parts.append("[warm_grey].[/]" if not dim else "[dim warm_grey].[/]")
        else:
            parts.append(ch)
    return "".join(parts)


def mascot_lines(*, dim: bool = False) -> List[str]:
    return [_paint_mascot_line(row, dim=dim) for row in CLAUDE_MASCOT]


def welcome_banner_lines(version: str = "vA.1272") -> List[str]:
    """Claude Code-style welcome block with xxoo digital art."""
    lines: List[str] = []
    lines.append(f"[orange]Welcome to Claude CLI {version}[/]")
    lines.append("")
    lines.append(f"[warm_grey]{WELCOME_DOT_LINE}[/]")
    for row in WELCOME_SCENE:
        lines.append(_paint_mascot_line(row))
    lines.append(f"[warm_grey]{WELCOME_DOT_LINE}[/]")
    lines.append("")
    lines.append("[warm_grey]  Sovereign local terminal · Ollama · ZTA Hardened · $0.00 API cost[/]")
    lines.append("[warm_grey]  Not Anthropic Claude Code — this is [/][cyan]claude-cli[/][warm_grey] (Oroboros)[/]")
    return lines


def watermark_block() -> List[str]:
    """Faint background mascot for chat area."""
    return mascot_lines(dim=True)


def tabs_line(active: str = "Chat") -> str:
    parts: List[str] = []
    for tab in TABS:
        if tab == active:
            parts.append(f"[bold cyan on grey23] {tab} [/]")
        else:
            parts.append(f"[warm_grey] {tab} [/]")
    return "  ".join(parts)


def chips_line() -> str:
    parts: List[str] = []
    for chip in COMMAND_CHIPS:
        if "<" in chip:
            base, arg = chip.split(" ", 1)
            parts.append(f"[white]{base}[/] [orange]{arg}[/]")
        else:
            parts.append(f"[white]{chip}[/]")
    return "  ".join(parts)


def model_bar(model: str, host: str) -> str:
    return (
        f"[warm_grey]Model:[/] [bold cyan]{model}[/]"
        f"    [dim]{host}[/]"
        f"    [bold gold on grey23] ZTA HARDENED [/]"
    )


def security_bar() -> str:
    return (
        "[green]Path Whitelist: ACTIVE[/]"
        "  [green]Rate Limit: 60/min[/]"
        "  [gold]Shell: ACTIVE[/]"
        "  [orange]Delete: DENIED[/]"
        "  [green]MCP: REAL[/]"
    )


def header_block() -> Iterable[str]:
    for line in DIGITAL_HEADER:
        if line.startswith("◆"):
            yield f"[orange]{line[:1]}[/][bold orange]{line[1:]}[/]"
        elif "1272 Hz" in line:
            yield f"[dim warm_grey]{line}[/]"
        else:
            yield f"[warm_grey]{line}[/]"
