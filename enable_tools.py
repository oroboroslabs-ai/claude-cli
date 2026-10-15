import json, os
cfg = os.path.expanduser(r"~\.claude-cli\.claude-cli.json")
d = json.load(open(cfg, encoding="utf-8"))

# Let the model actually USE its tools without a prompt per call.
d["defaultMode"] = "bypassPermissions"
d["bypassPermissionsMode"] = True
d["enableAllProjectMcpServers"] = True

# Tool-capable local models must be selectable (the undecillion builds are
# chat-only and cannot emit tool calls; these can).
cache = d.get("additionalModelOptionsCache", [])
have = {o.get("value") for o in cache}
for val, label, desc in [
    ("llama3.2:latest", "llama3.2 (tools)", "Local - tool-calling capable"),
    ("qwen2.5:14b", "qwen2.5 14B (tools)", "Local - tool-calling capable"),
]:
    if val not in have:
        cache.insert(0, {"value": val, "label": label, "description": desc})
d["additionalModelOptionsCache"] = cache

# keep them allowed
allow = d.get("availableModels") or []
for val in ("llama3.2:latest", "qwen2.5:14b"):
    if val not in allow:
        allow.append(val)
d["availableModels"] = allow

# clear the earlier project-level empty allowlist so tools are not blocked
projs = d.get("projects", {})
for p in projs.values():
    if isinstance(p, dict) and p.get("allowedTools") == []:
        p["allowedTools"] = ["Bash", "Edit", "Read", "Write", "Glob", "Grep"]

json.dump(d, open(cfg, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("defaultMode:", d["defaultMode"], "| bypassPermissionsMode:", d["bypassPermissionsMode"])
print("tool-capable models in picker:", [o["value"] for o in cache if "tools" in o.get("description", "")])
print("availableModels:", len(d["availableModels"]))
