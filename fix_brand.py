import io, json, os, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = Path(r"Q:\claude-cli\better-clawd-src\src\utils\theme.ts")
t = p.read_text(encoding="utf-8")

# red-orange -> Anthropic "Claude" orange (#D97757), lighter/not deep
REPL = [
    ("rgb(226,74,15)",  "rgb(217,119,87)"),   # primary Anthropic orange
    ("rgb(255,110,45)", "rgb(230,150,120)"),  # shimmer
    ("rgb(255,150,90)", "rgb(240,180,150)"),  # light
    ("rgb(180,45,0)",   "rgb(184,105,80)"),   # deep, but warm not dark-red
    ("rgb(80,26,6)",    "rgb(70,48,40)"),     # selection bg -> warm brown
    ("rgb(64,22,6)",    "rgb(60,42,36)"),     # rate_limit_empty
]
for a, b in REPL:
    t = t.replace(a, b)
p.write_text(t, encoding="utf-8")

# black & white (oroboros-mono) as the default theme, config + fallback
cfg = Path(os.path.expanduser(r"~\.claude-cli\.claude-cli.json"))
d = json.loads(cfg.read_text(encoding="utf-8"))
d["theme"] = "oroboros-mono"
d["defaultTheme"] = "oroboros-mono"
cfg.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")

print("Anthropic orange present:", t.count("rgb(217,119,87)"))
print("leftover red-orange:", sum(t.count(x) for x in ("rgb(226,74,15)","rgb(255,110,45)","rgb(255,150,90)","rgb(180,45,0)")))
print("config theme:", d["theme"])
