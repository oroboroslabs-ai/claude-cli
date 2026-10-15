import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = Path(r"Q:\claude-cli\better-clawd-src\src\utils\theme.ts")
t = p.read_text(encoding="utf-8")

# amber/burnt orange -> RED-ORANGE family
REPL = [
    ("rgb(204,85,0)",   "rgb(226,74,15)"),    # primary red-orange
    ("rgb(230,126,34)", "rgb(255,110,45)"),   # shimmer / lighter red-orange
    ("rgb(255,160,80)", "rgb(255,150,90)"),   # lightest red-orange
    ("rgb(191,79,0)",   "rgb(180,45,0)"),     # deep red-orange
    ("rgb(74,38,8)",    "rgb(80,26,6)"),      # selection bg (dark red)
    ("rgb(60,30,10)",   "rgb(64,22,6)"),      # rate_limit_empty
]
for a, b in REPL:
    t = t.replace(a, b)
p.write_text(t, encoding="utf-8")
print("primary:", t.count("rgb(226,74,15)"),
      "| shimmer:", t.count("rgb(255,110,45)"),
      "| light:", t.count("rgb(255,150,90)"),
      "| deep:", t.count("rgb(180,45,0)"))
print("leftover amber:", sum(t.count(x) for x in ("rgb(204,85,0)","rgb(230,126,34)","rgb(255,160,80)")))
