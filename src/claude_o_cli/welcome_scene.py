"""Claude CLI welcome scene — Anthropic grey + orange (copied layout)."""
from __future__ import annotations

from typing import List, Tuple

# Anthropic brand (cli.html / Claude Code welcome)
ORANGE = (217, 119, 87)       # #D97757
GREY = (150, 145, 135)        # #969187
WARM = (245, 242, 237)        # #F5F2ED
DOT = (100, 97, 90)
GROUND = (183, 179, 172)

WIDTH = 72
DOT_LINE = "." * WIDTH

# Block mascot copied from Claude logo silhouette (no outline) — Claude Code scale
MASCOT_BLOCK = [
    "      ██      ",
    "    ██████    ",
    "  ██████████  ",
    "  ████ ██ ████ ",
    "  ██████████  ",
    "    ██  ██    ",
    "    ██  ██    ",
    "    ██  ██    ",
    "    ██  ██    ",
]

MOON_BLOCK = [
    "                    ▄▀▀▀▄",
    "                  ▄██████▄",
    "                 ████████▀ ",
    "                 ████████  ",
    "                  ▀████▀  ",
    "                    ▀▀    ",
]

# Scene rows: (text, kind) kind = orange|grey|warm|dot|ground
def _build_scene() -> List[Tuple[str, str]]:
    rows: List[Tuple[str, str]] = []
    h = max(len(MASCOT_BLOCK), len(MOON_BLOCK), 8)
    for i in range(h):
        left = MASCOT_BLOCK[i] if i < len(MASCOT_BLOCK) else " " * 14
        moon = MOON_BLOCK[i] if i < len(MOON_BLOCK) else ""
        mid_w = WIDTH - len(left) - len(moon)
        mid = [" "] * max(mid_w, 0)
        if i == 0 and mid_w > 10:
            mid[8] = "*"
        if i == 2 and mid_w > 14:
            cloud = " ░▒▒░░ "
            for j, ch in enumerate(cloud):
                if 4 + j < len(mid):
                    mid[4 + j] = ch
        if i == 4 and mid_w > 20:
            mid[min(mid_w - 8, len(mid) - 1)] = "*"
        line = (left + "".join(mid) + moon)[:WIDTH]
        rows.append((line.ljust(WIDTH), "scene"))
    return rows


def _rgb(c: Tuple[int, int, int]) -> str:
    return f"rgb({c[0]},{c[1]},{c[2]})"


def _paint_line(line: str, *, dim: bool = False) -> str:
    parts: List[str] = []
    factor = 0.55 if dim else 1.0
    for ch in line:
        if ch == "█":
            r, g, b = ORANGE
            if dim:
                r, g, b = int(r * factor), int(g * factor), int(b * factor)
            parts.append(f"[{_rgb((r, g, b))}]{ch}[/]")
        elif ch in "▄▀":
            rgb = GREY if dim else WARM
            parts.append(f"[{_rgb(rgb)}]{ch}[/]")
        elif ch in "░▒▓":
            parts.append(f"[{_rgb(GREY)}]{ch}[/]")
        elif ch == "*":
            parts.append(f"[{_rgb(WARM)}]*[/]")
        elif ch == "─":
            parts.append(f"[{_rgb(GROUND)}]─[/]")
        elif ch == ".":
            parts.append(f"[{_rgb(DOT)}].[/]")
        else:
            parts.append(ch)
    return "".join(parts)


def render_welcome_art(version: str = "vA.1272") -> List[str]:
    lines: List[str] = [
        f"[{_rgb(ORANGE)}]Welcome to Claude CLI {version}[/]",
        "",
        f"[{_rgb(DOT)}]{DOT_LINE}[/]",
    ]
    for row, _ in _build_scene():
        lines.append(_paint_line(row))
    ground = "      " + "─" * 28
    lines.append(_paint_line(ground))
    lines.append(f"[{_rgb(DOT)}]{DOT_LINE}[/]")
    lines.append("")
    lines.append(f"[{_rgb(GREY)}]  Sovereign local terminal · Ollama · no sandbox · full access · $0.00 API[/]")
    lines.append(
        f"[{_rgb(GREY)}]  Not Anthropic Claude Code — run [/][{_rgb(ORANGE)}]claude-cli[/]"
        f"[{_rgb(GREY)}] (Oroboros · local)[/]"
    )
    return lines


def render_welcome_html(version: str = "vA.1272") -> str:
    def span(ch: str, rgb: Tuple[int, int, int]) -> str:
        return f'<span style="color:rgb({rgb[0]},{rgb[1]},{rgb[2]})">{ch}</span>'

    rows = [
        f'<div class="digital-welcome-title">Welcome to Claude CLI {version}</div>',
        span(".", DOT) * WIDTH if False else f'<span style="color:rgb({DOT[0]},{DOT[1]},{DOT[2]})">{DOT_LINE}</span>',
    ]
    for line, _ in _build_scene():
        html = []
        for ch in line:
            if ch == "█":
                html.append(span(ch, ORANGE))
            elif ch in "▄▀":
                html.append(span(ch, WARM))
            elif ch in "░▒▓":
                html.append(span(ch, GREY))
            elif ch == "*":
                html.append(span(ch, WARM))
            elif ch == "─":
                html.append(span(ch, GROUND))
            elif ch == ".":
                html.append(span(ch, DOT))
            else:
                html.append(ch if ch != " " else " ")
        rows.append("".join(html))
    rows.append("      " + "".join(span("─", GROUND) for _ in range(28)))
    rows.append(f'<span style="color:rgb({DOT[0]},{DOT[1]},{DOT[2]})">{DOT_LINE}</span>')
    return "\n".join(rows)


def watermark_block() -> List[str]:
    """Small dim mascot above chat."""
    return [_paint_line(row, dim=True) for row in MASCOT_BLOCK]
