"""Glass-styled terminal UI — digital xxoo interface matching Claude CLI HTML."""
from __future__ import annotations

from datetime import datetime

from rich.console import Console
from rich.panel import Panel
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

GLASS_THEME = Theme({
    "cyan": "#00ffcc",
    "gold": "#d5a021",
    "orange": "#D97757",
    "warm_grey": "#b7b3ac",
    "warm_white": "#e8e5dd",
    "green": "#00ff88",
    "white": "#ffffff",
})


class GlassTerminal:
    """Terminal renderer — digital xxoo welcome + glass chrome."""

    def __init__(self, model: str, ollama_url: str = "http://localhost:11434"):
        self.console = Console(theme=GLASS_THEME, highlight=False, soft_wrap=True)
        self.model = model
        host = ollama_url.replace("https://", "").replace("http://", "")
        self.ollama_host = host
        self._streaming = False
        self._watermark_printed = False

    @staticmethod
    def _time() -> str:
        return datetime.now().strftime("%H:%M:%S")

    def render_startup(self):
        # Claude Code-style digital welcome (xxoo block art)
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

        # Faint braille mascot watermark (from logo PNG)
        self.console.print(
            Panel(
                "",
                border_style="dim orange",
                padding=(0, 2),
                title="[dim orange]braille · U+2800[/]",
                subtitle="[dim warm_grey]chat below[/]",
            )
        )
        for line in watermark_block():
            self.console.print(line)
        self._watermark_printed = True
        self.console.print()

    def error(self, message: str):
        self.console.print(f"  [bold orange]✕[/]  {message}", style="orange")

    def note(self, message: str):
        self.console.print(f"  [gold]·[/]  {message}", style="warm_grey")

    def user_message(self, text: str):
        self.console.print()
        line = Text()
        line.append("YOU", style="bold gold")
        line.append(f"  {self._time()}", style="dim warm_grey")
        self.console.print(line)
        self.console.print(text, style="white")
        self.console.print()

    def assistant_begin(self):
        self._streaming = True
        self.console.print()
        line = Text()
        line.append("CLAUDE", style="bold cyan")
        line.append(f"  {self._time()}", style="dim warm_grey")
        self.console.print(line)
        self.console.print("  [italic orange]⟳ thinking...[/]")
        self.console.print("  ", end="")

    def assistant_token(self, token: str):
        if self._streaming:
            self.console.print(token, end="", style="white", highlight=False)

    def assistant_end(self):
        if self._streaming:
            self.console.print()
            self.console.print()
            self._streaming = False

    def read_prompt(self) -> str:
        self.console.print("[orange]◆[/] ", end="")
        try:
            return input().strip()
        except (EOFError, KeyboardInterrupt):
            self.console.print()
            raise

    def farewell(self, signature: str):
        self.console.print()
        self.console.print(f"  [dim warm_grey]{signature}[/]")
        self.console.print()
