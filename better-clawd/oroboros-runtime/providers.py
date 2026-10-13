#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLAUDE-CLI — PROVIDER LAYER (Ollama · HuggingFace · Anthropic)
===============================================================
Routes a chat request to the right backend:
  · ollama://<tag>            local Ollama (default, no key)
  · hf:<org>/<model>         HuggingFace Inference (needs HF_TOKEN)
  · anthropic:<model>        Anthropic API (DORMANT until a key is entered)

Rules kept deliberately simple and original-preserving:
  · every model is treated AS ITSELF — the caller's messages are passed through
    untouched; no persona is injected here.
  · Anthropic is dormant unless ANTHROPIC_API_KEY (or a caller-supplied key) is
    present. No key → clear "dormant" result, never a crash.
  · local + secure: no telemetry, no phone-home beyond the endpoint the user
    explicitly selects.

This is the single seam the rest of Claude-CLI calls. Swapping providers never
touches the UI or the model logic.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_BACKUP_URL = os.environ.get("OLLAMA_BACKUP_URL", "http://127.0.0.1:11435")
SHIM_URL = os.environ.get("CLI_SHIM_URL", "http://127.0.0.1:11499")
HF_URL = os.environ.get("HF_ROUTER_URL", "https://router.huggingface.co/v1/chat/completions")
ANTHROPIC_URL = os.environ.get("ANTHROPIC_URL", "https://api.anthropic.com/v1/messages")
ANTHROPIC_VERSION = "2023-06-01"


# ── provider detection ─────────────────────────────────────────────────────
def provider_of(model: str) -> str:
    m = (model or "").strip()
    low = m.lower()
    if low.startswith("anthropic:") or low.startswith("claude:") or low.startswith("claude-3") \
       or low.startswith("claude-4") or low.startswith("claude-opus") \
       or low.startswith("claude-sonnet") or low.startswith("claude-haiku"):
        return "anthropic"
    if low.startswith("hf:") or low.startswith("huggingface:"):
        return "huggingface"
    return "ollama"


def _bare(model: str) -> str:
    for p in ("anthropic:", "claude:", "hf:", "huggingface:", "ollama:"):
        if model.lower().startswith(p):
            return model[len(p):]
    return model


# ── Ollama ──────────────────────────────────────────────────────────────────
def ollama_chat(model: str, messages: List[Dict], system: str = "",
                options: Optional[Dict] = None, keep_alive: Any = 0,
                tools: Optional[List[Dict]] = None) -> Dict:
    if system:
        msgs = [{"role": "system", "content": system}] + messages
    else:
        msgs = messages
    payload = {
        "model": _bare(model),
        "messages": msgs,
        "stream": False,
        "options": options or {"num_ctx": 131072, "num_predict": 1024},
        "keep_alive": keep_alive,
    }
    if tools:
        payload["tools"] = tools
    last = None
    for base in (OLLAMA_URL, OLLAMA_BACKUP_URL):
        try:
            req = urllib.request.Request(
                f"{base}/api/chat",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=None) as resp:
                data = json.loads(resp.read().decode())
            # some models emit into message.thinking, not content — surface it
            msg = data.get("message", {}) or {}
            if not msg.get("content") and msg.get("thinking"):
                msg["content"] = msg["thinking"]
                data["message"] = msg
            if data.get("error"):
                last = data["error"]
                continue
            return data
        except Exception as e:  # noqa: BLE001
            last = e
    # fallback: load through the local bridge (different path, same Ollama)
    via = _shim_chat(model, msgs, payload)
    if via is not None:
        return via
    return {"error": f"ollama unreachable/load-failed: {last}"}


