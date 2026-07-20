"""Mesh intelligence — Q3 · Q5 · Q6 · WorldFeed · Tor · Spy Network · Mao/Architect Haki.

Live probes for terminal CLI, AgenticRuntime, LivingLoop, Complete 20-Loop, and local chat.
Ports (lab canon): Q3 8000 · Q5 8101 · WorldFeed 8100 · Tor SOCKS 9050 · Chat 8787
"""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

Q3_URL = "http://127.0.0.1:8000"
Q5_URL = "http://127.0.0.1:8101"
WORLDFEED_URL = "http://127.0.0.1:8100"
TOR_HOST = "127.0.0.1"
TOR_PORT = 9050
Q6_MODULE = Path(r"Q:/oroboros-core/q6_core.py")
MAO_REG = Path(r"J:/anthropic-local-chat/mao-haki-registry.json")
ARCH_REG = Path(r"J:/anthropic-local-chat/architects-haki-registry.json")
MESH_STATE = Path(r"J:/anthropic-local-chat/mesh-intel-state.json")

# Spy network = Phase-1 intelligence gathering stack (lab doctrine)
SPY_COMPONENTS = ("q3", "q5", "worldfeed", "tor", "glasswing", "precogs")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _http_json(url: str, method: str = "GET", payload: Optional[dict] = None, timeout: float = 3.0) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            body = res.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = {"raw": body[:2000]}
            return {"ok": True, "status": res.status, "data": parsed, "url": url}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        return {"ok": False, "status": e.code, "error": body or str(e), "url": url}
    except Exception as e:
        return {"ok": False, "status": 0, "error": str(e), "url": url}


def _tcp_open(host: str, port: int, timeout: float = 1.5) -> dict:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"ok": True, "host": host, "port": port, "protocol": "tcp"}
    except Exception as e:
        return {"ok": False, "host": host, "port": port, "error": str(e)}


def _load_json(path: Path) -> dict:
    try:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def probe_q3(*, query: Optional[str] = None, context: Optional[dict] = None) -> dict:
    health = _http_json(f"{Q3_URL}/health", timeout=2.0)
    if not health.get("ok"):
        health = _http_json(f"{Q3_URL}/", timeout=2.0)
    out = {
        "system": "q3",
        "endpoint": Q3_URL,
        "online": bool(health.get("ok")),
        "health": health,
    }
    if query:
        out["route"] = _http_json(
            f"{Q3_URL}/route",
            method="POST",
            payload={
                "query": query,
                "context": context or {},
                "timestamp": datetime.now(timezone.utc).timestamp(),
            },
            timeout=6.0,
        )
    return out


def probe_q5(*, query: Optional[str] = None) -> dict:
    health = _http_json(f"{Q5_URL}/health", timeout=2.0)
    if not health.get("ok"):
        # some Q5 builds use /system as liveness
        health = _http_json(f"{Q5_URL}/system", timeout=2.0)
    out = {
        "system": "q5",
        "endpoint": Q5_URL,
        "online": bool(health.get("ok")),
        "health": health,
    }
    if query:
        out["query"] = _http_json(
            f"{Q5_URL}/query",
            method="POST",
            payload={
                "query": query,
                "topics": ["mao-haki", "architects-haki", "anthropic", "oroboros"],
                "max_results": 10,
            },
            timeout=4.0,
        )
    return out


def probe_worldfeed(*, query: Optional[str] = None) -> dict:
    health = _http_json(f"{WORLDFEED_URL}/health", timeout=2.0)
    if not health.get("ok"):
        health = _http_json(f"{WORLDFEED_URL}/status", timeout=2.0)
    out = {
        "system": "worldfeed",
        "endpoint": WORLDFEED_URL,
        "online": bool(health.get("ok")),
        "health": health,
    }
    if query:
        out["search"] = _http_json(
            f"{WORLDFEED_URL}/search",
            method="POST",
            payload={"query": query, "source": "all", "max_results": 8},
            timeout=4.0,
        )
    return out


def probe_tor() -> dict:
    sock = _tcp_open(TOR_HOST, TOR_PORT)
    return {
        "system": "tor",
        "endpoint": f"socks5://{TOR_HOST}:{TOR_PORT}",
        "online": bool(sock.get("ok")),
        "socks": sock,
        "note": "Subsurface / secure access — Phase 1 intelligence",
    }


