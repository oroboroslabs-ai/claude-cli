import json, os
cfg = os.path.expanduser(r"~\.claude-cli\.claude-cli.json")
d = json.load(open(cfg, encoding="utf-8"))
latest = [
    ("claude-7:1gb", "Claude 7", "Orchestrator - 1.9 GB"),
    ("claude-7:fat", "Claude 7 (real 14B)", "Faithful 14B - 5.8 GB"),
    ("claude-7:latest", "Claude 7 (14B Q5)", "Full quality - 10 GB"),
    ("oroboros-labs/claude-fable7-undecillion-sse:latest", "Claude Fable 7 Undecillion", "Local - 9.9 GB"),
    ("claude-fable5-undecillion:latest", "Claude Fable 5 Undecillion", "Local - 11 GB"),
    ("oroboros-labs/claude-opus-9-undecillion-sse:latest", "Claude Opus 9 Undecillion", "Local - 16/29 GB"),
    ("claude-opus-9-undecillion-v:latest", "Claude Opus 9 Undecillion V", "Local - 11 GB"),
    ("oroboros-labs/gpt-5.6-sol-undecillion-6u5go5:latest", "GPT-5.6 Sol Undecillion", "Local - 11 GB"),
    ("oroboros-labs/gpt-astra-7-undecillion-7u5go5:latest", "GPT Astra 7 Undecillion", "Local - 11 GB"),
    ("oroboros-labs/claude-sonnet-7-undecillion:latest", "Claude Sonnet 7 Undecillion", "Local - 11 GB"),
    ("deepseek-prime-cl-1q5duo5:compounded", "DeepSeek Prime (Compounded)", "Local - 5 GB"),
]
d["additionalModelOptionsCache"] = [
    {"value": v, "label": l, "description": desc} for v, l, desc in latest
]
json.dump(d, open(cfg, "w", encoding="utf-8"), indent=2)
print("wrote", len(latest), "latest models into additionalModelOptionsCache")
