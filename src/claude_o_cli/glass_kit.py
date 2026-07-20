"""Claude CLI glass brand kit — tokens, welcome art, mascot (terminal + HTML)."""
from __future__ import annotations

from typing import Iterable, List, Tuple

# Glass UI tokens (match glass-ui/index.html :root)
ORANGE: Tuple[int, int, int] = (217, 119, 87)   # #D97757
CYAN: Tuple[int, int, int] = (0, 255, 204)      # #00ffcc
GOLD: Tuple[int, int, int] = (213, 160, 33)     # #d5a021
GREY: Tuple[int, int, int] = (183, 179, 172)    # #b7b3ac
WARM: Tuple[int, int, int] = (232, 229, 221)    # #e8e5dd
DOT: Tuple[int, int, int] = (100, 97, 90)
BG: Tuple[int, int, int] = (26, 25, 23)         # #1A1917
GREEN: Tuple[int, int, int] = (0, 255, 136)

VERSION = "vA.1272"
WIDTH = 62
DOT_LINE = "·" * WIDTH

# Oroboros glass welcome — mascot left, cyan orb + gold ring right
SCENE_ROWS: Tuple[str, ...] = (
    "                                                          ",
    "            ░░░░░░                          ◇            ",
    "    ░░░   ░░░░░░░░░░                    ░▒▒▒▒░           ",
    "   ░░░░░░░░░░░░░░░░░░░              ▒▒▓▓▓▓▒▒            ",
    "                                                          ",
    "      ██▄█████▄██                      ✦                 ",
    "      █████████                         ░▒▓▓▒░           ",
    "      █ █   █ █                          ◇               ",
    "      ▀▀▀▀▀▀▀▀▀                          ·              ",
)

MASCOT_MINI: Tuple[str, ...] = (
    "  ██▄██  ",
    "  █████  ",
    "  █ █ █  ",
    "  ▀▀▀▀▀  ",
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
        return f"[{_rgb(scale(ORANGE))}]{ch}[/]"
    if ch in "░▒▓":
        return f"[{_rgb(GREY)}]{ch}[/]"
    if ch in "◇✦":
        return f"[{_rgb(CYAN if ch == '◇' else GOLD)}]{ch}[/]"
    if ch == "·":
        return f"[{_rgb(DOT)}]{ch}[/]"
    if ch == "*":
        return f"[{_rgb(WARM)}]*[/]"
    return ch


def _paint_line(line: str, *, dim: bool = False) -> str:
    return "".join(_paint_char(ch, dim=dim) for ch in line)


def _html_char(ch: str) -> str:
    colors = {
        "█": ORANGE, "▄": ORANGE, "▀": ORANGE,
        "░": GREY, "▒": GREY, "▓": GREY,
        "◇": CYAN, "✦": GOLD, "·": DOT,
    }
    if ch in colors:
        c = colors[ch]
        return f'<span style="color:rgb({c[0]},{c[1]},{c[2]})">{ch}</span>'
    if ch == " ":
        return " "
    return ch


def render_welcome_art(version: str = VERSION) -> List[str]:
    o, c, g = _rgb(ORANGE), _rgb(CYAN), _rgb(GREY)
    lines = [
        f"[bold {o}]◆ Welcome to Claude CLI[/] [{g}]{version}[/]",
        f"[{c}]clear session[/] [{g}]· local Ollama · no sandbox · full access · $0 API[/]",
        "",
        f"[{_rgb(DOT)}]{DOT_LINE}[/]",
    ]
    for row in SCENE_ROWS:
        lines.append(_paint_line(row))
    lines.extend([
        f"[{_rgb(DOT)}]{DOT_LINE}[/]",
        "",
        f"[{g}]  Terminal chat below · Glass UI at [/][{o}]http://127.0.0.1:5000[/]",
        f"[{g}]  Not Anthropic Claude Code — command: [/][bold {o}]claude-cli[/]",
    ])
    return lines


def render_welcome_html(version: str = VERSION) -> str:
    rows = [
        f'<div class="digital-welcome-title">◆ Welcome to Claude CLI {version}</div>',
        f'<div class="digital-welcome-sub">Glass session · local Ollama · ZTA hardened</div>',
        f'<span style="color:rgb({DOT[0]},{DOT[1]},{DOT[2]})">{DOT_LINE}</span>',
    ]
    for line in SCENE_ROWS:
        rows.append("".join(_html_char(ch) for ch in line))
    rows.append(f'<span style="color:rgb({DOT[0]},{DOT[1]},{DOT[2]})">{DOT_LINE}</span>')
    return "\n".join(rows)


def watermark_block() -> List[str]:
    return [_paint_line(row, dim=True) for row in MASCOT_MINI]


def console_seed_message() -> str:
    return (
        "Claude CLI glass console ready.\n"
        "Type a message or /help for commands. "
        "This panel mirrors the terminal chat — same model, same local Ollama backend."
    )
