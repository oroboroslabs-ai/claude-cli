import json, os, subprocess, re

cfg = os.path.expanduser(r"~\.claude-cli\.claude-cli.json")
d = json.load(open(cfg, encoding="utf-8"))

out = subprocess.run(["ollama", "list"], capture_output=True, text=True).stdout
tags = []
for line in out.splitlines()[1:]:
    parts = line.split()
    if parts:
        tags.append(parts[0])

undec = sorted({t for t in tags if "undecillion" in t.lower()})
deepseek = [t for t in tags if t.lower().startswith("deepseek-prime-cl-1q5duo5:compounded")]

def label(t):
    return t

options = []
for t in undec:
    options.append({"value": t, "label": t, "description": "Undecillion - local"})
for t in deepseek:
    options.append({"value": t, "label": "DeepSeek Prime (Compounded)", "description": "Local - 5 GB"})

d["additionalModelOptionsCache"] = options
d["availableModels"] = [o["value"] for o in options]
d["defaultModel"] = "oroboros-labs/claude-fable7-undecillion-sse:latest"

json.dump(d, open(cfg, "w", encoding="utf-8"), indent=2)
print("undecillion tags:", len(undec))
for t in undec:
    print("  ", t)
print("deepseek:", deepseek)
print("allowlist size:", len(d["availableModels"]))
