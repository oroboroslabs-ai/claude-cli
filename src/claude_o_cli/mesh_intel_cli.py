"""CLI entry for mesh intel — used by serve-local.ps1 /api/mesh/*."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from claude_o_cli.mesh_intel import (
    probe_haki,
    probe_mesh,
    tool_mesh_status,
    tool_q3_route,
    tool_q5_query,
    tool_q6_query,
    tool_spy_network,
    tool_tor_connect,
    tool_tor_status,
    tool_worldfeed_live,
)


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--status", action="store_true")
    p.add_argument("--file", type=str, default="")
    p.add_argument("--tool", type=str, default="")
    p.add_argument("--query", type=str, default="")
    args = p.parse_args(argv)

    if args.status:
        print(json.dumps(probe_mesh(persist=True), indent=2, default=str))
        return 0

    payload = {}
    if args.file:
        payload = json.loads(Path(args.file).read_text(encoding="utf-8"))
    tool = (args.tool or payload.get("tool") or "mesh_status").strip()
    query = args.query or payload.get("query") or (payload.get("args") or {}).get("query") or ""
    tool_args = payload.get("args") if isinstance(payload.get("args"), dict) else {}
    if query and "query" not in tool_args:
        tool_args = {**tool_args, "query": query}

    if tool in ("q3_route", "q3", "route_q3"):
        out = tool_q3_route(tool_args)
    elif tool in ("q5_query", "q5"):
        out = tool_q5_query(tool_args)
    elif tool in ("q6_query", "q6"):
        out = tool_q6_query(tool_args)
    elif tool in ("worldfeed_live", "worldfeed", "wf", "worldfeed_context"):
        out = tool_worldfeed_live(tool_args)
    elif tool in ("tor_status", "tor"):
        out = tool_tor_status({})
    elif tool in ("tor_connect",):
        out = tool_tor_connect({})
    elif tool in ("spy_network", "spy"):
        out = tool_spy_network(tool_args if tool_args else {})
    elif tool in ("haki_status", "haki"):
        out = probe_haki()
    else:
        out = tool_mesh_status(tool_args if tool_args else {})
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
