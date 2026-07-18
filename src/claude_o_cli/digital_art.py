"""Digital terminal chrome — Anthropic grey + orange welcome + CLI panels."""
from __future__ import annotations

from typing import Iterable, List

from claude_o_cli.welcome_scene import ORANGE, GREY, render_welcome_art, watermark_block

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
    return render_welcome_art(version)


def tabs_line(active: str = "Chat") -> str:
    o = f"rgb({ORANGE[0]},{ORANGE[1]},{ORANGE[2]})"
    g = f"rgb({GREY[0]},{GREY[1]},{GREY[2]})"
    parts: List[str] = []
    for tab in TABS:
        if tab == active:
            parts.append(f"[bold rgb(0,255,204) on grey23] {tab} [/]")
        else:
            parts.append(f"[{g}] {tab} [/]")
    return "  ".join(parts)


def chips_line() -> str:
    g = f"rgb({GREY[0]},{GREY[1]},{GREY[2]})"
    o = f"rgb({ORANGE[0]},{ORANGE[1]},{ORANGE[2]})"
    parts: List[str] = []
    for chip in COMMAND_CHIPS:
        if "<" in chip:
            base, arg = chip.split(" ", 1)
            parts.append(f"[rgb(245,242,237)]{base}[/] [{o}]{arg}[/]")
        else:
            parts.append(f"[rgb(245,242,237)]{chip}[/]")
    return "  ".join(parts)


def model_bar(model: str, host: str) -> str:
    g = f"rgb({GREY[0]},{GREY[1]},{GREY[2]})"
    o = f"rgb({ORANGE[0]},{ORANGE[1]},{ORANGE[2]})"
    return (
        f"[{g}]Model:[/] [bold rgb(0,255,204)]{model}[/]"
        f"    [dim {g}]{host}[/]"
        f"    [bold {o} on grey23] ZTA HARDENED [/]"
    )


def security_bar() -> str:
    g = f"rgb({GREY[0]},{GREY[1]},{GREY[2]})"
    o = f"rgb({ORANGE[0]},{ORANGE[1]},{ORANGE[2]})"
    return (
        f"[rgb(0,255,136)]Path Whitelist: ACTIVE[/]"
        f"  [rgb(0,255,136)]Rate Limit: 60/min[/]"
        f"  [{o}]Shell: ACTIVE[/]"
        f"  [{o}]Delete: DENIED[/]"
        f"  [rgb(0,255,136)]MCP: REAL[/]"
    )


def header_block() -> Iterable[str]:
    o = f"rgb({ORANGE[0]},{ORANGE[1]},{ORANGE[2]})"
    g = f"rgb({GREY[0]},{GREY[1]},{GREY[2]})"
    for line in DIGITAL_HEADER:
        if line.startswith("◆"):
            yield f"[{o}]◆[/][bold {o}]{line[1:]}[/]"
        elif "1272 Hz" in line:
            yield f"[dim {g}]{line}[/]"
        else:
            yield f"[{g}]{line}[/]"
