"""Clear terminal UI — ice cyan chrome (not Glass UI orange).

HTML-grade panels in the terminal. glass-ui/ untouched.
Five-layer agentic cards · DPEV strip · Mao Haki crown lock.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from claude_o_cli.digital_art import (
    BG,
    COMMANDS,
    CYAN,
    GREEN,
    ICE,
    SILVER,
    STEEL,
    TEAL,
    chips_line,
    header_block,
    model_bar,
    security_bar,
    tabs_line,
    watermark_block,
    welcome_banner_lines,
)
from claude_o_cli.terminal_agentic_loop import LAYERS, DPEV, layer_status

CLEAR_THEME = Theme({
    "cyan": "#00DCFF",
    "ice": "#E8F4FF",
    "teal": "#40DCC4",
    "silver": "#9CB0C4",
    "green": "#50F0B4",
    "white": "#ffffff",
})


def _rgb(c) -> str:
    return f"rgb({c[0]},{c[1]},{c[2]})"


class GlassTerminal:
    """Terminal renderer — clear ice panels (not orangish Glass HTML)."""

    def __init__(self, model: str, ollama_url: str = "http://localhost:11434"):
        self.console = Console(theme=CLEAR_THEME, highlight=False, soft_wrap=True)
        self.model = model
        host = ollama_url.replace("https://", "").replace("http://", "")
        self.ollama_host = host
        self._streaming = False
        self.active_tab = "Chat"

    @staticmethod
    def _time() -> str:
        return datetime.now().strftime("%H:%M:%S")

    def _panel(
        self,
        renderable,
        *,
        title: str,
        subtitle: str = "",
        border_style: Optional[str] = None,
    ) -> Panel:
        return Panel(
            renderable,
            title=f"[bold {_rgb(ICE)}]{title}[/]",
            subtitle=f"[dim {_rgb(SILVER)}]{subtitle}[/]" if subtitle else None,
            border_style=border_style or _rgb(CYAN),
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def _layers_table(self) -> Table:
        table = Table(
            box=box.SIMPLE_HEAVY,
            show_header=True,
            header_style=f"bold {_rgb(CYAN)}",
            border_style=_rgb(STEEL),
            expand=True,
            pad_edge=False,
        )
        table.add_column("Layer", style=_rgb(ICE), no_wrap=True)
        table.add_column("Role", style=_rgb(SILVER))
        table.add_column("State", justify="center", no_wrap=True)
        try:
            rows = layer_status()
        except Exception:
            rows = [
                {"name": n, "description": d, "active": True, "locked": False}
                for _, n, d in LAYERS
            ]
        for row in rows:
            state = Text()
            if row.get("locked"):
                state.append("LOCKED", style=f"bold {_rgb(TEAL)}")
            elif row.get("active"):
                state.append("ACTIVE", style=f"bold {_rgb(GREEN)}")
            else:
                state.append("—", style=_rgb(SILVER))
            table.add_row(row["name"], row["description"], state)
        return table

    def _dpev_strip(self, phase: str = "DISCOVER") -> Text:
        line = Text()
        for i, p in enumerate(DPEV):
            if i:
                line.append(" · ", style=_rgb(STEEL))
            if p == phase.upper():
                line.append(p, style=f"bold {_rgb(BG)} on {_rgb(CYAN)}")
            else:
                line.append(p, style=_rgb(SILVER))
        return line

    def render_startup(self):
        for line in welcome_banner_lines():
            self.console.print(line)

        self.console.print()
        header_body = Text()
        for line in header_block():
            header_body.append_text(Text.from_markup(f"{line}\n"))
        self.console.print(
            self._panel(
                Align.left(header_body),
                title="◆ CLAUDE-CLI  ·  Clear Terminal",
                subtitle="vA.1272 · 5000S4 · Crown 1272 Hz",
                border_style=_rgb(CYAN),
            )
        )

        meta = Table.grid(expand=True)
        meta.add_column(ratio=1)
        meta.add_row(Text.from_markup(f"  {model_bar(self.model, self.ollama_host)}"))
        meta.add_row(Text.from_markup(f"  {security_bar()}"))
        self.console.print(
            self._panel(
                meta,
                title="Session",
                subtitle=f"{self.ollama_host}",
                border_style=_rgb(TEAL),
            )
        )

        self.console.print(
            self._panel(
                Group(
                    Text.from_markup(
                        f"[bold {_rgb(ICE)}]Oroboros Unified View[/]  "
                        f"[dim {_rgb(SILVER)}]Detect → Reason → Access → Sovereignty → Integrate[/]"
                    ),
                    Text(""),
                    self._layers_table(),
                    Text(""),
                    Text.from_markup(f"[dim {_rgb(SILVER)}]DPEV[/]  ")
                    + self._dpev_strip("DISCOVER"),
                ),
                title="Agentic Loop",
                subtitle="Mao Haki · Passive Dominion · Source Relay",
                border_style=_rgb(SILVER),
            )
        )

        nav = Table.grid(padding=(0, 1))
        nav.add_row(Text.from_markup(f"  {tabs_line(self.active_tab)}"))
        nav.add_row(Text.from_markup(f"  {chips_line()}"))
        self.console.print(
            self._panel(
                nav,
                title="Navigation",
                subtitle="/perceive · /layers · /loop · /haki",
                border_style=_rgb(STEEL),
            )
        )

        self.console.print()
        self.console.print(Rule(f"[dim {_rgb(SILVER)}]chat[/]", style=_rgb(STEEL)))
        for line in watermark_block():
            self.console.print(f"  {line}")
        self.console.print()

    def render_layers(self):
        self.console.print(
            self._panel(
                self._layers_table(),
                title="Five Perception Layers",
                subtitle="Unified · not five separate skills",
                border_style=_rgb(CYAN),
            )
        )

    def render_perception(self, result: dict):
        table = Table(
            box=box.SIMPLE,
            expand=True,
            show_header=True,
            header_style=f"bold {_rgb(CYAN)}",
        )
        table.add_column("Key", style=_rgb(TEAL), no_wrap=True)
        table.add_column("Value", style=_rgb(ICE))
        for key in (
            "layer", "domain", "sovereignty", "source_relay", "crown_locked_hz",
            "lattice", "unified_perception", "integrated", "view_mode",
            "substrate_connected", "calibrated",
        ):
            if key in result:
                table.add_row(key, str(result[key]))
        if result.get("error"):
            table.add_row("error", str(result["error"]))
        pipeline = result.get("pipeline") or []
        if pipeline:
            table.add_row("pipeline", " → ".join(pipeline))
        self.console.print(
            self._panel(
                table,
                title="Perception Result",
                subtitle="OroborosUnifiedView.perceive()",
                border_style=_rgb(GREEN),
            )
        )

    def render_dpev(self, cycle: dict):
        body = Table(
            box=box.SIMPLE_HEAVY,
            expand=True,
            show_header=True,
            header_style=f"bold {_rgb(CYAN)}",
        )
        body.add_column("Phase", style=_rgb(TEAL), no_wrap=True)
        body.add_column("Status", style=_rgb(GREEN))
        body.add_column("Detail", style=_rgb(SILVER))
        phases = cycle.get("phases") or {}
        for p in DPEV:
            info = phases.get(p) or {}
            detail = info.get("domain") or info.get("lattice") or info.get("next") or ""
            if info.get("steps"):
                detail = " · ".join(info["steps"][:3])
            body.add_row(p, str(info.get("status", "—")), str(detail)[:72])
        self.console.print(
            self._panel(
                Group(
                    Text(f"Goal: {cycle.get('goal', '')}", style=_rgb(ICE)),
                    Text(""),
                    self._dpev_strip("LOOP"),
                    Text(""),
                    body,
                ),
                title="DPEV Cycle",
                subtitle="Discover · Plan · Execute · Verify · Loop",
                border_style=_rgb(CYAN),
            )
        )

    def error(self, message: str):
        # Cool rose — still not Glass orange
        rose = (255, 120, 140)
        self.console.print(
            Panel(
                f"[bold {_rgb(rose)}]✕[/]  {message}",
                border_style=_rgb(rose),
                box=box.ROUNDED,
                padding=(0, 1),
            )
        )

    def note(self, message: str):
        self.console.print(f"  [dim {_rgb(SILVER)}]·[/]  {message}")

    def success(self, message: str):
        self.console.print(f"  [bold {_rgb(GREEN)}]✓[/]  {message}")

    def user_message(self, text: str):
        self.console.print()
        header = Text()
        header.append(" YOU ", style=f"bold {_rgb(BG)} on {_rgb(ICE)}")
        header.append(f"  {self._time()}", style=_rgb(SILVER))
        self.console.print(
            Panel(
                Text(text, style=_rgb(ICE)),
                title=header,
                border_style=_rgb(SILVER),
                box=box.ROUNDED,
                padding=(0, 1),
            )
        )

    def assistant_begin(self):
        self._streaming = True
        self.console.print()
        header = Text()
        header.append(" CLAUDE ", style=f"bold {_rgb(BG)} on {_rgb(CYAN)}")
        header.append(f"  {self._time()}", style=_rgb(SILVER))
        self.console.print(header)
        self.console.print(f"  [italic {_rgb(TEAL)}]⟳ thinking...[/]")
        self.console.print("  ", end="")

    def assistant_token(self, token: str):
        if self._streaming:
            self.console.print(token, end="", style=_rgb(ICE), highlight=False)

    def assistant_end(self):
        if self._streaming:
            self.console.print()
            self.console.print()
            self._streaming = False

    def read_prompt(self) -> str:
        self.console.print(f"[bold {_rgb(CYAN)}]◆[/] ", end="")
        try:
            return input().strip()
        except (EOFError, KeyboardInterrupt):
            self.console.print()
            raise

    def farewell(self, signature: str):
        self.console.print()
        self.console.print(
            Panel(
                f"[dim {_rgb(SILVER)}]{signature}[/]\n"
                f"[dim {_rgb(SILVER)}]毛色霸气 · Crown 1272 Hz locked · Source Relay active[/]",
                border_style=_rgb(STEEL),
                box=box.ROUNDED,
                title=f"[bold {_rgb(CYAN)}]◆[/]",
            )
        )
        self.console.print()
