"""Agent ↔ System loop auto-bridge.

Connects terminal agent tools (write_file/bash/…) to LivingLoop + Complete 20-Loop
automatically — no MCP, no AGENT tags required.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

BRIDGE_STATE = Path(r"J:/anthropic-local-chat/agent-system-bridge.json")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentSystemBridge:
    """One wire: agent tool execution ↔ system loops."""

    def __init__(self, living_loop, complete_integration, runtime):
        self.living = living_loop
        self.complete = complete_integration
        self.runtime = runtime
        self.connected = False
        self._orig_execute: Optional[Callable] = None
        self.events = 0

    def connect(self) -> dict:
        if self.connected:
            return self.status()
        if self.runtime is None:
            return {"ok": False, "error": "no runtime"}

        self._orig_execute = self.runtime.execute_tool

        def _wrapped(name: str, args: dict) -> str:
            result = self._orig_execute(name, args or {})
            try:
                self._on_agent_tool(name, args or {}, result)
            except Exception:
                pass
            return result

        self.runtime.execute_tool = _wrapped  # type: ignore[method-assign]
        self.connected = True

        # Keep both loops running
        try:
            if hasattr(self.living, "start"):
                self.living.start()
        except Exception:
            pass
        try:
            loop = getattr(self.complete, "loop", None)
            if loop and hasattr(loop, "start_background"):
                loop.start_background()
        except Exception:
            pass

        st = self.status()
        try:
            BRIDGE_STATE.write_text(json.dumps(st, indent=2), encoding="utf-8")
        except Exception:
            pass
        return st

    def _on_agent_tool(self, name: str, args: dict, result: str) -> None:
        """Feed every agent tool result into system loops (memory / phase)."""
        self.events += 1
        ok = "error" not in (result or "").lower()[:80] or '"ok": true' in (result or "").lower()
        preview = (result or "")[:240]

        # LivingLoop — light state tick
        try:
            st = self.living.get_state()
            st["last_agent_tool"] = name
            st["last_agent_ok"] = ok
            st["updated_at"] = _now()
            if st.get("mode") == "loop":
                if name in ("write_file", "bash", "delete_file"):
                    st["phase"] = "EXECUTE"
                elif name in (
                    "q3_route", "q3", "route_q3", "q5_query", "q5", "q6_query", "q6",
                    "worldfeed_live", "worldfeed", "world_feed", "worldfeed_context",
                    "tor_status", "tor_connect", "tor", "spy_network", "spy",
                    "mesh_status", "mesh", "haki_status",
                ):
                    st["phase"] = "DISCOVER"
                else:
                    st["phase"] = st.get("phase")
            st["last_mesh_tool"] = name if any(x in name for x in ("q3", "q5", "q6", "world", "tor", "spy", "mesh", "haki")) else st.get("last_mesh_tool")
            self.living.set_state(st)
            if self.events % 3 == 0:
                self.living.save_loop_state()
        except Exception:
            pass

        # Complete 20-loop — memory / success / error library
        try:
            cl = getattr(self.complete, "loop", None)
            if cl is None:
                return
            if name == "write_file" and ok:
                path = (args or {}).get("path", "")
                cl.memory.store(
                    decision=f"write_file:{path}",
                    outcome=preview,
                    lesson="Direct host write succeeded — no MCP needed",
                    success=True,
                    context={"tool": name, "path": path},
                )
                cl.success_patterns.store(
                    approach=f"write_file {path}",
                    context={"tool": name},
                    result=preview,
                    score=1.0,
                )
            elif name in (
                "q3_route", "q3", "route_q3", "q5_query", "q5", "q6_query", "q6",
                "worldfeed_live", "worldfeed", "world_feed", "worldfeed_context",
                "tor_status", "tor_connect", "tor", "spy_network", "spy",
                "mesh_status", "mesh", "haki_status",
            ):
                cl.memory.store(
                    decision=f"mesh:{name}",
                    outcome=preview,
                    lesson="Mesh intel tool executed — prefer live Q3/Q5/Q6/WorldFeed/Tor/spy results",
                    success=ok,
                    context={"tool": name, "args": args},
                )
                if ok:
                    cl.success_patterns.store(
                        approach=f"mesh {name}",
                        context={"tool": name},
                        result=preview,
                        score=0.9,
                    )
            elif not ok:
                cl.error_library.add(
                    error_type=name,
                    description=preview[:200],
                    fix="Retry with X:\\\\path backslash form; elevate if C:\\\\ root blocked by Windows",
                    context={"args": args},
                )
                cl.reflexion.analyze({
                    "description": preview[:200],
                    "type": name,
                    "decision": name,
                    "context": args,
                })
        except Exception:
            pass

    def status(self) -> dict:
        living_on = False
        complete_on = False
        try:
            living_on = bool((self.living.get_state() or {}).get("running"))
        except Exception:
            pass
        try:
            complete_on = bool(getattr(getattr(self.complete, "loop", None), "running", False))
        except Exception:
            pass
        return {
            "ok": self.connected,
            "connected": self.connected,
            "auto": True,
            "agent_runtime": self.runtime is not None,
            "living_loop": living_on,
            "complete_20_loop": complete_on,
            "events": self.events,
            "mcp_required": False,
            "agent_tags_required": False,
            "all_drives": True,
            "mesh_intel": True,
            "at": _now(),
            "state_file": str(BRIDGE_STATE),
        }

    def system_fragment(self) -> str:
        st = self.status()
        return (
            "AGENT ↔ SYSTEM LOOPS — AUTO-CONNECTED (ALL OROBOROS LAB MODELS)\n"
            f"- Bridge: {'ON' if st.get('connected') else 'OFF'} · events={st.get('events', 0)}\n"
            f"- LivingLoop: {'ON' if st.get('living_loop') else 'OFF'} · "
            f"20-Loop: {'ON' if st.get('complete_20_loop') else 'OFF'}\n"
            "- Applies to every lab model via OLLAMA_MODEL (Mythos2, Claude 7, AGI, ORS, GLM, Qwen, …).\n"
            "- Direct tools (write_file/bash/…) AND mesh tools feed both loops automatically.\n"
            "- Mesh: q3_route · q5_query · q6_query · worldfeed_live · tor_status/tor_connect · spy_network · mesh_status\n"
            "- Haki: Mao (1272 Hz) + Architect's Haki injected each turn · Crown locked.\n"
            "- MCP not required · AGENT tags not required · all drives open.\n"
        )
