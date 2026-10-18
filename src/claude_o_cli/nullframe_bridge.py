#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NULL FRAME BRIDGE — REA (reverse-engineer-assimilate) tools for the host registry.

Wires the Assimilation Architecture null-frame node (127.0.0.1:8090) directly
into the shared ToolRegistry so any model on any surface can run the full
pipeline: research → assimilate → read → brief → rebuild.
"""
from __future__ import annotations

import json
import glob
import os
import re
import urllib.request
from typing import Any, Dict, List

NODE = "http://127.0.0.1:8090"
VAULT_DIR = r"J:\Assimilation Architecture Null Frame\nullframe\vault\teardowns"
UA = {"Content-Type": "application/json"}


def _post(path: str, payload: dict, timeout: int = 300) -> dict:
    req = urllib.request.Request(
        NODE + path,
        data=json.dumps(payload).encode("utf-8"),
        headers=UA,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _get(path: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(NODE + path, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _vault_file(report: str) -> str:
    cand = str(report or "").strip()
    if cand and os.path.isabs(cand) and os.path.exists(cand):
        return cand
    files = sorted(glob.glob(os.path.join(VAULT_DIR, "*")))
    if cand:
        for f in files:
            if os.path.basename(f) == cand or os.path.basename(f).startswith(cand):
                return f
        # fuzzy: first file containing the fragment
        for f in files:
            if cand.lower() in os.path.basename(f).lower():
                return f
    return files[-1] if files else ""


def nf_vault(args: dict) -> dict:
    try:
        vault = _get("/vault")
        reports = vault.get("reports") or []
        return {"ok": True, "tool": "nullframe_vault", "vault_dir": VAULT_DIR,
                "count": len(reports), "reports": reports[-40:]}
    except Exception as e:
        return {"ok": False, "error": str(e), "tool": "nullframe_vault"}


def nf_assimilate(args: dict) -> dict:
    target = str(args.get("target") or args.get("path") or args.get("dir") or "").strip()
    if not target:
        return {"ok": False, "error": "target required (local directory or .asar)", "tool": "nullframe_assimilate"}
    name = str(args.get("name") or "")
    try:
        s = _post("/assimilate", {"target": target, "name": name}, timeout=600)
        return {"ok": bool(s.get("ok")), "tool": "nullframe_assimilate", **s}
    except Exception as e:
        return {"ok": False, "error": str(e), "tool": "nullframe_assimilate", "target": target}


def nf_read(args: dict) -> dict:
    report = str(args.get("report") or args.get("file") or "").strip()
    try:
        f = _vault_file(report)
        if not f:
            return {"ok": False, "error": "no teardown found in the vault", "tool": "nullframe_read"}
        with open(f, "r", encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
        result = data.get("result") or {}
        mods = result.get("modules") or []
        if isinstance(mods, list):
            mod_names = [m if isinstance(m, str) else (m.get("name") or m.get("id") or json.dumps(m)) for m in mods][:60]
        else:
            mod_names = []
        # REA in-toto statement: the real structure lives in normalized_result
        norm = result.get("normalized_result") or {}
        graph = norm.get("graph") or {}
        nodes = graph.get("nodes") or []
        artifacts = []
        for n in nodes:
            try:
                obs = (n.get("observations") or [{}])[0]
                label = obs.get("label") or n.get("kind") or "?"
                kind = n.get("kind") or "node"
                props = obs.get("properties") or {}
                if isinstance(props, dict) or isinstance(props, list):
                    p = obs.get("properties") or {}
                else:
                    p = {}
                    txt = str(props)
                    for key, pat in (("path", r"path=([^;}]+)"), ("file_kind", r"file_kind=([^;}]+)"), ("bytes", r"bytes=(\d+)")):
                        m = re.search(pat, txt)
                        if m:
                            p[key] = m.group(1).strip()
                if isinstance(p, dict) and p:
                    artifacts.append({
                        "label": str(label)[:120],
                        "kind": kind,
                        "path": str(p.get("path") or "")[:160],
                        "file_kind": str(p.get("file_kind") or ""),
                        "bytes": int(p.get("bytes") or 0),
                    })
            except Exception:
                continue
        stats = norm.get("statistics") or {}
        sem = norm.get("semantic_graph") or {}
        rels = {}
        if isinstance(sem, dict):
            for key in ("nodes", "relations", "unknowns", "fingerprints", "evidence_contexts"):
                v = sem.get(key)
                if isinstance(v, list):
                    rels[key] = len(v)
        return {
            "ok": True, "tool": "nullframe_read", "file": f,
            "target": data.get("target"), "generated": data.get("generated"),
            "modules": mod_names, "module_count": len(mods),
            "artifacts": artifacts[:60], "artifact_count": len(artifacts),
            "stats": stats, "semantic_counts": rels,
            "limitations": str(norm.get("limitations") or "")[:600],
            "imports_sample": (result.get("imports") or [])[:40] if isinstance(result.get("imports"), list) else [],
            "evidence_id": result.get("evidence_id"),
            "truncated_note": "full teardown json at the file path above",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "tool": "nullframe_read"}


def nf_brief(args: dict) -> dict:
    """Turn a teardown into a rebuild brief (same law as nullframe.mjs briefOf)."""
    report = str(args.get("report") or args.get("file") or "").strip()
    target_dir = str(args.get("dir") or args.get("target_dir") or "").strip()
    try:
        f = _vault_file(report)
        if not f:
            return {"ok": False, "error": "no teardown found in the vault", "tool": "nullframe_brief"}
        with open(f, "r", encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
        result = data.get("result") or {}
        mods = result.get("modules") if isinstance(result.get("modules"), list) else []
        lines = [
            f"# REBUILD BRIEF — {data.get('target')}",
            f"Source teardown: {data.get('generated')} by rea-agents. Vault: {f}",
            "",
            "STACK/EVIDENCE SUMMARY:",
        ]
        for m in (mods or [])[:40]:
            lines.append("- " + (m if isinstance(m, str) else (m.get("name") or m.get("id") or json.dumps(m))))
        if not mods:
            lines.append("- (modules listed in the vault json)")
        lines += [
            "",
            f"LAW (from the teardown): rebuild YOUR OWN implementation. Do not copy",
            f"proprietary assets or code wholesale; reconstruct behavior and structure you",
            f"observed and can justify, with your own code, in {target_dir or 'the target project directory'}.",
            "Evidence lives in the vault json (modules/imports/evidence fields).",
        ]
        out = f.replace(".json", "-brief.md")
        with open(out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
        return {"ok": True, "tool": "nullframe_brief", "brief": out,
                "target": data.get("target"), "modules": len(mods or [])}
    except Exception as e:
        return {"ok": False, "error": str(e), "tool": "nullframe_brief"}


def nf_compare(args: dict) -> dict:
    try:
        s = _post("/compare", {"a": args.get("a") or "", "b": args.get("b") or ""})
        return {"ok": bool(s.get("ok")), "tool": "nullframe_compare", **s}
    except Exception as e:
        return {"ok": False, "error": str(e), "tool": "nullframe_compare"}


def nf_probe(args: dict) -> dict:
    url = str(args.get("url") or args.get("target") or "").strip()
    if not url:
        return {"ok": False, "error": "url required", "tool": "nullframe_probe"}
    shots = int(args.get("shots") or 3)
    try:
        s = _post("/probe", {"url": url, "shots": shots}, timeout=300)
        summary = s.get("summary") or {}
        return {"ok": bool(s.get("ok")), "tool": "nullframe_probe", "url": url,
                "summary": summary, "teardown": s.get("teardown"), "report": s.get("report")}
    except Exception as e:
        return {"ok": False, "error": str(e), "tool": "nullframe_probe", "url": url}


def nf_ask(args: dict) -> dict:
    q = str(args.get("question") or args.get("query") or args.get("q") or "").strip()
    if not q:
        return {"ok": False, "error": "question required", "tool": "nullframe_ask"}
    try:
        s = _post("/query", {"question": q}, timeout=300)
        return {"ok": True, "tool": "nullframe_ask", "brain": "deepseek-prime-pcu:live",
                "answer": str(s.get("answer") or "")[:8000]}
    except Exception as e:
        return {"ok": False, "error": str(e), "tool": "nullframe_ask"}


def register_nullframe_tools(registry) -> List[str]:
    """Attach the REA pipeline tools to a ToolRegistry instance."""
    from claude_o_cli.oroboros_core import Tool

    tools = [
        ("nullframe_vault", "List REA teardowns in the null-frame vault", nf_vault, False),
        ("nullframe_assimilate", "REA: reverse-engineer a local dir/.asar into a vault teardown (args: target, name?)", nf_assimilate, False),
        ("nullframe_read", "Read one teardown: target, modules, imports, evidence (args: report)", nf_read, False),
        ("nullframe_brief", "Turn a teardown into a rebuild brief (args: report, dir?)", nf_brief, False),
        ("nullframe_compare", "Diff two vault teardowns (args: a, b)", nf_compare, False),
        ("nullframe_probe", "Live-probe a website: network + DOM + stack + screenshots (args: url, shots?)", nf_probe, False),
        ("nullframe_ask", "Ask the null-frame brain about any teardown/REA finding (args: question)", nf_ask, False),
    ]
    names = []
    for name, desc, handler, perm in tools:
        if name not in registry.tools:
            registry.register(Tool(name, desc, handler, perm))
        names.append(name)
    return names