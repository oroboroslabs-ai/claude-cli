#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REBRAND better-clawd -> OROBOROS-ANTHROPIC CLAUDE CLI  (text only)
==================================================================
Walks the repo source and applies text-only replacements so the whole product
is rebranded to the user's brand. No images are touched -- the brand mark is the
flipped-horizontal A (Anthropic symbol), carried as text art separately.

Product  : Oroboros-Anthropic Claude CLI
Command  : claude-cli
Config   : ~/.claude-cli
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(r"Q:\claude-cli\better-clawd-src")
EXTS = {".ts", ".tsx", ".js", ".mjs", ".json", ".md", ".txt"}

# order matters: longest / most specific first
REPL = [
    ("x1xhlol/better-clawd", "oroboroslabs-ai/claude-cli"),
    ("Better-Clawd", "Oroboros-Anthropic Claude CLI"),
    ("BETTER_CLAWD", "CLAUDE_CLI"),
    ("Better Clawd", "Oroboros-Anthropic Claude CLI"),
    ("BetterClawd", "ClaudeCLI"),
    ("better-clawd", "claude-cli"),
    ("better_clawd", "claude_cli"),
]

SKIP_DIRS = {".git", "node_modules", "dist", ".cache", "coverage"}
SKIP_FILES = {"rebrand.py"}


def rebrand_file(p: Path) -> int:
    if p.name in SKIP_FILES:
        return 0
    try:
        text = p.read_bytes().decode("utf-8")
    except Exception:
        return 0
    orig = text
    for a, b in REPL:
        if a in text:
            text = text.replace(a, b)
    if text != orig:
        p.write_bytes(text.encode("utf-8"))
        return 1
    return 0


def main() -> int:
    changed = 0
    scanned = 0
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix not in EXTS:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        scanned += 1
        changed += rebrand_file(p)
    print(f"scanned {scanned} files · rebranded {changed}")
    # verify no residual branding
    left = 0
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix not in EXTS:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        try:
            if "better-clawd" in p.read_text(encoding="utf-8").lower() or "better clawd" in p.read_text(encoding="utf-8").lower():
                left += 1
                print("  residual:", p.relative_to(ROOT))
        except Exception:
            pass
    print(f"residual files still carrying old brand: {left}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
