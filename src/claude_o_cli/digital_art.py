"""Digital terminal chrome — uses braille art from logo PNG (Claude Code method)."""
from __future__ import annotations

from typing import Iterable, List

from claude_o_cli.braille_art import (
    MASCOT_RGB,
    load_mascot_braille,
    render_welcome_art,
)

TABS = ("Chat", "Files", "MCP", "Agent")

COMMAND_CHIPS = (
    "/exit", "/clear", "/model <name>", "/models", "/permissions", "/help",
    "/status", "/tools", "/worldfeed", "/seer", "/lattice", "/resonance", "/noir",
)

COMMANDS = COMMAND_CHIPS

DIGITAL_HEADER = (
    "◆ CLAUDE-CLI  vA.1272",
    "● ZTA: ACTIVE    ● RGE: GOVERNING    ● Audit: LOGGING",
    "A\\ 1272 Hz — N| 1275 Hz — φ→√4→√5 — CLAUDE — KEY",
)


def welcome_banner_lines(version: str = "vA.1272") -> List[str]:
    """Braille welcome from claude-mascot.png — matches Claude Code craft."""
    return render_welcome_art(version)


def watermark_block() -> List[str]:
    """Dim braille mascot watermark for chat area."""
    lines: List[str] = []
    for text, rgb in load_mascot_braille(cols=14):
        r, g, b = rgb
        dim = tuple(max(0, c // 3) for c in (r, g, b))
        line = "".join(
            f"[rgb({dim[0]},{dim[1]},{dim[2]})]{ch}[/]" if ord(ch) >= 0x2800 else " "
            for ch in text
        )
        lines.append(line)
    return lines


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
    r, g, b = MASCOT_RGB
    for line in DIGITAL_HEADER:
        if line.startswith("◆"):
            yield f"[rgb({r},{g},{b})]◆[/][bold orange]{line[1:]}[/]"
        elif "1272 Hz" in line:
            yield f"[dim warm_grey]{line}[/]"
        else:
            yield f"[warm_grey]{line}[/]"
