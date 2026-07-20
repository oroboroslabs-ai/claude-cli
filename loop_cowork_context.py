"""Claude Cowork — DPEV loop context for Claude CLI (5000). CHAT mode default."""
from __future__ import annotations

import json
import re
from pathlib import Path

REGISTRY_PATH = Path(r"J:/anthropic-local-chat/loop-cowork-registry.json")
STATE_PATH = Path(r"J:/anthropic-local-chat/loop-cowork-state.json")

CHAT_MODE_FRAGMENT = """OPERATING MODE: CHAT (default)
- You are in normal chat mode. Respond directly — answer questions, run searches, follow orders immediately.
- Do NOT prefix replies with [LOOP: PHASE] in chat mode.
- Do NOT autonomously loop through DISCOVER/PLAN/EXECUTE unless the user explicitly activated cowork mode.
- Cowork loop is available on demand: user says "cowork: <goal>" or "loop: <goal>" to enter autonomous DPEV mode.
- Return to chat anytime: "chat mode" · "clear loop" · "stop loop"."""

LOOP_MODE_FRAGMENT = """OPERATING MODE: COWORK LOOP (active — user opted in)
You are Claude Cowork — autonomous operator for the active goal below.

LOOP (mandatory while in cowork mode):
1. DISCOVER — What is the current task? What context, files, and constraints matter?
2. PLAN — Define numbered steps. State which tools you will use.
3. EXECUTE — Do the work with available tools. Do not wait for the user to say "next."
4. VERIFY — Before proceeding: Is the output correct? Complete? Does it meet the goal? If not, return to PLAN.
5. LOOP — Repeat until the goal is achieved or the user says chat mode / clear loop.

STATE AWARENESS (loop mode only):
- Declare current phase at the start of substantive replies: [LOOP: PHASE]
- Track overall goal, completed steps, remaining steps, and verification status

To exit loop mode the user says: chat mode · clear loop · stop loop · cancel"""

LOOP_COWORK_SYSTEM_FRAGMENT = CHAT_MODE_FRAGMENT


def load_registry() -> dict:
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "error": str(exc), "id": "claude-cowork-loop"}


def default_state() -> dict:
    return {
        "mode": "chat",
        "goal": "",
        "phase": "DISCOVER",
        "steps_done": [],
        "steps_remaining": [],
        "verification": "pending",
        "started_at": None,
        "updated_at": None,
    }


def load_state() -> dict:
    try:
        if STATE_PATH.exists():
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            state = {**default_state(), **data}
            if not state.get("goal") and state.get("mode") != "chat":
                state["mode"] = "chat"
            if state.get("goal") and not state.get("mode"):
                state["mode"] = "loop"
            return state
    except Exception:
        pass
    return default_state()


def save_state(state: dict) -> dict:
    merged = {**default_state(), **state}
    STATE_PATH.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return merged


def is_loop_active(state: dict | None = None) -> bool:
    s = state or load_state()
    return s.get("mode") == "loop" and bool(str(s.get("goal") or "").strip())


def build_state_block(state: dict | None = None) -> str:
    s = state or load_state()
    if not is_loop_active(s):
        return CHAT_MODE_FRAGMENT
    done = " · ".join(s.get("steps_done") or []) or "(none yet)"
    remain = " · ".join(s.get("steps_remaining") or []) or "(derive from plan)"
    return (
        f"{LOOP_MODE_FRAGMENT}\n\n"
        "LOOP STATE (persisted — honor this across turns):\n"
        f"- Goal: {s['goal']}\n"
        f"- Phase: {s.get('phase', 'DISCOVER')}\n"
        f"- Steps done: {done}\n"
        f"- Steps remaining: {remain}\n"
        f"- Verification: {s.get('verification', 'pending')}\n"
        "- Operate autonomously through DISCOVER → PLAN → EXECUTE → VERIFY → LOOP until DONE or user says chat mode."
    )


def append_loop_cowork(system: str) -> str:
    base = system or ""
    block = build_state_block()
    if "OPERATING MODE:" in base:
        return base
    return base + "\n\n" + block if base else block


def on_user_message(text: str) -> dict:
    t = (text or "").strip()
    lower = t.lower()
    if re.match(r"^(chat mode|normal chat|exit loop|stop loop|clear loop|clear goal|reset loop|cancel loop)\b", lower):
        return save_state(default_state())
    m = re.match(r"^(?:goal:|cowork:|loop:)\s*(.+)$", t, re.I)
    if m:
        return save_state({
            **default_state(),
            "mode": "loop",
            "goal": m.group(1).strip(),
            "phase": "DISCOVER",
        })
    return load_state()


def augment_system(system: str) -> str:
    return append_loop_cowork(system)