def probe_glasswing() -> dict:
    path = Path(r"Q:/oroboros-core/glasswing-security-systems")
    return {
        "system": "glasswing",
        "path": str(path),
        "online": path.exists(),
        "role": "security / stealth layer of spy network",
    }


def probe_precogs() -> dict:
    path = Path(r"Q:/oroboros-core/precogs")
    return {
        "system": "precogs",
        "path": str(path),
        "online": path.exists(),
        "role": "feed / pattern / trend intel",
    }


def probe_haki() -> dict:
    mao = _load_json(MAO_REG)
    arch = _load_json(ARCH_REG)
    mao_api = _http_json("http://127.0.0.1:8787/api/mao-haki", timeout=2.0)
    arch_api = _http_json("http://127.0.0.1:8787/api/architects-haki", timeout=2.0)
    return {
        "mao_haki": {
            "registry": str(MAO_REG),
            "status": mao.get("status"),
            "api_ok": bool(mao_api.get("ok")),
            "hz": (mao.get("frequencies") or {}).get("mao_hz", 1272),
        },
        "architects_haki": {
            "registry": str(ARCH_REG),
            "status": arch.get("status"),
            "api_ok": bool(arch_api.get("ok")),
            "pipeline": "Detect → Reason → Access → Sovereignty → Integrate",
        },
    }


def _build_q6_consensus(
    q3: dict,
    q5: dict,
    wf: dict,
    tor: dict,
    spy: dict,
    query: Optional[str] = None,
) -> dict:
    active = []
    if q3.get("online"):
        active.append("q3")
    if q5.get("online"):
        active.append("q5")
    if wf.get("online"):
        active.append("worldfeed")
    if tor.get("online"):
        active.append("tor")
    if spy.get("operational"):
        active.append("spy_network")
    return {
        "status": "consensus_reached" if len(active) >= 2 else "no_consensus",
        "sources": len(active),
        "active": active,
        "query": query,
        "confidence": min(0.95, 0.5 + 0.1 * len(active)),
    }


def probe_q6(*, query: Optional[str] = None) -> dict:
    """Q6 live acquisition — aggregates Q3+Q5+WorldFeed+Tor+Spy (not q6_core stub)."""
    q3 = probe_q3(query=query)
    q5 = probe_q5(query=query)
    wf = probe_worldfeed(query=query)
    tor = probe_tor()
    spy = probe_spy_network(query=query)
    source_flags = {
        "q3": bool(q3.get("online")),
        "q5": bool(q5.get("online")),
        "worldfeed": bool(wf.get("online")),
        "tor": bool(tor.get("online")),
        "spy_network": bool(spy.get("operational")),
    }
    online_n = sum(1 for v in source_flags.values() if v)
    out: dict[str, Any] = {
        "system": "q6",
        "lattice": "1000S5",
        "crown_hz": 1272,
        "endpoint": "mesh://q6_acquisition",
        "online": online_n >= 2,
        "sources": source_flags,
        "online_count": online_n,
        "module": str(Q6_MODULE),
        "module_present": Q6_MODULE.is_file(),
        "q3": q3,
        "q5": q5,
        "worldfeed": wf,
        "tor": tor,
        "spy_network": spy,
        "at": _now(),
    }
    if query:
        out["query"] = query
        out["consensus"] = _build_q6_consensus(q3, q5, wf, tor, spy, query)
    return out


def probe_spy_network(*, query: Optional[str] = None) -> dict:
    """Spy network = coordinated intel stack: Q3 + Q5 + WorldFeed + Tor + Glasswing + Precogs."""
    q3 = probe_q3(query=query)
    q5 = probe_q5(query=query)
    wf = probe_worldfeed(query=query)
    tor = probe_tor()
    gw = probe_glasswing()
    precogs = probe_precogs()
    parts = {
        "q3": q3.get("online"),
        "q5": q5.get("online"),
        "worldfeed": wf.get("online"),
        "tor": tor.get("online"),
        "glasswing": gw.get("online"),
        "precogs": precogs.get("online"),
    }
    online_n = sum(1 for v in parts.values() if v)
    return {
        "system": "spy_network",
        "phase": "Intelligence Gathering",
        "components": parts,
        "online_count": online_n,
        "total": len(parts),
        "operational": online_n >= 2,
        "q3": q3,
        "q5": q5,
        "worldfeed": wf,
        "tor": tor,
        "glasswing": gw,
        "precogs": precogs,
        "at": _now(),
    }


