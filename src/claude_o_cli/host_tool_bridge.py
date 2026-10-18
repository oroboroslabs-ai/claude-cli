"""Shared host-tool backend for terminal CLI + HTML CLI UI + local chat 8787.

Canonical executor: claude_o_cli.oroboros_core.ToolRegistry (same as terminal chat).
Surfaces:
  - Terminal CLI (cmd_chat / AgenticRuntime)
  - HTML CLI UI (run_cli.py :5000 /api/host/tool + /api/chat tool loop)
  - Local chat (8787 /api/host/tool → this module via python)

Production tools (premiere_pro / call_api) are routed to the Premiere Pro MCP
HTTP gateway (127.0.0.1:3031/mcp) with friendly-arg → MCP-schema mapping so
model-emitted calls like {"method":"import_media","path":[...]} actually run.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

BRIDGE_LOG = Path(r"J:/anthropic-local-chat/host-tool-bridge.log.jsonl")
STATE_PATH = Path(r"J:/anthropic-local-chat/host-tool-bridge-state.json")

PREMIERE_GATEWAY = "http://127.0.0.1:3031/mcp"
PREMIERE_EG_DIR = Path(r"C:/Program Files/Adobe/Adobe Premiere Pro 2026/Essential Graphics")
AME_PRESET_DIR = Path(r"C:/Program Files/Adobe/Adobe Media Encoder 2026/MediaIO/systempresets")
AME_LUT_DIR = Path(r"C:/Program Files/Adobe/Adobe Media Encoder 2026/Lumetri/LUTs")
OVERLAY_DIR = Path(r"Q:/oroboros-brand-dam/overlays")
COMFYUI_URL = "http://127.0.0.1:8188"
COMFYUI_OUT = Path(r"Q:/ComfyUI/output")
COMFYUI_MODEL = "wan2.2_ti2v_5B_turbo_480p_fp16.safetensors"
COMFYUI_VAE = "wan2.2_vae_bf16.safetensors"
COMFYUI_T5 = "umt5_xxl_fp8_e4m3fn.safetensors"

HOST_TOOL_NAMES = frozenset({
    "write_file", "read_file", "list_dir", "delete_file", "bash",
    "write", "read", "ls", "dir", "shell", "cmd", "powershell", "delete", "rm",
    "premiere_pro", "call_api", "comfyui_generate", "pillow_text_overlay",
})

_ALIASES = {
    "write": "write_file",
    "read": "read_file",
    "ls": "list_dir",
    "dir": "list_dir",
    "shell": "bash",
    "cmd": "bash",
    "powershell": "bash",
    "delete": "delete_file",
    "rm": "delete_file",
}

_permissions = None
_tools = None
_event_count = 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def alias_tool(name: str) -> str:
    key = (name or "").strip()
    return _ALIASES.get(key.lower(), key)


def get_shared_permissions():
    global _permissions
    if _permissions is None:
        from claude_o_cli.oroboros_core import PermissionManager
        _permissions = PermissionManager()
    return _permissions


def get_shared_tools():
    """Singleton ToolRegistry — terminal CLI and HTTP surfaces share this code path."""
    global _tools
    if _tools is None:
        from claude_o_cli.oroboros_core import ToolRegistry
        _tools = ToolRegistry(get_shared_permissions())
        try:
            from claude_o_cli.mesh_intel import register_mesh_tools
            register_mesh_tools(_tools)
        except Exception:
            pass
        try:
            from claude_o_cli.nullframe_bridge import register_nullframe_tools
            register_nullframe_tools(_tools)
        except Exception:
            pass
        try:
            from claude_o_cli.linalg_bridge import register_linalg_tools
            register_linalg_tools(_tools)
        except Exception:
            pass
        try:
            from claude_o_cli.phi_library import register_phi_library_tools
            register_phi_library_tools(_tools)
        except Exception:
            pass
        try:
            from claude_o_cli.media_gen import register_media_gen_tools
            register_media_gen_tools(_tools)
        except Exception:
            pass
        try:
            from claude_o_cli.skill_deck import register_skill_deck_tools
            register_skill_deck_tools(_tools)
        except Exception:
            pass
        try:
            from claude_o_cli.cordis_bridge import register_cordis_tools
            register_cordis_tools(_tools)
        except Exception:
            pass
        try:
            from claude_o_cli.orca_cli_tool import run_orca_cli
            from claude_o_cli.oroboros_core import Tool
            if "orca_cli" not in _tools.tools:
                _tools.register(Tool("orca_cli", "Orca CLI — worktrees/terminals/handoffs through the orca binary", run_orca_cli, False))
        except Exception:
            pass
    return _tools


def status(*, source: str = "status") -> dict:
    tools = get_shared_tools()
    names = [t["name"] for t in tools.list_tools()]
    return {
        "ok": True,
        "connected": True,
        "backend": "claude_o_cli.host_tool_bridge",
        "canonical": "oroboros_core.ToolRegistry",
        "sandbox": False,
        "container": False,
        "all_drives": True,
        "mcp_required": False,
        "agent_tags_required": False,
        "surfaces": [
            "terminal_cli",
            "html_cli_ui:5000",
            "local_chat:8787",
            "q_chat_anthropic_html",
            "mesh_intel",
        ],
        "mesh": {
            "q3": "http://127.0.0.1:8000",
            "q5": "http://127.0.0.1:8101",
            "q6": "mesh://q6_acquisition",
            "worldfeed": "http://127.0.0.1:8100",
            "tor": "socks5://127.0.0.1:9050",
            "spy_network": True,
            "mao_haki": True,
            "architects_haki": True,
        },
        "tools": names + ["premiere_pro", "call_api"],
        "host_tools": sorted(n for n in names if n in (
            "write_file", "read_file", "list_dir", "delete_file", "bash"
        )),
        "production_tools": ["premiere_pro", "call_api"],
        "premiere_gateway": PREMIERE_GATEWAY,
        "mesh_tools": sorted(n for n in names if n in (
            "q3_route", "q5_query", "q6_query", "worldfeed_live", "tor_status", "tor_connect",
            "spy_network", "mesh_status", "q3", "route_q3", "q5", "q6", "worldfeed",
            "world_feed", "worldfeed_context", "tor", "spy", "mesh", "haki_status",
        )),
        "events": _event_count,
        "source": source,
        "state_file": str(STATE_PATH),
        "protocol": '{"tool":"write_file","args":{"path":"J:\\\\note.txt","content":"hello"}}',
        "at": _now(),
    }


def _log_event(record: dict) -> None:
    try:
        BRIDGE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with BRIDGE_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
        STATE_PATH.write_text(json.dumps({
            "ok": True,
            "last": record,
            "events": _event_count,
            "at": _now(),
        }, indent=2), encoding="utf-8")
    except Exception:
        pass


# ============================================================
# PREMIERE PRO PRODUCTION ROUTING (live MCP gateway :3031)
# ============================================================

def _premiere_rpc(method: str, params: dict, timeout: float = 120.0) -> dict:
    """Call the Premiere MCP HTTP gateway (JSON-RPC tools/call)."""
    payload = {"method": method, "params": params}
    req = urllib.request.Request(
        PREMIERE_GATEWAY,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _premiere_tool(name: str, arguments: dict, timeout: float = 120.0) -> dict:
    """Call one Premiere MCP tool; returns the structuredContent dict."""
    resp = _premiere_rpc("tools/call", {"name": name, "arguments": arguments}, timeout=timeout)
    result = resp.get("result") or {}
    sc = result.get("structuredContent") or {}
    if sc:
        return sc
    text = result.get("content") or []
    if text:
        try:
            return json.loads(text[0].get("text", "{}"))
        except Exception:
            return {"ok": False, "error": text[0].get("text", "no content")[:300]}
    return {"ok": False, "error": "no structured content from Premiere"}


def _premiere_sequences() -> list:
    """Live sequence list (id + name) from Premiere."""
    try:
        d = _premiere_tool("list_sequences", {}, timeout=20.0)
        return d.get("sequences") or []
    except Exception:
        return []


def _premiere_resolve_sequence(seq_ref: Any) -> Optional[str]:
    """Resolve a model-friendly sequence reference to a real sequenceId."""
    if not seq_ref:
        return None
    if isinstance(seq_ref, str) and len(seq_ref) == 36 and "-" in seq_ref:
        return seq_ref
    seqs = _premiere_sequences()
    if not seqs:
        return None
    name = str(seq_ref).strip().lower()
    for s in seqs:
        if str(s.get("id", "")).lower() == name:
            return s.get("id")
    for s in seqs:
        if name in str(s.get("name", "")).lower():
            return s.get("id")
    return None


def _premiere_active_sequence() -> Optional[str]:
    try:
        d = _premiere_tool("get_active_sequence", {}, timeout=20.0)
        return (d.get("sequence") or {}).get("id") or d.get("id")
    except Exception:
        return None


def _premiere_find_item(name: str) -> Optional[str]:
    """Find a project item id by name (exact, then substring)."""
    try:
        d = _premiere_tool("find_project_item_by_name", {"name": name}, timeout=20.0)
        items = d.get("items") or []
        if items:
            return items[0].get("id")
    except Exception:
        pass
    try:
        d = _premiere_tool("list_project_items", {}, timeout=20.0)
        for it in d.get("items") or []:
            if name.lower() in str(it.get("name", "")).lower():
                return it.get("id")
    except Exception:
        pass
    return None


def _premiere_import_media(path: str) -> dict:
    """Import media; returns {ok, projectItemId, name}."""
    try:
        d = _premiere_tool("import_media", {"filePath": path}, timeout=60.0)
        if d.get("success") is False:
            return {"ok": False, "error": d.get("message") or "import failed"}
        return {
            "ok": True,
            "projectItemId": d.get("id") or d.get("projectItemId"),
            "name": d.get("name"),
            "alreadyImported": bool(d.get("alreadyImported")),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _generate_text_overlay_png(text: str, font_size: int = 72, color: tuple = (255, 255, 255, 255)) -> Path:
    """Safe Sovereign Workaround: render text to a transparent PNG with Pillow.

    Premiere 26.0.1's UXP API cannot write MOGRT text components
    (getMGTComponent returns null), so text overlays are generated
    externally and imported as static assets instead.
    """
    from PIL import Image, ImageDraw, ImageFont

    font = None
    # Brand spec (Q:/oroboros-brand-dam/oroboros-anthropic/BRAND.json):
    #   display: Poppins (download → fonts/Poppins-Bold.ttf for brand-perfect overlays)
    #   ui_sans: Inter (already in DAM)
    #   wordmark mirror: Cormorant Garamond (already in DAM)
    # Fallbacks: Segoe UI → Arial (per brand fallback_display).
    brand_fonts = (
        r"Q:/oroboros-brand-dam/oroboros-anthropic/fonts/Poppins-Bold.ttf",
        r"Q:/oroboros-brand-dam/oroboros-anthropic/fonts/Poppins-SemiBold.ttf",
        r"Q:/oroboros-brand-dam/oroboros-anthropic/fonts/Poppins-Regular.ttf",
        r"Q:/oroboros-brand-dam/oroboros-anthropic/fonts/Inter-Bold.ttf",
        r"Q:/oroboros-brand-dam/oroboros-anthropic/fonts/Inter-Regular.ttf",
        r"Q:/oroboros-brand-dam/oroboros-anthropic/fonts/CormorantGaramond-SemiBold.ttf",
        r"C:/Users/incoguser/AppData/Local/Microsoft/Windows/Fonts/Lato-Bold.ttf",
        r"C:/Users/incoguser/AppData/Local/Microsoft/Windows/Fonts/Lato-Semibold.ttf",
        r"C:/Users/incoguser/AppData/Local/Microsoft/Windows/Fonts/Lato-Regular.ttf",
        r"C:/Windows/Fonts/segoeuib.ttf",
        r"C:/Windows/Fonts/arialbd.ttf",
        r"C:/Windows/Fonts/arial.ttf",
    )
    for candidate in brand_fonts:
        try:
            font = ImageFont.truetype(candidate, font_size)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    dummy = Image.new("RGBA", (1, 1))
    dd = ImageDraw.Draw(dummy)
    bbox = dd.textbbox((0, 0), text, font=font)
    pad = 24
    w = (bbox[2] - bbox[0]) + pad * 2
    h = (bbox[3] - bbox[1]) + pad * 2

    img = Image.new("RGBA", (max(w, 64), max(h, 64)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((pad - bbox[0], pad - bbox[1]), text, fill=color, font=font)

    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
    import uuid
    out = OVERLAY_DIR / f"text_overlay_{uuid.uuid4().hex[:8]}.png"
    img.save(out)
    return out


def _premiere_export_preset() -> Optional[str]:
    """Find a usable H.264 export preset (.epr) on disk."""
    candidates = [
        AME_PRESET_DIR / "3F3F3F3F_4D6F6F56" / "H264 Match Source - High bitrate.epr",
        AME_PRESET_DIR / "3F3F3F3F_4D6F6F56" / "01 - Match Source.epr",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    try:
        hits = sorted(AME_PRESET_DIR.rglob("*.epr"))
        for h in hits:
            if "h264" in h.stem.lower() or "match source" in h.stem.lower():
                return str(h)
        if hits:
            return str(hits[0])
    except Exception:
        pass
    return None


def _premiere_lut() -> Optional[str]:
    """Find a bundled creative LUT (.cube) for color grading."""
    try:
        hits = sorted((AME_LUT_DIR / "Creative").glob("*.cube"))
        if hits:
            return str(hits[0])
        hits = sorted(AME_LUT_DIR.rglob("*.cube"))
        if hits:
            return str(hits[0])
    except Exception:
        pass
    return None


def _premiere_mogrt() -> Optional[str]:
    """Find a bundled MOGRT template for text overlays."""
    try:
        hits = sorted((PREMIERE_EG_DIR / "Lower Thirds").glob("*.mogrt"))
        if hits:
            return str(hits[0])
        hits = sorted(PREMIERE_EG_DIR.rglob("*.mogrt"))
        if hits:
            return str(hits[0])
    except Exception:
        pass
    return None


def _premiere_sequence_structure(seq_id: str) -> dict:
    try:
        d = _premiere_tool("get_sequence_structure", {"sequenceId": seq_id}, timeout=30.0)
        return d.get("data") or d
    except Exception:
        return {}


def _premiere_first_clip(seq_id: str) -> Optional[str]:
    """First video clip nodeId on the lowest video track (for LUT/transition)."""
    try:
        st = _premiere_sequence_structure(seq_id)
        for tr in st.get("videoTracks") or []:
            clips = tr.get("clips") or []
            if clips:
                return clips[0].get("nodeId")
    except Exception:
        pass
    return None


def _premiere_handle(method: str, args: dict) -> dict:
    """Route a model-emitted premiere_pro call to the real MCP tool.

    Friendly-arg mapping (what the model emits → MCP schema):
      import_media:    path[]/path → filePath (first existing file)
      add_transition:  sequence/type → sequenceId + transitionName (clip-based)
      add_text_overlay: sequence/text → sequenceId + text (+ bundled MOGRT)
      apply_lut:       sequence → sequenceId + clipId + bundled LUT
      export_sequence: sequence/output_path → sequenceId + outputPath + preset
    """
    method = (method or "").strip().lower()
    args = args or {}

    if method in ("verify", "verify_premiere_connection", "status", "ping"):
        try:
            d = _premiere_tool("verify_premiere_connection", {}, timeout=30.0)
            return {"ok": bool(d.get("success")), "premiere": d}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    if method in ("list_sequences", "sequences"):
        try:
            return {"ok": True, "sequences": _premiere_sequences()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    if method in ("import_media", "import"):
        raw = args.get("path") or args.get("paths") or args.get("filePath") or args.get("file")
        if isinstance(raw, list):
            raw = next((p for p in raw if p and Path(p).exists()), None)
        if not raw:
            return {"ok": False, "error": "import_media needs path (file to import)"}
        if not Path(raw).exists():
            return {"ok": False, "error": f"file not found: {raw}"}
        return _premiere_import_media(str(raw))

    if method in ("add_transition", "transition"):
        seq_ref = args.get("sequence") or args.get("sequenceId") or args.get("sequence_name")
        seq_id = _premiere_resolve_sequence(seq_ref) or _premiere_active_sequence()
        if not seq_id:
            return {"ok": False, "error": "no sequence found — open a project with sequences"}
        tname = args.get("type") or args.get("transitionName") or args.get("transition") or "Cross Dissolve"
        dur = args.get("duration") or 0.5
        clip = args.get("clipId") or _premiere_first_clip(seq_id)
        if not clip:
            return {"ok": False, "error": "no clip found to transition"}
        try:
            d = _premiere_tool("add_transition_to_clip", {
                "clipId": clip, "transitionName": tname,
                "position": "end", "duration": float(dur),
            }, timeout=60.0)
            return {"ok": bool(d.get("success")), "transition": d}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    if method in ("add_text_overlay", "text_overlay", "add_text"):
        seq_ref = args.get("sequence") or args.get("sequenceId") or args.get("sequence_name")
        seq_id = _premiere_resolve_sequence(seq_ref) or _premiere_active_sequence()
        if not seq_id:
            return {"ok": False, "error": "no sequence found — open a project with sequences"}
        text = args.get("text") or args.get("content") or ""
        if not text:
            return {"ok": False, "error": "add_text_overlay needs text"}
        track_index = int(args.get("trackIndex") or 2)
        start_time = float(args.get("startTime") or 0.0)
        duration = float(args.get("duration") or 4.0)

        # Path 1: native MOGRT text (works on most builds)
        mogrt = args.get("mogrtPath") or _premiere_mogrt()
        if mogrt:
            try:
                d = _premiere_tool("add_text_overlay", {
                    "text": text,
                    "sequenceId": seq_id,
                    "trackIndex": track_index,
                    "startTime": start_time,
                    "duration": duration,
                    "mogrtPath": mogrt,
                }, timeout=90.0)
                if d.get("success"):
                    return {"ok": True, "text_overlay": d, "method": "mogrt"}
            except Exception:
                pass

        # Path 2 (Safe Sovereign Workaround): Premiere 26.0.1 UXP API cannot
        # write MOGRT text (getMGTComponent → null). Generate a transparent
        # PNG with Pillow, import it, and place it on the timeline as an
        # overlay clip. Zero reliance on Adobe's MOGRT API.
        try:
            png_path = _generate_text_overlay_png(text)
            imp = _premiere_import_media(str(png_path))
            if not imp.get("ok"):
                return {"ok": False, "error": f"text overlay PNG import failed: {imp.get('error')}"}
            item_id = imp.get("projectItemId") or imp.get("id")
            placed = _premiere_tool("add_to_timeline", {
                "sequenceId": seq_id,
                "projectItemId": item_id,
                "trackIndex": track_index,
                "time": start_time,
                "insertMode": "overwrite",
                "linkAudio": False,
            }, timeout=90.0)
            return {
                "ok": bool(placed.get("success")),
                "method": "pillow_png",
                "text_overlay": placed,
                "overlay_path": str(png_path),
                "project_item_id": item_id,
                "note": "MOGRT text API unavailable on this Premiere build (getMGTComponent null); "
                        "used Pillow-generated PNG overlay instead.",
            }
        except Exception as e:
            return {"ok": False, "error": f"text overlay fallback failed: {e}"}

    if method in ("apply_lut", "lut", "color_grade"):
        seq_ref = args.get("sequence") or args.get("sequenceId") or args.get("sequence_name")
        seq_id = _premiere_resolve_sequence(seq_ref) or _premiere_active_sequence()
        if not seq_id:
            return {"ok": False, "error": "no sequence found — open a project with sequences"}
        clip = args.get("clipId") or _premiere_first_clip(seq_id)
        if not clip:
            return {"ok": False, "error": "no clip found to grade"}
        lut = args.get("lutPath") or _premiere_lut()
        if not lut:
            return {"ok": False, "error": "no LUT found for color grade"}
        try:
            d = _premiere_tool("apply_lut", {
                "clipId": clip, "lutPath": lut,
                "intensity": int(args.get("intensity") or 50),
            }, timeout=60.0)
            return {"ok": bool(d.get("success")), "lut": d}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    if method in ("export_sequence", "export", "render"):
        seq_ref = args.get("sequence") or args.get("sequenceId") or args.get("sequence_name")
        seq_id = _premiere_resolve_sequence(seq_ref) or _premiere_active_sequence()
        if not seq_id:
            return {"ok": False, "error": "no sequence found — open a project with sequences"}
        out = args.get("output_path") or args.get("outputPath") or args.get("output") or args.get("path")
        if not out:
            out = str(Path.home() / "Desktop" / "oroboros_export.mp4")
        preset = args.get("presetPath") or _premiere_export_preset()
        if not preset:
            return {"ok": False, "error": "no export preset found (.epr)"}
        try:
            d = _premiere_tool("export_sequence", {
                "sequenceId": seq_id,
                "outputPath": str(out),
                "presetPath": preset,
                "allowOverwrite": True,
            }, timeout=60.0)
            return {"ok": bool(d.get("success")), "export": d}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    if method in ("get_project_info", "project_info"):
        try:
            return {"ok": True, "project": _premiere_tool("get_project_info", {}, timeout=30.0)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    if method in ("get_render_queue_status", "render_queue"):
        try:
            return {"ok": True, "render_queue": _premiere_tool("get_render_queue_status", {}, timeout=30.0)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # Generic pass-through: method IS a real MCP tool name
    try:
        d = _premiere_tool(method, args, timeout=90.0)
        return {"ok": bool(d.get("success", d.get("ok", True))), "result": d}
    except Exception as e:
        return {"ok": False, "error": f"premiere_pro: unknown method '{method}' or call failed: {e}"}


def _call_api_handle(args: dict) -> dict:
    """call_api — generic JSON-RPC pass-through to the Premiere MCP gateway."""
    method = args.get("method") or args.get("name") or ""
    params = args.get("params") or args.get("arguments") or {}
    if not method:
        return {"ok": False, "error": "call_api needs method (MCP tool name)"}
    try:
        d = _premiere_tool(str(method), dict(params) if isinstance(params, dict) else {}, timeout=90.0)
        return {"ok": bool(d.get("success", d.get("ok", True))), "result": d}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ============================================================
# COMFYUI WAN 2.2 GENERATION (local GPU :8188)
# ============================================================

# ============================================================
# VRAM HANDOFF — 16GB card cannot hold Wan 5B (10GB) + Jhanna (9.8GB)
# ============================================================

def _ollama_unload_all():
    """Evict all loaded Ollama models so ComfyUI can load (Wan needs ~10GB)."""
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=5) as r:
            ps = json.loads(r.read().decode("utf-8", "replace"))
        for m in ps.get("models") or []:
            name = m.get("name")
            if not name:
                continue
            try:
                req = urllib.request.Request(
                    "http://127.0.0.1:11434/api/generate",
                    data=json.dumps({"model": name, "keep_alive": 0}).encode(),
                    headers={"Content-Type": "application/json"},
                )
                urllib.request.urlopen(req, timeout=20)
            except Exception:
                pass
    except Exception:
        pass


def _comfyui_unload():
    """Unload the Wan transformer from VRAM after generation (free for Jhanna)."""
    try:
        req = urllib.request.Request(
            f"{COMFYUI_URL}/free",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=20)
    except Exception:
        pass


def _comfyui_post(payload: dict, timeout: float = 60.0) -> dict:
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _comfyui_wait(prompt_id: str, timeout: float = 900.0) -> dict:
    import time
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10) as r:
                hist = json.loads(r.read().decode("utf-8", "replace"))
            entry = (hist or {}).get(prompt_id)
            if entry and entry.get("outputs"):
                return entry
        except Exception:
            pass
        time.sleep(2.0)
    return {}


def _comfyui_latest_output(prefix: str) -> Optional[Path]:
    try:
        hits = sorted(COMFYUI_OUT.glob(f"{prefix}*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if hits:
            return hits[0]
    except Exception:
        pass
    return None


def _comfyui_generate_handle(args: dict) -> dict:
    """Generate a video clip with Wan 2.2 (text-to-video, 480p turbo).

    Args (model-friendly):
      prompt / text / positive_prompt — scene description
      negative_prompt — optional
      width / height / num_frames / steps / cfg / seed — optional overrides
      filename_prefix — output prefix (default 'oroboros_scene')
    """
    prompt = args.get("prompt") or args.get("text") or args.get("positive_prompt") or ""
    if not prompt:
        return {"ok": False, "error": "comfyui_generate needs prompt (scene description)"}
    negative = args.get("negative_prompt") or ""
    width = int(args.get("width") or 832)
    height = int(args.get("height") or 480)
    frames = int(args.get("num_frames") or args.get("frames") or 33)
    steps = int(args.get("steps") or 12)
    cfg = float(args.get("cfg") or 1.0)
    seed = int(args.get("seed") or 0)
    prefix = args.get("filename_prefix") or "oroboros_scene"

    workflow = {
        "1": {
            "class_type": "WanVideoModelLoader",
            "inputs": {"model": COMFYUI_MODEL, "base_precision": "bf16",
                       "quantization": "disabled", "load_device": "offload_device"},
        },
        "2": {
            "class_type": "WanVideoVAELoader",
            "inputs": {"model_name": COMFYUI_VAE, "precision": "bf16"},
        },
        "3": {
            "class_type": "LoadWanVideoT5TextEncoder",
            "inputs": {"model_name": COMFYUI_T5, "precision": "bf16"},
        },
        "4": {
            "class_type": "WanVideoTextEncode",
            "inputs": {"positive_prompt": prompt, "negative_prompt": negative,
                       "t5": ["3", 0], "force_offload": True},
        },
        "5": {
            "class_type": "WanVideoEmptyEmbeds",
            "inputs": {"width": width, "height": height, "num_frames": frames},
        },
        "6": {
            "class_type": "WanVideoSampler",
            "inputs": {"model": ["1", 0], "image_embeds": ["5", 0],
                       "text_embeds": ["4", 0],
                       "steps": steps, "cfg": cfg, "shift": 5.0, "seed": seed,
                       "force_offload": False, "scheduler": "unipc", "riflex_freq_index": 0},
        },
        "7": {
            "class_type": "WanVideoDecode",
            "inputs": {"vae": ["2", 0], "samples": ["6", 0],
                       "enable_vae_tiling": False, "tile_x": 272, "tile_y": 272,
                       "tile_stride_x": 144, "tile_stride_y": 128},
        },
        "7b": {
            "class_type": "CreateVideo",
            "inputs": {"images": ["7", 0], "fps": 16.0},
        },
        "8": {
            "class_type": "SaveVideo",
            "inputs": {"video": ["7b", 0], "filename_prefix": prefix, "format": "mp4"},
        },
    }
    try:
        _ollama_unload_all()
        resp = _comfyui_post({"prompt": workflow}, timeout=30.0)
        pid = resp.get("prompt_id")
        if not pid:
            return {"ok": False, "error": f"ComfyUI rejected prompt: {resp}"}
        entry = _comfyui_wait(pid, timeout=900.0)
        outputs = (entry.get("outputs") or {}) if entry else {}
        if not outputs:
            return {"ok": False, "error": "ComfyUI generation timed out (no output)", "prompt_id": pid}
        out = _comfyui_latest_output(prefix)
        _comfyui_unload()
        return {
            "ok": True,
            "prompt_id": pid,
            "output_path": str(out) if out else None,
            "engine": "comfyui_wan2.2_t2v_480p_turbo",
            "width": width, "height": height, "frames": frames,
        }
    except Exception as e:
        return {"ok": False, "error": f"comfyui_generate failed: {e}"}


def _pillow_text_overlay_handle(args: dict) -> dict:
    """Generate a text overlay PNG (brand fonts) — no Premiere needed."""
    text = args.get("text") or args.get("content") or ""
    if not text:
        return {"ok": False, "error": "pillow_text_overlay needs text"}
    try:
        png = _generate_text_overlay_png(
            text,
            font_size=int(args.get("font_size") or 72),
            color=tuple(args.get("color") or (255, 255, 255, 255)),
        )
        return {"ok": True, "path": str(png), "engine": "pillow", "text": text}
    except Exception as e:
        return {"ok": False, "error": f"pillow_text_overlay failed: {e}"}


def execute_host_tool(
    tool: str,
    args: Optional[dict] = None,
    *,
    source: str = "unknown",
) -> dict:
    """Execute a host tool through the shared CLI ToolRegistry."""
    global _event_count
    name = alias_tool(tool)
    args = args or {}
    tools = get_shared_tools()
    raw = tools.execute(name, args)
    _event_count += 1

    if isinstance(raw, dict):
        out = dict(raw)
    else:
        out = {"ok": True, "result": raw}

    out.setdefault("tool", name)
    out["host"] = True
    out["sandbox"] = False
    out["backend"] = "claude_o_cli.host_tool_bridge"
    out["source"] = source
    out["connected_surfaces"] = ["terminal_cli", "html_cli_ui", "local_chat"]

    _log_event({
        "at": _now(),
        "source": source,
        "tool": name,
        "args_keys": sorted(list(args.keys())),
        "ok": out.get("ok", "error" not in out),
        "path": args.get("path"),
    })
    return out


def execute_production_tool(
    tool: str,
    args: Optional[dict] = None,
    *,
    source: str = "unknown",
) -> dict:
    """Execute a production tool (premiere_pro / call_api) against the live
    Premiere MCP gateway. Falls back to the shared registry for unknown tools."""
    global _event_count
    name = (tool or "").strip()
    args = args or {}
    _event_count += 1

    if name == "premiere_pro":
        method = args.get("method") or args.get("tool") or args.get("name") or ""
        out = _premiere_handle(str(method), args)
    elif name == "call_api":
        out = _call_api_handle(args)
    elif name == "comfyui_generate":
        out = _comfyui_generate_handle(args)
    elif name == "pillow_text_overlay":
        out = _pillow_text_overlay_handle(args)
    else:
        return execute_host_tool(name, args, source=source)

    out.setdefault("tool", name)
    out["host"] = True
    out["sandbox"] = False
    out["backend"] = "claude_o_cli.host_tool_bridge"
    out["source"] = source
    out["connected_surfaces"] = ["terminal_cli", "html_cli_ui", "local_chat"]

    _log_event({
        "at": _now(),
        "source": source,
        "tool": name,
        "args_keys": sorted(list(args.keys())),
        "ok": out.get("ok", "error" not in out),
        "path": args.get("path"),
    })
    return out


def execute_payload(payload: dict, *, source: str = "unknown") -> dict:
    """Accept Express-sketch or CLI shapes."""
    if not isinstance(payload, dict):
        return {"ok": False, "error": "payload must be an object"}
    cmd = payload
    if isinstance(payload.get("message"), dict) and payload["message"].get("tool"):
        cmd = payload["message"]
    tool = cmd.get("tool") or payload.get("tool")
    args = cmd.get("args") or cmd.get("params") or payload.get("args") or payload.get("params") or {}
    if not tool:
        return {
            "ok": False,
            "error": 'Missing tool. Expected {"tool":"write_file","args":{...}}',
        }
    name = str(tool)
    if name in ("premiere_pro", "call_api", "comfyui_generate", "pillow_text_overlay"):
        return execute_production_tool(name, dict(args) if isinstance(args, dict) else {}, source=source)
    # Model-friendly aliases → premiere_pro methods
    premiere_aliases = {
        "premiere_import_media": "import_media",
        "premiere_import": "import_media",
        "premiere_add_transition": "add_transition",
        "premiere_transition": "add_transition",
        "premiere_apply_lut": "apply_lut",
        "premiere_lut": "apply_lut",
        "premiere_export_sequence": "export_sequence",
        "premiere_export": "export_sequence",
        "premiere_add_text_overlay": "add_text_overlay",
        "premiere_text_overlay": "add_text_overlay",
        "premiere_create_sequence": "create_sequence",
        "premiere_verify": "verify_premiere_connection",
        "premiere_verify_connection": "verify_premiere_connection",
        "premiere_list_sequences": "list_sequences",
        "premiere_add_to_timeline": "add_to_timeline",
    }
    if name in premiere_aliases:
        merged = dict(args)
        merged.setdefault("method", premiere_aliases[name])
        return execute_production_tool("premiere_pro", merged, source=source)
    return execute_host_tool(name, dict(args) if isinstance(args, dict) else {}, source=source)


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Shared Oroboros host tool bridge (CLI canonical)")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--tool", type=str, default="")
    parser.add_argument("--args", type=str, default="{}")
    parser.add_argument("--source", type=str, default="cli_argv")
    parser.add_argument("--stdin", action="store_true", help="Read JSON payload from stdin")
    parser.add_argument("--file", type=str, default="", help="Read JSON payload from a file")
    args = parser.parse_args(argv)

    if args.status:
        print(json.dumps(status(source=args.source), indent=2))
        return 0

    if args.file:
        payload = json.loads(Path(args.file).read_text(encoding="utf-8"))
        print(json.dumps(execute_payload(payload, source=args.source), indent=2, default=str))
        return 0

    if args.stdin:
        payload = json.loads(sys.stdin.read() or "{}")
        print(json.dumps(execute_payload(payload, source=args.source), indent=2, default=str))
        return 0

    if not args.tool:
        parser.error("provide --tool, --stdin, --file, or --status")
    tool_args = json.loads(args.args or "{}")
    print(json.dumps(execute_host_tool(args.tool, tool_args, source=args.source), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
