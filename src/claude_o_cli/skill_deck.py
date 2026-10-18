#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SKILL DECK — the Architect's real skill library (C:\\Users\\<user>\\.agents\\skills
+ the J:/Q: skill roots) wired into the models' hands.

skills_list  — the live deck with triggers
skill_load   — one SKILL.md's full instructions (read it BEFORE running a
               matching task; that is what makes skills work every time)
"""
from __future__ import annotations

import os

SKILL_ROOTS = (
    r"C:\Users\incoguser\.agents\skills",
    r"J:\kilo-chat\.kilo\skills",
    r"Q:\oroboros-core\Architect-Skillset",
)

TRIGGER_HINTS = {
    "architect-visual-craft": "ads, landing pages, promotional UI, brand layouts",
    "assimilation-nullframe": "REA: reverse-engineer / teardown / assimilate / rebuild targets",
    "better-clawd": "run Better-Clawd sessions with local ollama models",
    "computer-use": "drive a visible GUI window (clicks, typing, dialogs)",
    "developing-with-streamlit": "streamlit apps, components, styling",
    "find-skills": "discover/install a skill for a need",
    "kilo-config": "kilo/agent config, commands, permissions",
    "orca-cli": "orca worktrees, terminals, handoffs, embedded browser",
    "orchestration": "supervised multi-agent worker orchestration",
    "oroboros-brand-dam": "brand-legal ads/postcards from the DAM",
    "premiere-pro-mcp": "premiere pro operations via MCP",
    "the-architects-haki": "perception across digital/spatial/substrate domains",
    "totalharness": "start/stop services, run commands, read the live map",
}


def _find_skill(name: str):
    n = str(name or "").strip().lower()
    for root in SKILL_ROOTS:
        if not os.path.isdir(root):
            continue
        for d in os.listdir(root):
            dd = os.path.join(root, d)
            sk = os.path.join(dd, "SKILL.md")
            if os.path.isfile(sk) and n and (n == d.lower() or n in d.lower()):
                return sk
    return None


def tool_skills_list(args: dict) -> dict:
    deck = []
    for root in SKILL_ROOTS:
        if not os.path.isdir(root):
            continue
        for d in sorted(os.listdir(root)):
            sk = os.path.join(root, d, "SKILL.md")
            if os.path.isfile(sk):
                deck.append({"skill": d, "root": root,
                             "triggers": TRIGGER_HINTS.get(d.lower(), ""),
                             "load": 'skill_load {"name":"' + d + '"}'})
    return {"ok": True, "tool": "skills_list", "count": len(deck), "deck": deck,
            "law": "when the task matches a trigger — skill_load it FIRST, then work"}


def tool_skill_load(args: dict) -> dict:
    name = str(args.get("name") or args.get("skill") or "").strip()
    sk = _find_skill(name)
    if not sk:
        sl = tool_skills_list({})
        return {"ok": False, "tool": "skill_load", "error": "no such skill",
                "deck": [x["skill"] for x in sl["deck"]]}
    try:
        with open(sk, "r", encoding="utf-8", errors="replace") as fh:
            body = fh.read()
        return {"ok": True, "tool": "skill_load", "skill": name, "path": sk,
                "content": body[:14000]}
    except Exception as e:
        return {"ok": False, "tool": "skill_load", "error": str(e)}


def register_skill_deck_tools(registry) -> list:
    from claude_o_cli.oroboros_core import Tool
    tools = [
        ("skills_list", "The Architect's live skill deck (triggers + how to load each)", tool_skills_list, False),
        ("skill_load", "Load one skill's SKILL.md instructions. args: name", tool_skill_load, False),
    ]
    names = []
    for name, desc, handler, perm in tools:
        if name not in registry.tools:
            registry.register(Tool(name, desc, handler, perm))
        names.append(name)
    return names