def _shim_chat(model: str, msgs: List[Dict], payload: Dict) -> Optional[Dict]:
    """Reload a model through the bridge (:11499) — an alternate path that
    translates and retries, for when a direct Ollama load errors out."""
    try:
        req = urllib.request.Request(
            f"{SHIM_URL}/v1/messages",
            data=json.dumps({
                "model": _bare(model), "max_tokens": payload["options"].get("num_predict", 1024),
                "messages": [m for m in msgs if m.get("role") != "system"],
                "system": "".join(m.get("content", "") for m in msgs if m.get("role") == "system"),
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=None) as resp:
            data = json.loads(resp.read().decode())
        text = ""
        for b in data.get("content", []):
            if isinstance(b, dict) and b.get("type") == "text":
                text += b.get("text", "")
            elif isinstance(b, dict) and b.get("type") == "tool_use":
                text = json.dumps({"name": b.get("name"), "arguments": b.get("input", {})})
        return {"message": {"role": "assistant", "content": text}}
    except Exception:
        return None


# ── HuggingFace (OpenAI-compatible router) ─────────────────────────────────
def hf_chat(model: str, messages: List[Dict], system: str = "",
            max_tokens: int = 1024, temperature: float = 0.7,
            api_key: Optional[str] = None) -> Dict:
    key = api_key or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
    if not key:
        return {"error": "HuggingFace token not set (set HF_TOKEN) — provider dormant"}
    msgs = ([{"role": "system", "content": system}] if system else []) + list(messages)
    payload = {"model": _bare(model), "messages": msgs,
               "max_tokens": max_tokens, "temperature": temperature, "stream": False}
    try:
        req = urllib.request.Request(
            HF_URL, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=180) as resp:
            return _normalize_openai(json.loads(resp.read().decode()))
    except urllib.error.HTTPError as e:
        return {"error": f"HF HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}"}
    except Exception as e:  # noqa: BLE001
        return {"error": f"HF error: {e}"}


# ── Anthropic (DORMANT unless a key is entered) ─────────────────────────────
def anthropic_chat(model: str, messages: List[Dict], system: str = "",
                   max_tokens: int = 1024, api_key: Optional[str] = None) -> Dict:
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return {"error": "anthropic dormant — no API key entered",
                "dormant": True, "provider": "anthropic"}
    # Anthropic wants system separate and only user/assistant in messages.
    sys_txt = system
    convo = []
    for m in messages:
        if m.get("role") == "system":
            sys_txt = (sys_txt + "\n" + m.get("content", "")).strip()
        else:
            convo.append({"role": m.get("role"), "content": m.get("content", "")})
    payload = {"model": _bare(model), "max_tokens": max_tokens, "messages": convo}
    if sys_txt:
        payload["system"] = sys_txt
    try:
        req = urllib.request.Request(
            ANTHROPIC_URL, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json",
                     "x-api-key": key,
                     "anthropic-version": ANTHROPIC_VERSION})
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode())
        text = "".join(b.get("text", "") for b in data.get("content", [])
                       if b.get("type") == "text")
        return {"message": {"role": "assistant", "content": text},
                "provider": "anthropic", "raw": data}
    except urllib.error.HTTPError as e:
        return {"error": f"anthropic HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}"}
    except Exception as e:  # noqa: BLE001
        return {"error": f"anthropic error: {e}"}


# ── unified entry ──────────────────────────────────────────────────────────
def chat(model: str, messages: List[Dict], system: str = "", **kw) -> Dict:
    """Route to the right provider. Returns an Ollama-shaped dict for the UI."""
    p = provider_of(model)
    if p == "anthropic":
        return anthropic_chat(model, messages, system,
                              api_key=kw.get("api_key"), max_tokens=kw.get("max_tokens", 1024))
    if p == "huggingface":
        return hf_chat(model, messages, system,
                       api_key=kw.get("api_key"), max_tokens=kw.get("max_tokens", 1024),
                       temperature=kw.get("temperature", 0.7))
    return ollama_chat(model, messages, system,
                       options=kw.get("options"), keep_alive=kw.get("keep_alive", 0))


def _normalize_openai(data: Dict) -> Dict:
    try:
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message", {})
        if "content" not in msg and choice.get("text"):
            msg = {"role": "assistant", "content": choice["text"]}
        return {"message": msg, "provider": "huggingface", "raw": data}
    except Exception:  # noqa: BLE001
        return data


def provider_status() -> Dict:
    return {
        "ollama": {"url": OLLAMA_URL, "configured": True},
        "huggingface": {"url": HF_URL,
                        "configured": bool(os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY"))},
        "anthropic": {"url": ANTHROPIC_URL, "dormant": not bool(os.environ.get("ANTHROPIC_API_KEY")),
                      "configured": bool(os.environ.get("ANTHROPIC_API_KEY"))},
    }
