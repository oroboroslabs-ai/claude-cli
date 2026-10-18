from __future__ import annotations

import os
import shutil
import subprocess

ORCA_CLI_SCHEMA = {
    "type": "object",
    "properties": {
        "argv": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "description": "Orca CLI arguments, for example [\"status\", \"--json\"].",
        },
        "timeout_ms": {
            "type": "integer",
            "minimum": 1000,
            "maximum": 60000,
            "default": 30000,
        },
    },
    "required": ["argv"],
}


def run_orca_cli(args: dict) -> dict:
    argv = args.get("argv")
    if argv is None or (isinstance(argv, list) and len(argv) == 0):
        # No argv given: return the full Orca command schema + status so the
        # caller learns how to use the tool instead of getting a hard error.
        argv = ["agent-context", "--json"]
    if not isinstance(argv, list) or not all(isinstance(item, str) for item in argv):
        return {"error": "orca_cli requires argv as an array of strings"} 
    if len(argv) > 64 or sum(len(item) for item in argv) > 32768:
        return {"error": "orca_cli argv exceeds the supported size"}

    try:
        timeout_ms = int(args.get("timeout_ms", 30000))
    except (TypeError, ValueError):
        return {"error": "timeout_ms must be an integer"}
    if not 1000 <= timeout_ms <= 60000:
        return {"error": "timeout_ms must be between 1000 and 60000"}

    command = os.environ.get("ORCA_CLI_COMMAND") or shutil.which("orca")
    if not command:
        return {"error": "Orca CLI was not found on PATH"}

    try:
        result = subprocess.run(
            [command, *argv],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_ms / 1000,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return {"error": f"Orca CLI timed out after {timeout_ms} ms"}
    except OSError as exc:
        return {"error": f"Could not start Orca CLI: {exc}"}

    stdout = result.stdout or ""
    stderr = result.stderr or ""
    return {
        "exit_code": result.returncode,
        "stdout": stdout[-50000:],
        "stderr": stderr[-10000:],
        "truncated": len(stdout) > 50000 or len(stderr) > 10000,
    }
