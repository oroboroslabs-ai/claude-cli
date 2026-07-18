"""Image → Braille terminal art (Claude Code technique).

Claude Code renders startup art with Ink + Unicode block/braille chars and
truecolor ANSI. This module converts the Claude mascot PNG to braille cells
(2×4 pixels per U+2800 character) for faithful terminal reproduction.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Sequence, Tuple

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

# Braille dot bit map (ISO/IEC 10646)
_BRAILLE_BITS: Tuple[Tuple[int, int, int], ...] = (
    (0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (0, 3, 0x08),
    (1, 0, 0x10), (1, 1, 0x20), (1, 2, 0x40), (1, 3, 0x80),
)

MASCOT_PATH = Path(__file__).resolve().parents[2] / "glass-ui" / "claude-mascot.png"

# Claude terracotta from logo / brand
MASCOT_RGB = (217, 119, 87)
MOON_RGB = (232, 229, 221)
CLOUD_RGB = (120, 118, 112)
STAR_RGB = (245, 242, 237)
GROUND_RGB = (183, 179, 172)
DOT_RGB = (80, 78, 74)


def _luma(r: int, g: int, b: int) -> float:
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def image_to_braille_lines(
    path: Path,
    *,
    cols: int = 22,
    threshold: int = 140,
    invert: bool = False,
) -> List[Tuple[str, Tuple[int, int, int]]]:
    """Return list of (braille_line, rgb) from image. One color per row."""
    if Image is None or not path.exists():
        return []

    img = Image.open(path).convert("RGBA")
    aspect = img.height / max(img.width, 1)
    rows = max(4, int(cols * aspect * 2))  # braille rows ≈ 2× aspect of cols
    px_w, px_h = cols * 2, rows * 4
    img = img.resize((px_w, px_h), Image.Resampling.LANCZOS)

    lines: List[Tuple[str, Tuple[int, int, int]]] = []
    for cy in range(rows):
        chars: List[str] = []
        rs: List[int] = []
        gs: List[int] = []
        bs: List[int] = []
        for cx in range(cols):
            value = 0
            tr, tg, tb, count = 0, 0, 0, 0
            for px, py, bit in _BRAILLE_BITS:
                x, y = cx * 2 + px, cy * 4 + py
                if x >= px_w or y >= px_h:
                    continue
                r, g, b, a = img.getpixel((x, y))
                if a < 40:
                    continue
                lit = _luma(r, g, b) < threshold if not invert else _luma(r, g, b) > threshold
                if lit:
                    value |= bit
                    tr += r
                    tg += g
                    tb += b
                    count += 1
            chars.append(chr(0x2800 + value))
            if count:
                rs.append(tr // count)
                gs.append(tg // count)
                bs.append(tb // count)
        if rs:
            rgb = (sum(rs) // len(rs), sum(gs) // len(gs), sum(bs) // len(bs))
        else:
            rgb = MASCOT_RGB
        lines.append(("".join(chars), rgb))
    return lines


def _block_moon(width: int = 14) -> List[str]:
    """Crescent moon using Unicode block elements (Claude Code style)."""
    art = [
        "      ▄▀▀▀▄",
        "    ▄██████▄",
        "   ████████▀",
        "   ████████ ",
        "    ▀████▀ ",
        "      ▀▀   ",
    ]
    pad = max(0, width - len(art[0]))
    return [" " * pad + line for line in art]


def _block_cloud(col: int, width: int = 10) -> str:
    patterns = [
        " ░▒▒░░ ",
        "▒▒▒▒▒▒▒",
        " ░▒▒░░ ",
    ]
    row = patterns[col % len(patterns)]
    return row.center(width)


def compose_welcome_scene(
    mascot_lines: Sequence[Tuple[str, Tuple[int, int, int]]],
    *,
    width: int = 72,
) -> List[Tuple[str, Tuple[int, int, int] | None]]:
    """Compose mascot + sky + moon row layout like Claude Code welcome."""
    moon = _block_moon(12)
    scene_h = max(len(mascot_lines), len(moon), 9)
    moon_col = width - max(len(moon[0]), 16)

    out: List[Tuple[str, Tuple[int, int, int] | None]] = []
    for i in range(scene_h):
        parts: List[str] = []
        colors: List[Tuple[int, int, int] | None] = []

        # mascot column
        if i < len(mascot_lines):
            mtext, mrgb = mascot_lines[i]
            parts.append(mtext)
            colors.append(mrgb)
        else:
            parts.append("")
            colors.append(None)

        # sky middle
        mid_w = moon_col - len(parts[0])
        mid = [" "] * mid_w
        if i == 1:
            mid[min(4, mid_w - 1)] = "*"
        if i == 3 and mid_w > 12:
            cloud = _block_cloud(0, min(12, mid_w - 2))
            mid = list(cloud.ljust(mid_w))
        if i == 5 and mid_w > 8:
            mid[min(mid_w // 2, mid_w - 1)] = "*"
        parts.append("".join(mid))
        colors.append(None)

        # moon
        if i < len(moon):
            parts.append(moon[i])
            colors.append(MOON_RGB)
        else:
            parts.append("")
            colors.append(None)

        line = "".join(parts)[:width].ljust(width)
        # Row color: mascot color if row has mascot pixels else None (multi-style below)
        row_rgb = mascot_lines[i][1] if i < len(mascot_lines) else None
        out.append((line, row_rgb))
    return out


def braille_to_rich_segments(
    scene: Sequence[Tuple[str, Tuple[int, int, int] | None]],
) -> List[str]:
    """Convert composed scene to Rich markup lines with per-region truecolor."""
    rich_lines: List[str] = []
    moon = _block_moon(12)
    moon_start = 72 - len(moon[0]) if moon else 50

    for i, (line, row_rgb) in enumerate(scene):
        if not line.strip():
            rich_lines.append("")
            continue
        parts: List[str] = []
        for j, ch in enumerate(line):
            if ch == " ":
                parts.append(" ")
            elif ch == "*":
                parts.append(f"[rgb({STAR_RGB[0]},{STAR_RGB[1]},{STAR_RGB[2]})]*[/]")
            elif ch in "░▒▓":
                parts.append(f"[rgb({CLOUD_RGB[0]},{CLOUD_RGB[1]},{CLOUD_RGB[2]})]{ch}[/]")
            elif ch in "▄▀█":
                parts.append(f"[rgb({MOON_RGB[0]},{MOON_RGB[1]},{MOON_RGB[2]})]{ch}[/]")
            elif ord(ch) >= 0x2800 and row_rgb:
                r, g, b = row_rgb
                parts.append(f"[rgb({r},{g},{b})]{ch}[/]")
            elif ord(ch) >= 0x2800:
                r, g, b = MASCOT_RGB
                parts.append(f"[rgb({r},{g},{b})]{ch}[/]")
            elif ch == "─":
                parts.append(f"[rgb({GROUND_RGB[0]},{GROUND_RGB[1]},{GROUND_RGB[2]})]─[/]")
            else:
                parts.append(ch)
        rich_lines.append("".join(parts))
    return rich_lines


def load_mascot_braille(cols: int = 20) -> List[Tuple[str, Tuple[int, int, int]]]:
    return image_to_braille_lines(MASCOT_PATH, cols=cols)


def render_welcome_html(version: str = "vA.1272", width: int = 72) -> str:
    """HTML fragment for glass UI digital welcome (truecolor spans)."""
    dot = f'<span style="color:rgb({DOT_RGB[0]},{DOT_RGB[1]},{DOT_RGB[2]})">{"." * width}</span>'
    mascot = load_mascot_braille(cols=20)
    scene = compose_welcome_scene(mascot, width=width)
    r, g, b = MASCOT_RGB

    rows: List[str] = [
        f'<div class="digital-welcome-title">Welcome to Claude CLI {version}</div>',
        dot,
    ]
    for line, row_rgb in scene:
        spans: List[str] = []
        for ch in line:
            if ch == " ":
                spans.append(" ")
            elif ch == "*":
                spans.append(f'<span style="color:rgb({STAR_RGB[0]},{STAR_RGB[1]},{STAR_RGB[2]})">*</span>')
            elif ch in "░▒▓":
                spans.append(f'<span style="color:rgb({CLOUD_RGB[0]},{CLOUD_RGB[1]},{CLOUD_RGB[2]})">{ch}</span>')
            elif ch in "▄▀█":
                spans.append(f'<span style="color:rgb({MOON_RGB[0]},{MOON_RGB[1]},{MOON_RGB[2]})">{ch}</span>')
            elif ord(ch) >= 0x2800:
                cr, cg, cb = row_rgb or MASCOT_RGB
                spans.append(f'<span style="color:rgb({cr},{cg},{cb})">{ch}</span>')
            else:
                spans.append(ch)
        rows.append("".join(spans))
    rows.append(" " * 6 + f'<span style="color:rgb({GROUND_RGB[0]},{GROUND_RGB[1]},{GROUND_RGB[2]})">{"─" * 28}</span>')
    rows.append(dot)
    return "\n".join(rows)


def render_welcome_art(version: str = "vA.1272", width: int = 72) -> List[str]:
    """Full Claude Code-style welcome: title + dot frame + braille scene + ground."""
    dot = f"[rgb({DOT_RGB[0]},{DOT_RGB[1]},{DOT_RGB[2]})]{'.' * width}[/]"
    mascot = load_mascot_braille(cols=20)
    scene = compose_welcome_scene(mascot, width=width)
    art_lines = braille_to_rich_segments(scene)

    lines: List[str] = [
        f"[rgb({MASCOT_RGB[0]},{MASCOT_RGB[1]},{MASCOT_RGB[2]})]Welcome to Claude CLI {version}[/]",
        "",
        dot,
    ]
    lines.extend(art_lines)
    # Ground line under mascot (Claude Code white platform)
    ground = " " * 6 + f"[rgb({GROUND_RGB[0]},{GROUND_RGB[1]},{GROUND_RGB[2]})]{'─' * 28}[/]"
    lines.append(ground)
    lines.append(dot)
    lines.append("")
    lines.append(
        "[rgb(150,148,140)]  Sovereign local terminal · Ollama · ZTA Hardened · $0.00 API cost[/]"
    )
    lines.append(
        "[rgb(150,148,140)]  Not Anthropic Claude Code — run [/][cyan]claude-cli[/]"
        "[rgb(150,148,140)] (Oroboros · local)[/]"
    )
    return lines
