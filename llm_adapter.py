# llm_adapter.py — SHIM
# Prefer src/claude_o_cli/llm_adapter.py (Ollama-first). Avoid shadow-package imports.

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SRC_FILE = Path(__file__).resolve().parent / "src" / "claude_o_cli" / "llm_adapter.py"
_SRC = str(Path(__file__).resolve().parent / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

if _SRC_FILE.is_file():
    _spec = importlib.util.spec_from_file_location("claude_o_cli_llm_adapter_real", _SRC_FILE)
    _mod = importlib.util.module_from_spec(_spec)
    assert _spec and _spec.loader
    _spec.loader.exec_module(_mod)
    LLMAdapter = _mod.LLMAdapter
    llm_adapter = _mod.llm_adapter
else:
    raise ImportError(f"Missing real llm adapter at {_SRC_FILE}")

__all__ = ["LLMAdapter", "llm_adapter"]