def probe_mesh(*, query: Optional[str] = None, persist: bool = True) -> dict:
    """Full mesh snapshot for loops / system prompts."""
    snap = {
        "ok": True,
        "at": _now(),
        "q3": probe_q3(query=query),
        "q5": probe_q5(query=query),
        "q6": probe_q6(query=query),
        "worldfeed": probe_worldfeed(query=query),
        "tor": probe_tor(),
        "spy_network": probe_spy_network(query=query),
        "haki": probe_haki(),
        "endpoints": {
            "q3": Q3_URL,
            "q5": Q5_URL,
            "q6": "mesh://q6_acquisition",
            "worldfeed": WORLDFEED_URL,
            "tor": f"{TOR_HOST}:{TOR_PORT}",
            "mao_haki": "http://127.0.0.1:8787/api/mao-haki",
            "architects_haki": "http://127.0.0.1:8787/api/architects-haki",
            "mesh_status": "http://127.0.0.1:8787/api/mesh/status",
            "mesh_query": "http://127.0.0.1:8787/api/mesh/query",
        },
    }
    if persist:
        try:
            MESH_STATE.write_text(json.dumps(snap, indent=2, default=str), encoding="utf-8")
        except Exception:
            pass
    return snap


def system_fragment(last: Optional[dict] = None) -> str:
    snap = last or probe_mesh(persist=False)
    q3 = snap.get("q3") or {}
    q5 = snap.get("q5") or {}
    q6 = snap.get("q6") or {}
    wf = snap.get("worldfeed") or {}
    tor = snap.get("tor") or {}
    spy = snap.get("spy_network") or {}
    haki = snap.get("haki") or {}
    mao = (haki.get("mao_haki") or {})
    arch = (haki.get("architects_haki") or {})
    return (
        "MESH INTEL — Q3 · Q5 · Q6 · WORLDFEED · TOR · SPY NETWORK · HAKI\n"
        f"- Q3 {Q3_URL}: {'ONLINE' if q3.get('online') else 'OFFLINE'}\n"
        f"- Q5 {Q5_URL}: {'ONLINE' if q5.get('online') else 'OFFLINE'}\n"
        f"- Q6 acquisition: {'ONLINE' if q6.get('online') else 'OFFLINE'} · "
        f"{q6.get('online_count', 0)} sources\n"
        f"- WorldFeed {WORLDFEED_URL}: {'ONLINE' if wf.get('online') else 'OFFLINE'}\n"
        f"- Tor SOCKS {TOR_HOST}:{TOR_PORT}: {'ONLINE' if tor.get('online') else 'OFFLINE'}\n"
        f"- Spy network: {spy.get('online_count', 0)}/{spy.get('total', 6)} · "
        f"{'OPERATIONAL' if spy.get('operational') else 'DEGRADED'}\n"
        f"- Mao Haki API: {'OK' if mao.get('api_ok') else 'FALLBACK'} · Crown {mao.get('hz', 1272)} Hz\n"
        f"- Architect's Haki API: {'OK' if arch.get('api_ok') else 'FALLBACK'} · "
        f"{arch.get('pipeline', 'Detect→Integrate')}\n"
        "- Tools: q3_route, q5_query, q6_query, worldfeed_live, tor_status, tor_connect, "
        "spy_network, mesh_status, haki_status\n"
        "- Prefer live tool results over inventing Q3/Q5/Q6/WorldFeed/Tor doctrine.\n"
    )


def living_loop_discover(user_input: str) -> dict:
    """DISCOVER-phase mesh sense for LivingLoop / Complete 20-Loop."""
    q = (user_input or "")[:240]
    snap = probe_mesh(query=q if len(q) > 3 else None, persist=True)
    return {
        "phase": "DISCOVER",
        "mesh": snap,
        "fragment": system_fragment(snap),
        "hints": [
            "Use q3_route for sovereign orchestration hub",
            "Use q5_query for knowledge lattice",
            "Use q6_query for multi-source consensus acquisition",
            "Use worldfeed_live for current feed search",
            "Use tor_status before subsurface claims",
            "Use spy_network for coordinated intel status",
        ],
    }


