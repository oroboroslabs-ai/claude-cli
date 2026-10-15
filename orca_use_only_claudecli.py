import json, os, shutil, time
p = os.path.join(os.environ["APPDATA"], "orca", "orca-data.json")
shutil.copyfile(p, p + ".bak-claudecli-only-" + time.strftime("%Y%m%d-%H%M%S"))
d = json.load(open(p, encoding="utf-8"))

AGENTS = [
    "claude", "claude-agent-teams", "openclaude", "codex", "gemini", "antigravity",
    "aider", "amp", "kiro", "crush", "autohand", "cline", "command-code", "continue",
    "cursor", "kimi", "mistral-vibe", "qwen-code", "rovo", "hermes", "copilot", "grok",
    "goose", "custom",
]
ov = d.setdefault("agentCmdOverrides", {})
for a in AGENTS:
    ov[a] = "claude-cli"

# any custom agent command also points at our CLI
for k in list(d.keys()):
    v = d[k]
    if isinstance(v, dict) and "customAgentCommand" in v:
        v["customAgentCommand"] = "claude-cli"

# walk nested dicts for customAgentCommand / selectedAgent
def walk(o):
    if isinstance(o, dict):
        if "customAgentCommand" in o:
            o["customAgentCommand"] = "claude-cli"
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)
walk(d)

json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("agentCmdOverrides set to claude-cli for", len(AGENTS), "agents")
print("overrides:", json.dumps(ov, ensure_ascii=False))
