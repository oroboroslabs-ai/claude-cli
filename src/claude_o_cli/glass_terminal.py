"""Glass-styled terminal UI — matches Claude CLI HTML design."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

GLASS_THEME = Theme({
    "cyan": "#00ffcc",
    "gold": "#d5a021",
    "orange": "#D97757",
    "warm_grey": "#b7b3ac",
    "warm_white": "#e8e5dd",
    "green": "#00ff88",
    "white": "#ffffff",
})

COMMANDS = (
    "/exit", "/clear", "/model <name>", "/models", "/help", "/status",
    "/tools", "/scan", "/noir", "/worldfeed", "/seer",
)


class GlassTerminal:
    """Terminal renderer aligned with the glass HTML UI."""

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
        header = Text()
        header.append("◆ ", style="orange")
        header.append("CLAUDE-CLI", style="bold orange")
        header.append("  vA.1272", style="warm_grey")
        header.append("     ● ", style="green")
        header.append("Connected", style="bold green")
        header.append("     ● ", style="cyan")
        header.append("Model: ", style="warm_grey")
        header.append("Local", style="bold cyan")
        header.append("     ● ", style="orange")
        header.append("Tools: ", style="warm_grey")
        header.append("Ready", style="bold orange")
        header.append("     Anthropic × OROBOROS", style="gold")

        model_line = Text()
        model_line.append("Model: ", style="warm_grey")
        model_line.append(self.model, style="bold cyan")
        model_line.append(f"     {self.ollama_host}", style="dim warm_grey")
        model_line.append("     ZTA HARDENED", style="bold gold")

        security = Text()
        security.append("🛡 Path Whitelist: ", style="warm_grey")
        security.append("ACTIVE", style="bold green")
        security.append("   🛡 Rate Limit: ", style="warm_grey")
        security.append("60/min", style="bold green")
        security.append("   ⚠ Shell: ", style="warm_grey")
        security.append("ACTIVE", style="bold gold")
        security.append("   🚫 Delete: ", style="warm_grey")
        security.append("DENIED", style="bold orange")
        security.append("   🛡 MCP: ", style="warm_grey")
        security.append("REAL", style="bold green")

        chips = Text()
        for i, cmd in enumerate(COMMANDS):
            if i:
                chips.append("  ")
            if " " in cmd:
                base, arg = cmd.split(" ", 1)
                chips.append(base, style="bold white")
                chips.append(f" {arg}", style="orange")
            else:
                chips.append(cmd, style="bold white")

        body = Text()
        body.append_text(header)
        body.append("\n")
        body.append_text(model_line)
        body.append("\n")
        body.append_text(security)
        body.append("\n")
        body.append_text(chips)

        self.console.print(
            Panel(
                body,
                border_style="cyan",
                padding=(1, 2),
                title="[orange]◆[/] [bold orange]Claude CLI[/]",
                subtitle="[warm_grey]Sovereign · local · $0.00[/]",
            )
        )
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
