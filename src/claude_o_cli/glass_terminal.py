"""Glass-styled terminal UI — Anthropic welcome + CLI chrome."""
from __future__ import annotations

from datetime import datetime

from rich.console import Console
from rich.text import Text
from rich.theme import Theme

from claude_o_cli.digital_art import (
    COMMANDS,
    chips_line,
    header_block,
    model_bar,
    security_bar,
    tabs_line,
    watermark_block,
    welcome_banner_lines,
)
from claude_o_cli.welcome_scene import GREY, ORANGE

GLASS_THEME = Theme({
    "cyan": "#00ffcc",
    "gold": "#d5a021",
    "orange": "#D97757",
    "warm_grey": "#969187",
    "warm_white": "#F5F2ED",
    "green": "#00ff88",
    "white": "#ffffff",
})


class GlassTerminal:
    """Terminal renderer — copied Claude Code welcome + glass CLI."""

    def __init__(self, model: str, ollama_url: str = "http://localhost:11434"):
        self.console = Console(theme=GLASS_THEME, highlight=False, soft_wrap=True)
        self.model = model
        host = ollama_url.replace("https://", "").replace("http://", "")
        self.ollama_host = host
        self._streaming = False

    @staticmethod
    def _time() -> str:
        return datetime.now().strftime("%H:%M:%S")

    def render_startup(self):
        for line in welcome_banner_lines():
            self.console.print(line)

        self.console.print()
        for line in header_block():
            self.console.print(f"  {line}")
        self.console.print()
        self.console.print(f"  {model_bar(self.model, self.ollama_host)}")
        self.console.print(f"  {security_bar()}")
        self.console.print()
        self.console.print(f"  {tabs_line('Chat')}")
        self.console.print()
        self.console.print(f"  {chips_line()}")
        self.console.print()

        g = f"rgb({GREY[0]},{GREY[1]},{GREY[2]})"
        self.console.print(f"  [{g}]──── chat ────[/]")
        for line in watermark_block():
            self.console.print(f"  {line}")
        self.console.print()

    def error(self, message: str):
        o = f"rgb({ORANGE[0]},{ORANGE[1]},{ORANGE[2]})"
        self.console.print(f"  [bold {o}]✕[/]  {message}")

    def note(self, message: str):
        g = f"rgb({GREY[0]},{GREY[1]},{GREY[2]})"
        self.console.print(f"  [{g}]·[/]  {message}")

    def user_message(self, text: str):
        self.console.print()
        line = Text()
        o = f"rgb({ORANGE[0]},{ORANGE[1]},{ORANGE[2]})"
        g = f"rgb({GREY[0]},{GREY[1]},{GREY[2]})"
        line.append("YOU", style=o)
        line.append(f"  {self._time()}", style=g)
        self.console.print(line)
        self.console.print(text, style="rgb(245,242,237)")
        self.console.print()

    def assistant_begin(self):
        self._streaming = True
        self.console.print()
        line = Text()
        line.append("CLAUDE", style="rgb(0,255,204)")
        line.append(f"  {self._time()}", style=f"rgb({GREY[0]},{GREY[1]},{GREY[2]})")
        self.console.print(line)
        o = f"rgb({ORANGE[0]},{ORANGE[1]},{ORANGE[2]})"
        self.console.print(f"  [italic {o}]⟳ thinking...[/]")
        self.console.print("  ", end="")

    def assistant_token(self, token: str):
        if self._streaming:
            self.console.print(token, end="", style="rgb(245,242,237)", highlight=False)

    def assistant_end(self):
        if self._streaming:
            self.console.print()
            self.console.print()
            self._streaming = False

    def read_prompt(self) -> str:
        o = f"rgb({ORANGE[0]},{ORANGE[1]},{ORANGE[2]})"
        self.console.print(f"[{o}]◆[/] ", end="")
        try:
            return input().strip()
        except (EOFError, KeyboardInterrupt):
            self.console.print()
            raise

    def farewell(self, signature: str):
        g = f"rgb({GREY[0]},{GREY[1]},{GREY[2]})"
        self.console.print()
        self.console.print(f"  [dim {g}]{signature}[/]")
        self.console.print()
