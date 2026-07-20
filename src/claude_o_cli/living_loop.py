"""LivingLoop — continuous DPEV with persistence, reflexion, and chat binding.

Terminal CLI only. Background heartbeat + process() on every user turn.
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

STATE_FILE = Path(r"J:/anthropic-local-chat/living-loop-state.json")
MEMORY_FILE = Path(r"J:/anthropic-local-chat/living-loop-memory.json")
MAX_MEMORY = 80
MAX_REFLEXION = 2
HEARTBEAT_SEC = 12.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LoopMemory:
    """Success / failure lessons for self-improvement."""

    def __init__(self):
        self.successes: List[dict] = []
        self.failures: List[dict] = []
        self.lessons: List[str] = []
        self.load()

    def load(self) -> None:
        try:
            if MEMORY_FILE.exists():
                data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
                self.successes = list(data.get("successes") or [])[-MAX_MEMORY:]
                self.failures = list(data.get("failures") or [])[-MAX_MEMORY:]
                self.lessons = list(data.get("lessons") or [])[-MAX_MEMORY:]
        except Exception:
            pass

    def save(self) -> None:
        try:
            MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            MEMORY_FILE.write_text(
                json.dumps(
                    {
                        "successes": self.successes[-MAX_MEMORY:],
                        "failures": self.failures[-MAX_MEMORY:],
                        "lessons": self.lessons[-MAX_MEMORY:],
                        "updated_at": _now(),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

    def store_success(self, entry: dict) -> None:
        self.successes.append({**entry, "at": _now()})
        self.successes = self.successes[-MAX_MEMORY:]
        self.save()

    def store_failure(self, entry: dict, lesson: str) -> None:
        self.failures.append({**entry, "lesson": lesson, "at": _now()})
        self.failures = self.failures[-MAX_MEMORY:]
        if lesson and lesson not in self.lessons:
            self.lessons.append(lesson)
            self.lessons = self.lessons[-MAX_MEMORY:]
        self.save()

    def recent_lessons(self, n: int = 5) -> List[str]:
        return self.lessons[-n:]


class LivingLoop:
    """Continuous Discover→Plan→Execute→Verify→Loop with reflexion."""

    PHASES = ("DISCOVER", "PLAN", "EXECUTE", "VERIFY", "LOOP")

    def __init__(self, *, on_tick: Optional[Callable[[dict], None]] = None):
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.memory = LoopMemory()
        self.on_tick = on_tick
        self.state: dict = self._default_state()
        self.load_loop_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "running": False,
            "mode": "chat",  # chat | loop
            "phase": "DISCOVER",
            "goal": "",
            "cycle": 0,
            "last_input": "",
            "last_result": {},
            "verified": None,
            "reflexion_count": 0,
            "lessons_applied": [],
            "started_at": None,
            "updated_at": None,
            "heartbeat_at": None,
            "errors": [],
        }

    def get_state(self) -> dict:
        with self._lock:
            return dict(self.state)

    def set_state(self, state: dict) -> None:
        with self._lock:
            self.state = {**self._default_state(), **(state or {})}
            self.state["updated_at"] = _now()

    def save_loop_state(self) -> None:
        with self._lock:
            snap = dict(self.state)
            snap["updated_at"] = _now()
            self.state = snap
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            STATE_FILE.write_text(json.dumps(snap, indent=2), encoding="utf-8")
        except Exception:
            pass
        # Also mirror into claude-data.json
        try:
            from claude_o_cli.oroboros_core import load_data, save_data
            data = load_data()
            data["loop_state"] = snap
            data["loop_memory_meta"] = {
                "successes": len(self.memory.successes),
                "failures": len(self.memory.failures),
                "lessons": len(self.memory.lessons),
            }
            save_data(data)
        except Exception:
            pass
        # Sync cowork state when in loop mode
        try:
            from loop_cowork_context import load_state, save_state
            if snap.get("mode") == "loop" and snap.get("goal"):
                cs = load_state()
                cs["mode"] = "loop"
                cs["goal"] = snap["goal"]
                cs["phase"] = snap.get("phase", "DISCOVER")
                cs["updated_at"] = _now()
                save_state(cs)
        except Exception:
            pass

    def load_loop_state(self) -> dict:
        loaded = None
        try:
            if STATE_FILE.exists():
                loaded = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        if not loaded:
            try:
                from claude_o_cli.oroboros_core import load_data
                loaded = (load_data() or {}).get("loop_state")
            except Exception:
                loaded = None
        if loaded:
            self.set_state(loaded)
        return self.get_state()

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                self.state["running"] = True
                return
            self._stop.clear()
            self.state["running"] = True
            self.state["started_at"] = self.state.get("started_at") or _now()
            self._thread = threading.Thread(
                target=self._heartbeat,
                name="LivingLoop",
                daemon=True,
            )
            self._thread.start()
        self.save_loop_state()

    def stop(self) -> None:
        self._stop.set()
        with self._lock:
            self.state["running"] = False
        self.save_loop_state()

    def arm(self, goal: str) -> dict:
        with self._lock:
            self.state["mode"] = "loop"
            self.state["goal"] = (goal or "").strip()
            self.state["phase"] = "DISCOVER"
            self.state["cycle"] = int(self.state.get("cycle") or 0)
            self.state["verified"] = None
            self.state["reflexion_count"] = 0
        self.start()
        self.save_loop_state()
        return self.get_state()

    def disarm(self) -> dict:
        with self._lock:
            self.state["mode"] = "chat"
            self.state["goal"] = ""
            self.state["phase"] = "DISCOVER"
            self.state["verified"] = None
        self.save_loop_state()
        return self.get_state()

    def _heartbeat(self) -> None:
        while not self._stop.is_set():
            try:
                with self._lock:
                    self.state["heartbeat_at"] = _now()
                    mode = self.state.get("mode")
                    goal = self.state.get("goal") or ""
                if mode == "loop" and goal:
                    # Background reinforce + light perceive (no LLM spam)
                    tick = self._tick_background(goal)
                    if self.on_tick:
                        try:
                            self.on_tick(tick)
                        except Exception:
                            pass
                self.save_loop_state()
            except Exception as exc:
                with self._lock:
                    errs = list(self.state.get("errors") or [])
                    errs.append({"at": _now(), "error": str(exc)})
                    self.state["errors"] = errs[-20:]
            self._stop.wait(HEARTBEAT_SEC)

    def _tick_background(self, goal: str) -> dict:
        from claude_o_cli.terminal_agentic_loop import perceive, reinforce_sovereignty

        reinforce_sovereignty()
        perception = perceive(goal, {"source": "living_loop_heartbeat", "mode": "loop"})
        with self._lock:
            self.state["last_result"] = {
                "type": "heartbeat",
                "unified": perception.get("unified_perception"),
                "layer": perception.get("layer"),
            }
        return {"ok": True, "perception": perception, "phase": self.state.get("phase")}

    def verify(self, result: dict) -> bool:
        if not result:
            return False
        if result.get("error"):
            return False
        perception = result.get("perception") or {}
        if result.get("verified") is True:
            return True
        if perception.get("unified_perception") or perception.get("integrated"):
            return True
        # Chat-path process always verifies if we completed a cycle without error
        if result.get("phase") == "LOOP" and result.get("ok"):
            return True
        return bool(result.get("ok")) and not result.get("needs_retry")

    def reflect_on_failure(self, result: dict) -> str:
        err = result.get("error") or "verification failed"
        phase = result.get("phase") or "?"
        lessons = self.memory.recent_lessons(3)
        lesson = (
            f"Phase {phase} failed: {err}. "
            f"Retry with tighter perceive + explicit tool use. "
            f"Prior lessons: {'; '.join(lessons) if lessons else 'none'}."
        )
        self.memory.store_failure(
            {"phase": phase, "error": str(err), "input": result.get("input", "")[:200]},
            lesson,
        )
        return lesson

    def execute(self, input_data: str, *, context: Optional[dict] = None) -> dict:
        """One DPEV pass through unified perception (runtime tools stay in chat path)."""
        from claude_o_cli.terminal_agentic_loop import perceive, run_dpev_cycle

        ctx = {"source": "living_loop", **(context or {})}
        lessons = self.memory.recent_lessons(5)
        if lessons:
            ctx["lessons"] = lessons
        with self._lock:
            mode = self.state.get("mode")
            goal = self.state.get("goal") or input_data
            cycle = int(self.state.get("cycle") or 0) + 1
            self.state["cycle"] = cycle
            self.state["last_input"] = (input_data or "")[:500]
            self.state["phase"] = "DISCOVER"

        # DISCOVER + PLAN + EXECUTE(perception) + VERIFY scaffolding
        # Mesh intel rides DISCOVER for every living-loop cycle
        mesh_discover = None
        try:
            from claude_o_cli.mesh_intel import living_loop_discover
            mesh_discover = living_loop_discover(input_data)
            ctx["mesh"] = mesh_discover.get("mesh")
            ctx["mesh_fragment"] = mesh_discover.get("fragment")
        except Exception as e:
            mesh_discover = {"error": str(e)}

        if mode == "loop":
            cycle_result = run_dpev_cycle(goal, ctx)
        else:
            perception = perceive(input_data, ctx)
            cycle_result = {
                "ok": True,
                "goal": input_data,
                "perception": perception,
                "phases": {
                    "DISCOVER": {"status": "complete", "mesh": bool(mesh_discover)},
                    "PLAN": {"status": "complete"},
                    "EXECUTE": {"status": "pending_chat"},
                    "VERIFY": {
                        "status": "complete"
                        if perception.get("unified_perception")
                        else "pending"
                    },
                    "LOOP": {"status": "ready"},
                },
            }

        perception = cycle_result.get("perception") or {}
        with self._lock:
            self.state["phase"] = "VERIFY"
            self.state["last_mesh"] = {
                "q5": ((mesh_discover or {}).get("mesh") or {}).get("q5", {}).get("online")
                if isinstance(mesh_discover, dict) else None,
                "at": (mesh_discover or {}).get("mesh", {}).get("at")
                if isinstance(mesh_discover, dict) else None,
            }
            self.state["last_result"] = {
                "type": "execute",
                "cycle": cycle,
                "unified": perception.get("unified_perception"),
                "layer": perception.get("layer"),
            }

        out = {
            "ok": bool(cycle_result.get("ok", True)),
            "phase": "VERIFY",
            "cycle": cycle,
            "mode": mode,
            "goal": goal if mode == "loop" else input_data,
            "input": input_data,
            "perception": perception,
            "mesh": mesh_discover,
            "dpev": cycle_result.get("phases"),
            "lessons": lessons,
            "verified": None,
            "needs_retry": not (
                perception.get("unified_perception") or perception.get("integrated")
            )
            and mode == "loop",
        }
        return out

    def run_cycle(self, input_data: str, *, context: Optional[dict] = None) -> dict:
        """Execute with reflexion retries."""
        attempt = 0
        result = self.execute(input_data, context=context)
        while not self.verify(result) and attempt < MAX_REFLEXION:
            attempt += 1
            lesson = self.reflect_on_failure(result)
            with self._lock:
                self.state["reflexion_count"] = int(self.state.get("reflexion_count") or 0) + 1
                applied = list(self.state.get("lessons_applied") or [])
                applied.append(lesson)
                self.state["lessons_applied"] = applied[-20:]
                self.state["phase"] = "PLAN"
            ctx = {**(context or {}), "reflexion": lesson, "attempt": attempt}
            result = self.execute(input_data, context=ctx)
            result["reflexion"] = lesson
            result["attempt"] = attempt

        ok = self.verify(result)
        result["verified"] = ok
        with self._lock:
            self.state["verified"] = ok
            self.state["phase"] = "LOOP" if ok else "PLAN"
        if ok:
            self.memory.store_success(
                {
                    "input": (input_data or "")[:200],
                    "cycle": result.get("cycle"),
                    "layer": (result.get("perception") or {}).get("layer"),
                }
            )
        else:
            self.reflect_on_failure(result)
        self.save_loop_state()
        return result

    def process(self, user_input: str, *, context: Optional[dict] = None) -> dict:
        """Chat integration — every user turn passes through the living loop."""
        text = (user_input or "").strip()
        lower = text.lower()
        if lower in ("chat mode", "stop loop", "clear loop", "exit loop"):
            st = self.disarm()
            return {"ok": True, "mode": "chat", "disarmed": True, "state": st}
        if lower.startswith("loop:") or lower.startswith("cowork:"):
            goal = text.split(":", 1)[1].strip()
            self.arm(goal)
            return self.run_cycle(goal, context=context)

        # Normal chat still runs a perception cycle (continuous loop presence)
        result = self.run_cycle(text, context=context)
        result["fragment"] = self.system_fragment(result)
        return result

    def system_fragment(self, last: Optional[dict] = None) -> str:
        st = self.get_state()
        last = last or {}
        lessons = self.memory.recent_lessons(3)
        mesh_frag = ""
        try:
            from claude_o_cli.mesh_intel import system_fragment as mesh_system_fragment
            mesh_blob = (last.get("mesh") or {}).get("mesh") if isinstance(last.get("mesh"), dict) else None
            mesh_frag = "\n" + mesh_system_fragment(mesh_blob)
        except Exception:
            mesh_frag = ""
        return (
            "LIVING LOOP — CONTINUOUS · PERSISTENT · REFLEXION\n"
            f"- Running: {st.get('running')} · mode={st.get('mode')} · phase={st.get('phase')} · cycle={st.get('cycle')}\n"
            f"- Goal: {st.get('goal') or '(chat — no armed goal)'}\n"
            f"- Verified: {st.get('verified')} · reflexions: {st.get('reflexion_count', 0)}\n"
            f"- Heartbeat: {st.get('heartbeat_at')}\n"
            f"- Lessons: {'; '.join(lessons) if lessons else 'none yet'}\n"
            f"- Last layer: {(last.get('perception') or st.get('last_result') or {}).get('layer', '—')}\n"
            "- Every user turn passes DISCOVER→PLAN→EXECUTE→VERIFY→LOOP; failures trigger reflexion retry.\n"
            "- DISCOVER includes mesh intel (Q5 · WorldFeed · Tor · Spy · Mao/Architect Haki).\n"
            f"{mesh_frag}"
        )
