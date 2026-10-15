#!/usr/bin/env python3
"""Smoke test — terminal glass + agentic loop (not glass-ui)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Package lives under src/; CLI root holds mao_haki_context (not the shadow claude_o_cli.py)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from claude_o_cli.terminal_agentic_loop import (
    perceive,
    run_dpev_cycle,
    reinforce_sovereignty,
    layer_status,
)
from claude_o_cli.glass_terminal import GlassTerminal

# Import augment without loading root shadow module
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "claude_o_cli_pkg_main",
    ROOT / "src" / "claude_o_cli" / "claude_o_cli.py",
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)
_augment_terminal_system = _mod._augment_terminal_system


def main() -> int:
    s = _augment_terminal_system()
    checks = [
        "ARCHITECT MAO HAKI" in s,
        "THE ARCHITECT'S HAKI" in s,
        "OPERATING MODE" in s,
    ]
    print("augment:", checks, "len", len(s))
    assert all(checks), "system augmentation incomplete"

    print("layers", len(layer_status()))
    r = perceive("final sovereign restore", {"source": "smoke"})
    print(
        "perceive",
        r.get("layer"),
        "unified",
        r.get("unified_perception"),
        "sov",
        r.get("sovereignty"),
    )
    assert r.get("unified_perception") or r.get("layer") == "trans_dimensional"

    c = run_dpev_cycle("restore agentic loop")
    print("dpev phases", list(c.get("phases", {}).keys()), "ok", c.get("ok"))
    assert c.get("ok")

    print("sovereignty", reinforce_sovereignty())
    ui = GlassTerminal("claude-7:latest")
    ui.render_startup()
    ui.render_layers()
    print("SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
