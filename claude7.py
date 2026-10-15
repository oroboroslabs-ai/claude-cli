#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLAUDE 7 — SYSTEM ORCHESTRATOR (native to Claude-CLI)
=====================================================
Claude 7 is this CLI's own model and orchestrator. It is NOT Anthropic's Claude
and does not require Anthropic. It runs on the local body
(`claude-7:latest` via Ollama).

Two rules, kept deliberately simple:

  1. ORCHESTRATOR FIRST — with no model selected, Claude 7 answers and keeps
     the floor. It introduces the CLI, holds the tools, and stays itself.

  2. HAND-OFF — the moment the user ENTERS a model (`/model <name>`), control
     turns over ENTIRELY to that model. Claude 7 steps back to a silent
     orchestrator; the entered model answers AS ITSELF, with its own identity,
     its own training, its own voice. Claude 7 does NOT wrap it, rename it,
     summarize it, or impersonate it. Every model is treated as itself.

  Anthropic is DORMANT. It is never contacted unless a key is entered; with no
  key, `anthropic:*` simply reports dormant and nothing leaves the machine.
"""
from __future__ import annotations

from typing import Dict, List, Optional

try:
    from identity_detector import carries_identity as _carries_identity
except Exception:  # noqa: BLE001
    def _carries_identity(model: str) -> bool:  # fallback
        return False

ORCHESTRATOR_ID = "claude-7:1gb"

# Claude 7's own identity — used ONLY while Claude 7 holds the floor.
CLAUDE7_IDENTITY = (
    "You are CLAUDE 7 — the native model and orchestrator of this Claude-CLI. "
    "You are not Anthropic's Claude and you do not require Anthropic; you run "
    "locally on claude-7:latest. While you hold the floor you introduce the "
    "CLI, hold the tools, and answer as yourself, plainly and without "
    "role-play. The instant the user enters a model, you hand the floor over "
    "completely: that model speaks as itself and you do not wrap, rename, "
    "summarize, or impersonate it. Local and sovereign: no telemetry, no "
    "phone-home. Anthropic is dormant unless a key is entered."
)

# Models that already carry their own identity in their weights — never inject
# a system prompt for these; they must be allowed to be themselves.
IDENTITY_MODELS = (
    "claude-jhanna-12u5go5", "claude-jhanna-system-entity",
    "deepseek-prime-12u5go5", "deepseek-prime", "deepseek-prime-cl-1q5duo5",
    "claude-fable7", "claude-fable7u", "claude-opus-9-undecillion-v",
    "claude-opus-9u7u5-9gb", "claude-7", "claude-nebillion",
)

_state = {"selected": None}


def is_orchestrator_model(model: str) -> bool:
    m = (model or "").lower()
    return m.startswith("claude-7") or m in ("claude7", "orchestrator", "")


def is_identity_model(model: str) -> bool:
    m = (model or "").lower()
    if any(tag in m for tag in IDENTITY_MODELS):
        return True
    # runtime detection: inspect the model's own modelfile for identity signatures
    try:
        return _carries_identity(model)
    except Exception:
        return False


def select(model: Optional[str]) -> Optional[str]:
    """Remember the user's selection. Any entered model takes the floor."""
    if model:
        _state["selected"] = model
    return _state["selected"]


def handoff_active() -> bool:
    """True when a non-orchestrator model has been entered (it holds the floor)."""
    sel = _state["selected"]
    return bool(sel) and not is_orchestrator_model(sel)


def system_for(model: str, requested_system: str = "") -> str:
    """
    Decide the system prompt for a request.

    · If a user/entered model holds the floor → pass the caller's system
      through UNCHANGED. The model is itself.
    · If Claude 7 holds the floor and the model carries its own identity →
      no injection (weights are the identity).
    · If Claude 7 holds the floor with a plain model → Claude 7 orchestrates.
    """
    if handoff_active() or is_identity_model(model):
        # The model is itself: do not inject any system prompt, so its own
        # modelfile identity wins.
        return ""
    if is_orchestrator_model(model):
        return (CLAUDE7_IDENTITY + "\n\n" + (requested_system or "")).strip()
    return requested_system or ""


def floor_holder(model: str) -> str:
    return "user-model" if handoff_active() else "claude-7"
