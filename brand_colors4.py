import io, sys, json, os
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = Path(r"Q:\claude-cli\better-clawd-src\src\utils\theme.ts")
t = p.read_text(encoding="utf-8")

# remaining blue / cyan accents -> red-orange family + warm neutrals
REPL = [
    ("rgb(51,153,255)", "rgb(226,74,15)"),
    ("rgb(8,145,178)",  "rgb(180,45,0)"),
    ("rgb(0,102,153)",  "rgb(226,74,15)"),
    ("rgb(0,102,204)",  "rgb(226,74,15)"),
    ("rgb(0,119,179)",  "rgb(255,110,45)"),
    ("rgb(0,153,153)",  "rgb(226,74,15)"),
    ("rgb(0,178,178)",  "rgb(255,110,45)"),
    ("rgb(102,153,153)","rgb(255,150,90)"),
    ("rgb(102,178,255)","rgb(255,110,45)"),
    ("rgb(102,204,204)","rgb(255,150,90)"),
    ("rgb(106,155,204)","rgb(226,74,15)"),
    ("rgb(51,102,204)", "rgb(226,74,15)"),
    ("rgb(209,231,253)","rgb(255,225,200)"),
    ("rgb(230,245,250)","rgb(245,240,235)"),
    ("rgb(210,216,226)","rgb(240,235,230)"),
]
for a, b in REPL:
    t = t.replace(a, b)
p.write_text(t, encoding="utf-8")

# set the official theme to dark (night sky)
cfg = Path(os.path.expanduser(r"~\.claude-cli\.claude-cli.json"))
d = json.loads(cfg.read_text(encoding="utf-8"))
d["theme"] = "dark"
d["defaultTheme"] = "dark"
cfg.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")

blue = sum(t.count(x) for x in ("rgb(51,153,255)","rgb(8,145,178)","rgb(0,102,153)",
        "rgb(0,102,204)","rgb(0,119,179)","rgb(0,153,153)","rgb(0,178,178)",
        "rgb(102,178,255)","rgb(102,204,204)","rgb(106,155,204)","rgb(51,102,204)"))
print("blue/cyan accents remaining:", blue)
print("primary red-orange:", t.count("rgb(226,74,15)"), "| shimmer:", t.count("rgb(255,110,45)"))
print("config theme set to:", d["theme"])
