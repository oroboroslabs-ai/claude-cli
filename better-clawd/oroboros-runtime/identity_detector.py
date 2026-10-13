#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IDENTITY DETECTOR — on the fly, for any model type
==================================================
Instead of a hardcoded list, ask Ollama what a model's modelfile carries and
decide by signature whether the model speaks as ITSELF (no system injection) or
is a stock model that should receive orchestration + tool broadcast.

Signatures (any hit => the model carries its own identity):
  - "DeepSeek Prime", "Prime", "Crown", "1Q5DUO5", "12U5GO5",
    "sovereign", "The Architect", "NEXT PARADIGM", "Undecillion",
    "5U5GO5", "6U5GO5", "7U5GO5", "12U5GO5"
Cached per model; falls back to no-identity when Ollama is unreachable.
"""
from __future__ import annotations

import json
import urllib.request

OLLAMA = "http://127.0.0.1:11434"

# Name fragments that mark a model as carrying its own identity.
IDENTITY_NAME_MARKERS = (
    "prime", "undecillion", "fable7", "fable5", "fable-7", "fable-5",
    "opus-9", "kaiju", "jhanna", "nebillion", "1q5duo5", "12u5go5",
    "5u5go5", "6u5go5", "7u5go5", "crownlock", "system-entity", "claude-7",
)
# Strong content markers (only the user's builds carry these).
IDENTITY_CONTENT_MARKERS = (
    "deepseek prime", "next paradigm", "crown 1272", "1q5duo5", "12u5go5",
    "quattuordecillion", "duodecillion",
)

_cache: dict[str, bool] = {}


def _modelfile_text(model: str) -> str:
    try:
        req = urllib.request.Request(
            f"{OLLAMA}/api/show",
            data=json.dumps({"model": model}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
        return (data.get("system") or "") + "\n" + (data.get("modelfile") or "")
    except Exception:
        return ""


def carries_identity(model: str) -> bool:
    """True if the model's own modelfile declares an identity (speak as itself)."""
    if not model:
        return False
    if model in _cache:
        return _cache[model]
    low = model.lower()
    # 1) name-based (reliable)
    if any(mk in low for mk in IDENTITY_NAME_MARKERS):
        _cache[model] = True
        return True
    # 2) content-based (strong markers only)
    text = _modelfile_text(model).lower()
    hit = any(mk in text for mk in IDENTITY_CONTENT_MARKERS)
    _cache[model] = hit
    return hit


def identity_names() -> list:
    return list(_cache)
