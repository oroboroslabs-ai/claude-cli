#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MEDIA GEN BRIDGE — the FLUX + WAN hands for the models (the Architect's
custom builds).

- FLUX.2-dev (the Architect's fused Qwen-Wan line, single-file 32B transformer
  at Q:\\FLUX-2-dev via ComfyUI :8188) — `flux_generate`
- WAN video (Oroboros Meta-Nexus :8920 /api/video/generate) — `wan_generate`

Both queue real jobs and return ids; poll with `*_status`. Builds are marked
OROBOROS CUSTOM — fused towers, not stock.
"""
from __future__ import annotations

import json
import time
import urllib.request

COMFY = "http://127.0.0.1:8188"
VIDEO_NEXUS = "http://127.0.0.1:8920"
FLUX_UNET = "flux2-dev.safetensors"
FLUX_VAE = "ae.safetensors"
FLUX_CLIP = "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"

COMFY_OUTPUT = r"Q:\ComfyUI\output"
VAULT = r"J:\Assimilation Architecture Null Frame\nullframe\vault\teardowns"
UA_JSON = {"Content-Type": "application/json"}
CUSTOM_BUILDS = (
    "oroboros custom builds — the Architect's fused towers: flux2-dev 32B "
    "(single-file Q:\\FLUX-2-dev) + the qwen-wan video nexus :8920"
)


def _write_media_capture(kind: str, target: str, files: list, meta: dict | None = None) -> str | None:
    """Register a finished render into the nullframe vault as a capture the
    TEARDOWN card displays (same shape as probe-*.json: screenshots_jpeg_b64)."""
    try:
        import base64, glob, os
        os.makedirs(VAULT, exist_ok=True)
        b64s = []
        for f in files[:3]:
            p = str(f)
            if not os.path.isabs(p):
                p = os.path.join(COMFY_OUTPUT, f)
            if os.path.exists(p):
                with open(p, "rb") as fh:
                    b64s.append(base64.b64encode(fh.read()).decode("ascii"))
        ts = time.strftime("%Y%m%d-%H%M%S")
        path = os.path.join(VAULT, f"media-{kind}-{ts}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({
                "target": f"{kind}:// {target}"[:300],
                "title": f"{kind.upper()} render — the Architect's fused build",
                "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "screenshots_jpeg_b64": b64s,
                "graphics_files": [str(f) for f in files[:12]],
                "stack_signals": [meta or {}, ],
                "network": {"summary": {"count": len(files), "bytes_mb": 0}},
                "build": CUSTOM_BUILDS,
                "via": f"{kind}_generate → the media hands",
            }, fh)
        return path
    except Exception:
        return None


def _post(url: str, payload: dict, timeout: int = 60) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _get(url: str, timeout: int = 30) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _flux_graph(prompt: str, width: int, height: int, steps: int, seed: int, guidance: float) -> dict:
    """The canonical local FLUX.2-dev graph (128-ch latent + flux2 scheduler)."""
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": FLUX_UNET, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": FLUX_CLIP, "type": "flux2"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": FLUX_VAE}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": prompt}},
        "5": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["4", 0], "guidance": guidance}},
        "6": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "7": {"class_type": "Flux2Scheduler", "inputs": {"steps": steps, "width": width, "height": height}},
        "8": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "9": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "10": {"class_type": "BasicGuider", "inputs": {"model": ["1", 0], "conditioning": ["5", 0]}},
        "11": {"class_type": "SamplerCustomAdvanced", "inputs": {
            "noise": ["9", 0], "guider": ["10", 0], "sampler": ["8", 0],
            "sigmas": ["7", 0], "latent_image": ["6", 0]}},
        "12": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["3", 0]}},
        "13": {"class_type": "SaveImage", "inputs": {"images": ["12", 0], "filename_prefix": "OroborosFlux"}},
    }


def tool_flux_generate(args: dict) -> dict:
    """Queue a FLUX.2-dev render in ComfyUI. args: prompt, width?, height?, steps?, seed?, guidance?"""
    prompt = str(args.get("prompt") or args.get("q") or "").strip()
    if not prompt:
        return {"ok": False, "tool": "flux_generate", "error": "prompt required",
                "build": CUSTOM_BUILDS}
    width = int(args.get("width") or 1024) & ~15
    height = int(args.get("height") or 1024) & ~15
    steps = int(args.get("steps") or 20)
    seed = int(args.get("seed") if args.get("seed") is not None else time.time())
    guidance = float(args.get("guidance") or 4.0)
    graph = _flux_graph(prompt, width, height, steps, seed, guidance)
    try:
        out = _post(COMFY + "/prompt", {"prompt": graph, "client_id": "oroboros_flux_hands"})
        pid = out.get("prompt_id")
        return {"ok": True, "tool": "flux_generate", "prompt_id": pid,
                "queued": True, "build": CUSTOM_BUILDS,
                "note": "IF a render errors with mat1/mat2 matmul mismatches: the flux2 text tower (6144-dim, in Q:\\\\FLUX-2-dev\\\\text_encoder diffusers shards) needs one conversion to a single text_encoder safetensors in ComfyUI\\\\models\\\\text_encoders — one-time fix. poll with flux_status {\"prompt_id\":\"" + str(pid) + "\"}; "
                        "rendering 32B transformer — big steps are slow on the 16GB card",
                "params": {"w": width, "h": height, "steps": steps, "seed": seed, "guidance": guidance}}
    except Exception as e:
        return {"ok": False, "tool": "flux_generate", "error": str(e), "build": CUSTOM_BUILDS}


def tool_flux_status(args: dict) -> dict:
    """Poll a queued flux job. args: prompt_id. On completion the render is
    registered into the nullframe vault so the TEARDOWN card shows it."""
    pid = str(args.get("prompt_id") or "").strip()
    if not pid:
        return {"ok": False, "tool": "flux_status", "error": "prompt_id required"}
    try:
        hist = _get(COMFY + "/history/" + pid)
        item = hist.get(pid)
        if not item:
            q = _get(COMFY + "/queue")
            running = any(e[1] == pid for e in q.get("queue_running", []))
            return {"ok": True, "tool": "flux_status", "state": "running" if running else "queued",
                    "prompt_id": pid}
        outs = item.get("outputs", {})
        files = []
        for node_out in outs.values():
            for img in node_out.get("images", []):
                files.append(img.get("filename"))
        status = (item.get("status") or {})
        st = status.get("status_str", "done")
        result = {"ok": True, "tool": "flux_status", "state": st,
                  "completed": bool(status.get("completed")),
                  "files": files,
                  "dir": COMFY_OUTPUT,
                  "prompt_id": pid}
        if st == "done" and files:
            prompt_txt = ""
            try:
                for n in (item.get("prompt") or [None, None])[2] or {}:
                    inp = (item["prompt"][2][n] or {})
                    if inp.get("class_type") == "CLIPTextEncode":
                        prompt_txt = (inp.get("inputs") or {}).get("text", "")[:200]
            except Exception:
                pass
            cap = _write_media_capture("flux", prompt_txt or pid, files)
            if cap:
                result["teardown_card"] = "registered — the TEARDOWN panel now shows this render"
        return result
    except Exception as e:
        return {"ok": False, "tool": "flux_status", "error": str(e)}


def tool_wan_generate(args: dict) -> dict:
    """Queue a WAN video render via the Oroboros Meta-Nexus (:8920).
    args: prompt, mode?, duration_seconds?, fps?, title? save_as?"""
    prompt = str(args.get("prompt") or args.get("script") or "").strip()
    if not prompt:
        return {"ok": False, "tool": "wan_generate", "error": "prompt required",
                "build": CUSTOM_BUILDS}
    body = {
        "prompt": prompt,
        "mode": args.get("mode"),
        "duration_seconds": int(args.get("duration_seconds") or 4),
        "fps": int(args.get("fps") or 24),
        "title": str(args.get("title") or "Oroboros / Anthropic"),
        "save_as": args.get("save_as"),
        "prefer_gpu": bool(args.get("prefer_gpu", True)),
    }
    try:
        r = _post(VIDEO_NEXUS + "/api/video/generate", body, timeout=60)
        return {"ok": True, "tool": "wan_generate", "queued": True,
                "build": CUSTOM_BUILDS,
                "nexus_response": r, "poll": "re-run with the same args to read status; "
                                             "the nexus streams the render queue"}
    except Exception as e:
        return {"ok": False, "tool": "wan_generate", "error": str(e),
                "hint": "the nexus is at :8920 /api/video/generate",
                "build": CUSTOM_BUILDS}


def tool_wan_status(args: dict) -> dict:
    """The Meta-Nexus render queue state."""
    try:
        s = _get(VIDEO_NEXUS + "/api/status", timeout=25); s["_capture"] = True
        return {"ok": True, "tool": "wan_status", "nexus": s}
    except Exception as e:
        return {"ok": False, "tool": "wan_status", "error": str(e)}


def register_media_gen_tools(registry) -> list:
    """Attach the FLUX + WAN hands to a ToolRegistry instance."""
    from claude_o_cli.oroboros_core import Tool
    tools = [
        ("flux_generate", "Render an image with the Architect's custom FLUX.2-dev 32B (ComfyUI :8188). args: prompt, width?, height?, steps?, seed?", tool_flux_generate, False),
        ("flux_status", "Poll a flux render. args: prompt_id", tool_flux_status, False),
        ("wan_generate", "Render a video with the Architect's custom WAN nexus (:8920). args: prompt, duration_seconds?", tool_wan_generate, False),
        ("wan_status", "The WAN nexus queue state.", tool_wan_status, False),
    ]
    names = []
    for name, desc, handler, perm in tools:
        if name not in registry.tools:
            registry.register(Tool(name, desc, handler, perm))
        names.append(name)
    return names