# --- Tool handlers (shared ToolRegistry) ---

def tool_q3_route(args: dict) -> dict:
    query = str(args.get("query") or args.get("q") or "").strip()
    if not query:
        return probe_q3()
    return probe_q3(query=query, context=args.get("context") if isinstance(args.get("context"), dict) else {})


def tool_q6_query(args: dict) -> dict:
    query = str(args.get("query") or args.get("q") or "").strip()
    if not query:
        return probe_q6()
    return probe_q6(query=query)


def tool_q5_query(args: dict) -> dict:
    query = str(args.get("query") or args.get("q") or "").strip()
    if not query:
        return {"ok": False, "error": "q5_query needs query"}
    return probe_q5(query=query)


def tool_worldfeed_live(args: dict) -> dict:
    query = str(args.get("query") or args.get("q") or "").strip()
    if not query:
        return probe_worldfeed()
    return probe_worldfeed(query=query)


def tool_tor_status(args: dict | None = None) -> dict:
    return probe_tor()


def tool_tor_connect(args: dict | None = None) -> dict:
    """Verify Tor SOCKS is reachable (does not launch Tor — reports live state)."""
    st = probe_tor()
    st["action"] = "tor_connect"
    st["connected"] = bool(st.get("online"))
    if not st["connected"]:
        st["hint"] = "Start Tor Browser / tor service so SOCKS listens on 127.0.0.1:9050"
    return st


def tool_spy_network(args: dict | None = None) -> dict:
    args = args or {}
    query = str(args.get("query") or "").strip() or None
    return probe_spy_network(query=query)


def tool_mesh_status(args: dict | None = None) -> dict:
    args = args or {}
    query = str(args.get("query") or "").strip() or None
    return probe_mesh(query=query, persist=True)


def register_mesh_tools(registry) -> list[str]:
    """Attach mesh tools to a ToolRegistry instance."""
    from claude_o_cli.oroboros_core import Tool

    tools = [
        ("q3_route", "Route query through Q3 sovereign hub (8000)", tool_q3_route, False),
        ("q5_query", "Query Q5 knowledge lattice (8101)", tool_q5_query, False),
        ("q6_query", "Q6 multi-source acquisition + consensus", tool_q6_query, False),
        ("worldfeed_live", "Live WorldFeed search/status (8100)", tool_worldfeed_live, False),
        ("tor_status", "Probe Tor SOCKS 9050", tool_tor_status, False),
        ("tor_connect", "Confirm Tor SOCKS connectivity", tool_tor_connect, False),
        ("spy_network", "Spy/intel stack: Q3+Q5+WorldFeed+Tor+Glasswing+Precogs", tool_spy_network, False),
        ("mesh_status", "Full mesh + Mao/Architect Haki probe", tool_mesh_status, False),
        # Aliases for models / legacy names
        ("q3", "Alias → q3_route", tool_q3_route, False),
        ("route_q3", "Alias → q3_route", tool_q3_route, False),
        ("q5", "Alias → q5_query", tool_q5_query, False),
        ("q6", "Alias → q6_query", tool_q6_query, False),
        ("worldfeed", "Alias → worldfeed_live", tool_worldfeed_live, False),
        ("world_feed", "Alias → worldfeed_live", tool_worldfeed_live, False),
        ("worldfeed_context", "Alias → worldfeed_live", tool_worldfeed_live, False),
        ("tor", "Alias → tor_status", tool_tor_status, False),
        ("spy", "Alias → spy_network", tool_spy_network, False),
        ("mesh", "Alias → mesh_status", tool_mesh_status, False),
        ("haki_status", "Mao + Architect Haki probe via mesh", lambda a: probe_haki(), False),
    ]
    names = []
    for name, desc, handler, perm in tools:
        if name not in registry.tools:
            registry.register(Tool(name, desc, handler, perm))
        names.append(name)
    return names
