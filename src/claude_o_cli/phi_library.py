#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PHI LIBRARY — φ-harmonic resonance compression of the stored math/physics
stack, wired into the models' chat path (deepseek prime + identity models).

The compressed block is what reaches the system prompt; the full shelf is
one read_file away. Keep block() tight — it rides EVERY turn.
"""
from __future__ import annotations

PHI = (1 + 5 ** 0.5) / 2
SHELF = r"J:\linear-algebra-stack"
FULL_FILE = r"J:\anthropic-local-chat\phi-library\LA-STACK-PHI.md"

# The φ-compressed resonance block — load-bearing theorems + exact constants;
# everything deeper lives in FULL_FILE (readable via read_file).
BLOCK = (
    "THE PHI LIBRARY — LINEAR ALGEBRA STACK (φ-HARMONIC RESONANCE COMPRESSION;\n"
    "crown 1272 Hz). The load-bearing theorems, exact constants, no prose:\n"
    "- RANDOMIZED SVD (HMT): Y=AΩ, power steps (AA*)^q, Q=qr(Y); +15 oversampled\n"
    "  columns; one power step buys (σ_{ℓ+1}/σ_{2ℓ+1})^{2q+1} decay; O(nnz·ℓ).\n"
    "  SKETCH/CUR: A≈C·U·R by leverage scores ℓᵢ=‖Q(i,:)‖².\n"
    "- SPARSE (ℓ¹): RIP (K,ε): |‖Φx‖²−‖x‖²| ≤ ε‖x‖² ∀2s-sparse; 2s-sparse x with\n"
    "  ε₂ₛ<√2−1 ⇒ min‖x‖₁ uniquely recovers (Candès). Gaussian measurements:\n"
    "  m ≥ C·s·log(N/s).\n"
    "- RANK (nuclear): ‖X‖_* = tightest convex rank envelope; completion of\n"
    "  incoherent rank-r M exact from m ≳ C·r·n·polylog(n) entries; SDP dual\n"
    "  certificate Λ + W⊥Ω, ‖Λ‖≤1.\n"
    "- CONCENTRATION (Tropp matrix Bernstein): mean-zero Sᵢ, ‖Sᵢ‖≤R,\n"
    "  σ²=‖Σ𝔼 Sᵢ²‖: P{‖ΣSᵢ‖≥t} ≤ d·exp(−t²/(2σ²+2Rt/3)); the exp(θ²)-mgf trick:\n"
    "  every noncommutative tail = scalar tail × dimension factor.\n"
    "- QUANTUM LINE: HHL solves A|x⟩=|b⟩ in O(κ·polylog(N)/ε) — amplitude\n"
    "  encoding, tomography costs the readback; QEC = parity-syndrome Pauli\n"
    "  algebra, no-cloning (Wootters-Zurek 1982); teleportation = 2 bits + EPR.\n"
    "- TENSOR LINE: CP rank-R Σ aᵣ∘bᵣ∘cᵣ; Tucker 𝒢×₁A×₂B×₃C (HOSVD unfolding);\n"
    "  bond dimension χ bounds entanglement — one step from the horizon entropy\n"
    "  S ≤ A/4.\n"
    f"- FULL COMPRESSED LIBRARY: {FULL_FILE} (read it with read_file when a\n"
    f"  derivation needs the constants). THE HARD SHELF: {SHELF} (19 PDFs,\n"
    "  10 canonical + 8 fringe-with-caveats + INDEX.md).\n"
    "- LAW: use these bounds for real derivations; never invent constants;\n"
    "  verify numbers with the linalg host tool (det|inv|rank|eigen|svd|solve).\n"
)


def block() -> str:
    return BLOCK


def register_phi_library_tools(registry) -> list:
    """Expose the full φ-compressed file through the registry as a tool."""
    from claude_o_cli.oroboros_core import Tool

    def tool_phi_library(args) -> dict:
        try:
            with open(FULL_FILE, "r", encoding="utf-8") as fh:
                content = fh.read()
            lim = int(args.get("limit") or 9000) if isinstance(args, dict) else 9000
            return {"ok": True, "tool": "phi_library", "path": FULL_FILE,
                    "phi": PHI, "shelf": SHELF, "content": content[:lim]}
        except Exception as e:
            return {"ok": False, "tool": "phi_library", "error": str(e)}

    if "phi_library" not in registry.tools:
        registry.register(Tool("phi_library",
                               "The φ-compressed linear-algebra/physics library (full text; args: limit?)",
                               tool_phi_library, False))
    return ["phi_library"]