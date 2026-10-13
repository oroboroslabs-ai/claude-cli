#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI SHARED SETTINGS — wallpaper + theme (one store, CLI drives it)
==================================================================
Default wallpaper comes from the CLI. Changing it here changes the CLI (the
glass UI reads /api/settings on load, so it follows). One source of truth:
  Q:\\claude-cli\\cli-settings.json
"""
from __future__ import annotations

import json
from pathlib import Path

SETTINGS = Path(r"Q:\claude-cli\cli-settings.json")

DEFAULTS = {
    "wallpaper": None,                          # default: none (black + flipped-A)
    "theme": "oroboros-mono",                    # default theme option
}


def load() -> dict:
    d = dict(DEFAULTS)
    try:
        d.update(json.loads(SETTINGS.read_text(encoding="utf-8")))
    except Exception:
        pass
    return d


def save(**kw) -> dict:
    d = load()
    d.update({k: v for k, v in kw.items() if v is not None})
    SETTINGS.write_text(json.dumps(d, indent=2), encoding="utf-8")
    return d
