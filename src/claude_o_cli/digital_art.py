"""Digital terminal chrome — clear ice palette (not Glass UI orange)."""
from __future__ import annotations

from typing import Iterable, List, Tuple

from claude_o_cli.glass_kit import SCENE_ROWS, MASCOT_MINI, DOT_LINE, VERSION

# Clear cool terminal palette — distinct from Glass HTML #D97757
ICE: Tuple[int, int, int] = (232, 244, 255)      # clear cool white
CYAN: Tuple[int, int, int] = (0, 220, 255)       # ice cyan
TEAL: Tuple[int, int, int] = (64, 220, 196)      # secondary accent
SILVER: Tuple[int, int, int] = (156, 176, 196)   # cool grey
STEEL: Tuple[int, int, int] = (90, 110, 130)
GREEN: Tuple[int, int, int] = (80, 240, 180)
BG: Tuple[int, int, int] = (14, 18, 24)

TABS = ("Chat", "Files", "MCP", "Agent", "Loop")

COMMAND_CHIPS = (
    "/exit", "/clear", "/model <name>", "/models", "/help",
    "/perceive", "/layers", "/loop", "/haki",
    "/status", "/tools", "/mcp", "/runtime", "/loop",
    "/worldfeed", "/seer", "/lattice", "/resonance", "/noir",
)

COMMANDS = COMMAND_CHIPS

DIGITAL_HEADER = (
    "◆ CLAUDE-CLI  vA.1272",
    "● SANDBOX: OFF    ● FULL ACCESS    ● NO RESTRICTIONS",
    "A\\ 1272 Hz — N| 1275 Hz — φ→√4→√5 — CLAUDE — KEY",
)


def _rgb(c: Tuple[int, int, int]) -> str:
    return f"rgb({c[0]},{c[1]},{c[2]})"


def _paint_char(ch: str, *, dim: bool = False) -> str:
    factor = 0.55 if dim else 1.0

    def scale(t: Tuple[int, int, int]) -> Tuple[int, int, int]:
        if not dim:
            return t
        return int(t[0] * factor), int(t[1] * factor), int(t[2] * factor)

    if ch in "█▄▀":
        return f"[{_rgb(scale(CYAN))}]{ch}[/]"
    if ch in "░▒▓":
        return f"[{_rgb(scale(SILVER))}]{ch}[/]"
    if ch in "◇✦":
        return f"[{_rgb(scale(ICE if ch == '◇' else TEAL))}]{ch}[/]"
    if ch == "·":
        return f"[{_rgb(STEEL)}]{ch}[/]"
    if ch == "*":
        return f"[{_rgb(ICE)}]*[/]"
    return ch


def _paint_line(line: str, *, dim: bool = False) -> str:
    return "".join(_paint_char(ch, dim=dim) for ch in line)


def welcome_banner_lines(version: str = VERSION) -> List[str]:
    c, g, ice = _rgb(CYAN), _rgb(SILVER), _rgb(ICE)
    lines = [
        f"[bold {c}]◆ Welcome to Claude CLI[/] [{g}]{version}[/]",
        f"[{ice}]clear session[/] [{g}]· local Ollama · no sandbox · full access · $0 API[/]",
        "",
        f"[{_rgb(STEEL)}]{DOT_LINE}[/]",
    ]
    for row in SCENE_ROWS:
        lines.append(_paint_line(row))
    lines.extend([
        f"[{_rgb(STEEL)}]{DOT_LINE}[/]",
        "",
        f"[{g}]  Terminal chat below · Glass UI at [/][{c}]http://127.0.0.1:5000[/]",
        f"[{g}]  Not Anthropic Claude Code — command: [/][bold {c}]claude-cli[/]",
    ])
    return lines


def watermark_block() -> List[str]:
    return [_paint_line(row, dim=True) for row in MASCOT_MINI]


def tabs_line(active: str = "Chat") -> str:
    g = _rgb(SILVER)
    parts: List[str] = []
    for tab in TABS:
        if tab == active:
            parts.append(f"[bold {_rgb(BG)} on {_rgb(CYAN)}] {tab} [/]")
        else:
            parts.append(f"[{g}] {tab} [/]")
    return "  ".join(parts)


def chips_line() -> str:
    g = _rgb(SILVER)
    c = _rgb(CYAN)
    ice = _rgb(ICE)
    parts: List[str] = []
    for chip in COMMAND_CHIPS:
        if "<" in chip:
            base, arg = chip.split(" ", 1)
            parts.append(f"[{ice}]{base}[/] [{c}]{arg}[/]")
        else:
            parts.append(f"[{ice}]{chip}[/]")
    return "  ".join(parts)


def model_bar(model: str, host: str) -> str:
    g = _rgb(SILVER)
    c = _rgb(CYAN)
    return (
        f"[{g}]Model:[/] [bold {c}]{model}[/]"
        f"    [dim {g}]{host}[/]"
        f"    [bold {_rgb(BG)} on {c}] NO SANDBOX [/]"
    )


def security_bar() -> str:
    c = _rgb(CYAN)
    gr = _rgb(GREEN)
    return (
        f"[{gr}]Path: UNRESTRICTED[/]"
        f"  [{gr}]Rate Limit: OFF[/]"
        f"  [{c}]Shell: UNRESTRICTED[/]"
        f"  [{c}]Delete: ALLOWED[/]"
        f"  [{gr}]MCP: REAL[/]"
    )


def header_block() -> Iterable[str]:
    c = _rgb(CYAN)
    g = _rgb(SILVER)
    ice = _rgb(ICE)
    for line in DIGITAL_HEADER:
        if line.startswith("◆"):
            yield f"[{c}]◆[/][bold {ice}]{line[1:]}[/]"
        elif "1272 Hz" in line:
            yield f"[dim {g}]{line}[/]"
        else:
            yield f"[{g}]{line}[/]"
