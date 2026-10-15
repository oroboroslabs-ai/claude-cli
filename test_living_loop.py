#!/usr/bin/env python3
"""Smoke — LivingLoop continuous + persist + reflexion."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
# Only src — root claude_o_cli.py is a shadow module, not the package
sys.path = [str(SRC)] + [p for p in sys.path if Path(p).resolve() != ROOT.resolve()]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from claude_o_cli.living_loop import LivingLoop, STATE_FILE, MEMORY_FILE


def main() -> int:
    loop = LivingLoop()
    loop.start()
    assert loop.get_state().get("running") is True
    print("started", loop.get_state().get("heartbeat_at") or "pending")

    r = loop.process("living loop smoke probe")
    assert r.get("ok") is not None
    print("process cycle", r.get("cycle"), "verified", r.get("verified"), "phase", r.get("phase"))

    loop.arm("continuous goal smoke")
    assert loop.get_state().get("mode") == "loop"
    r2 = loop.run_cycle("continuous goal smoke")
    print("armed cycle", r2.get("cycle"), "verified", r2.get("verified"))

    loop.save_loop_state()
    assert STATE_FILE.exists()
    loop2 = LivingLoop()
    st = loop2.load_loop_state()
    assert st.get("goal") == "continuous goal smoke" or st.get("mode") in ("loop", "chat")
    print("persisted", STATE_FILE, "goal", st.get("goal"), "cycle", st.get("cycle"))

    loop.disarm()
    loop.stop()
    print("memory", MEMORY_FILE.exists(), "lessons", len(loop.memory.lessons))
    print("LIVING_LOOP_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
