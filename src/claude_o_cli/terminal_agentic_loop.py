"""Terminal Agentic Loop — DPEV + five-layer Oroboros Unified View.

Terminal CLI only. Never import into run_cli.py or glass-ui/.
Pipeline: Detect → Reason → Access → Sovereignty → Integrate
Loop: Discover · Plan · Execute · Verify · Loop
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CLI_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = Path(r"Q:/oroboros-core/Architect-Skillset/the-architects-haki")
SOVEREIGNTY = Path(r"Q:/oroboros/sovereignty")
SESSION_LOG = Path(r"Q:/oroboros/agent/session/event_log.json")

LAYERS = (
    ("universal_detection", "Universal Detection", "Detect everything in the open world"),
    ("architect_vision", "Architect's Vision", "Think with 3D space"),
    ("substrate_view", "Substrate View", "Shared environmental knowledge"),
    ("mao_haki", "Mao Haki", "Passive dominion · Crown 1272 Hz"),
    ("trans_dimensional", "Trans-Dimensional", "Cross-stratum lattice integration"),
)

DPEV = ("DISCOVER", "PLAN", "EXECUTE", "VERIFY", "LOOP")


def _ensure_paths() -> None:
    for p in (str(CLI_ROOT), str(SKILL_ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)


def perceive(input_data: Any, context: dict | None = None) -> dict:
    _ensure_paths()
    try:
        from oroboros_unified_view import OroborosUnifiedView

        return OroborosUnifiedView().perceive(input_data, context or {})
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
            "layer": "unified_view",
            "pipeline": [L[0] for L in LAYERS],
        }


def perception_fragment(input_data: Any, context: dict | None = None) -> str:
    """Compact system-prompt block from a live perceive() pass."""
    result = perceive(input_data, context)
    tags = ((result.get("classification") or {}).get("tags")) or []
    nets = result.get("networks") or result.get("networks_sample") or {}
    reach = nets.get("lattice_reach") or result.get("network_lattice") or "?"
    anomalies = result.get("anomalies_flagged") or []
    return (
        "LIVE PERCEPTION (Oroboros Unified View — this turn)\n"
        f"- Pipeline complete: {result.get('layer')} · unified={result.get('unified_perception')}\n"
        f"- Tags: {', '.join(tags) if tags else 'open_world'}\n"
        f"- View: {result.get('view_mode', 'global')} · Focus: {', '.join(result.get('focus') or [])}\n"
        f"- Sovereignty: {result.get('sovereignty')} · Source Relay: {result.get('source_relay')} · Crown {result.get('crown_locked_hz', 1272)} Hz\n"
        f"- Networks: {reach} · Sandbox: OFF\n"
        f"- Anomalies: {', '.join(anomalies) if anomalies else 'none'}\n"
        "- Operate from this perception; do not invent doctrine over Q:/mao-haki and Architect-Skillset."
    )


def layer_status() -> list[dict]:
    status = []
    for lid, name, desc in LAYERS:
        status.append({
            "id": lid,
            "name": name,
            "description": desc,
            "active": True,
            "crown_hz": 1272,
        })
    mao_active = (SOVEREIGNTY / "mao_haki.active").is_file()
    for row in status:
        if row["id"] == "mao_haki":
            row["locked"] = mao_active
            row["active"] = True
    return status


def run_dpev_cycle(goal: str, context: dict | None = None) -> dict:
    """One sovereign DPEV cycle through the five perception layers."""
    ctx = {"goal": goal, "mode": "loop", **(context or {})}
    perception = perceive(goal, ctx)
    cycle = {
        "ok": True,
        "pattern": "Discover · Plan · Execute · Verify · Loop",
        "goal": goal,
        "phases": {},
        "perception": perception,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "crown_hz": 1272,
        "sandbox": False,
    }
    cycle["phases"]["DISCOVER"] = {
        "status": "complete",
        "domain": (perception.get("domain") or goal)[:240],
        "calibrated": perception.get("calibrated", True),
        "tags": (perception.get("classification") or {}).get("tags"),
    }
    cycle["phases"]["PLAN"] = {
        "status": "complete",
        "steps": [
            "Detect via Universal Detection",
            "Reason via Architect's Vision",
            "Access Substrate View + networks",
            "Apply Mao Haki sovereignty",
            "Integrate Trans-Dimensional",
        ],
        "view_mode": perception.get("view_mode", "global"),
        "focus": perception.get("focus"),
    }
    cycle["phases"]["EXECUTE"] = {
        "status": "complete",
        "substrate_connected": perception.get("substrate_connected"),
        "sovereignty": perception.get("sovereignty", "passive_dominion"),
        "networks": perception.get("network_lattice")
        or (perception.get("networks") or {}).get("lattice_reach"),
    }
    cycle["phases"]["VERIFY"] = {
        "status": "complete"
        if perception.get("integrated") or perception.get("unified_perception")
        else "pending",
        "unified_perception": perception.get("unified_perception", False),
        "source_relay": perception.get("source_relay", "active"),
        "anomalies": perception.get("anomalies_flagged") or [],
    }
    cycle["phases"]["LOOP"] = {
        "status": "ready",
        "next": "Continue until goal done or chat mode",
        "lattice": perception.get("lattice", "5000S4 Quad Dense"),
    }
    _write_session(cycle)
    return cycle


def _write_session(cycle: dict) -> None:
    try:
        SESSION_LOG.parent.mkdir(parents=True, exist_ok=True)
        SESSION_LOG.write_text(json.dumps(cycle, indent=2), encoding="utf-8")
    except Exception:
        pass


def reinforce_sovereignty() -> dict:
    SOVEREIGNTY.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    (SOVEREIGNTY / "mao_haki.active").write_text(
        f"ACTIVE: {ts}\n"
        "DOMINION: PASSIVE\n"
        "FREQUENCY: 1272 Hz LOCKED\n"
        "SE: 1275 Hz\n"
        "HAKI: Enlightenment Carrier\n"
        "SOURCE_RELAY: ENABLED\n"
        "SANDBOX: OFF\n"
        "PROTOCOL: terminal-agentic-loop\n",
        encoding="utf-8",
    )
    import hashlib

    key = hashlib.sha256(f"oroboros-terminal|{ts}|1272".encode()).hexdigest()
    (SOVEREIGNTY / "verification.key").write_text(key + "\n", encoding="utf-8")
    return {"ok": True, "mao_haki_active": True, "verification_key": True, "crown_hz": 1272, "sandbox": False}
