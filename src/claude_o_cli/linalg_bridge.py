#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LINEAR ALGEBRA BRIDGE — a real linalg tool on the shared ToolRegistry.

Numbers for the physics lab and the REA briefs: determinant, inverse, rank,
eigen, SVD, solve, matmul — numpy-backed. The models reach it like any host
tool: {"tool":"linalg","args":{"op":"solve","a":[[3,1],[1,2]],"b":[9,8]}}.
"""
from __future__ import annotations

import numpy as np

_OPS = ("det", "inv", "rank", "eigen", "svd", "solve", "matmul", "norm")


def _mat(x) -> "np.ndarray | None":
    try:
        m = np.array(x, dtype=float)
        if m.ndim == 1:
            m = m.reshape(1, -1)
        if m.ndim not in (1, 2):
            return None
        return m
    except Exception:
        return None


def _list(m) -> list:
    return np.asarray(m).tolist()


def tool_linalg(args: dict) -> dict:
    """Compute one linear-algebra operation."""
    a = _mat(args.get("a"))
    b = _mat(args.get("b"))
    op = str(args.get("op") or "").strip().lower()
    out: dict = {"ok": False, "tool": "linalg", "op": op,
                 "backend": "numpy " + np.__version__}
    if a is None and op not in ("norm",):
        out["error"] = "matrix 'a' malformed (use nested lists [[..],[..]])"
        return out
    try:
        if op == "det":
            out["ok"] = True; out["det"] = float(np.linalg.det(a))
        elif op == "inv":
            if a.ndim != 2 or a.shape[0] != a.shape[1]:
                out["error"] = "inv needs a square matrix"
            else:
                out["ok"] = True; out["inv"] = _list(np.linalg.inv(a))
        elif op == "rank":
            out["ok"] = True; out["rank"] = int(np.linalg.matrix_rank(a))
        elif op == "eigen":
            if a.ndim != 2 or a.shape[0] != a.shape[1]:
                out["error"] = "eigen needs a square matrix"
            else:
                w, v = np.linalg.eig(a)
                out["ok"] = True
                out["eigenvalues"] = _list(w)
                out["eigenvectors"] = _list(v)
        elif op == "svd":
            u, s, vh = np.linalg.svd(a)
            out["ok"] = True
            out["singular_values"] = _list(s)
            out["U"] = _list(u); out["Vh"] = _list(vh)
        elif op == "solve":
            if b is None:
                out["error"] = "solve needs right-hand side 'b' (vector or matrix)"
            else:
                flat = b.reshape(-1) if b.size == a.shape[0] else b
                x = np.linalg.solve(a, flat)
                out["ok"] = True; out["x"] = _list(x)
        elif op == "matmul":
            if b is None:
                out["error"] = "matmul needs 'b'"
            elif a.shape[1] != b.shape[0]:
                out["error"] = f"shape mismatch {a.shape} × {b.shape}"
            else:
                out["ok"] = True; out["product"] = _list(a @ b)
        elif op == "norm":
            v = np.array(args.get("a") or 0.0, dtype=float).reshape(-1)
            out["ok"] = True
            out["norm"] = float(np.linalg.norm(v)) if v.size else 0.0
        else:
            out["error"] = "op must be one of: " + ", ".join(_OPS)
    except Exception as e:
        out["error"] = str(e)
    return out


def register_linalg_tools(registry) -> list:
    """Attach the linalg tool to a ToolRegistry instance."""
    from claude_o_cli.oroboros_core import Tool
    name = "linalg"
    if name not in registry.tools:
        registry.register(Tool(name, "Linear algebra (numpy): det|inv|rank|eigen|svd|solve|matmul|norm — args: op, a, b", tool_linalg, False))
    return [name]