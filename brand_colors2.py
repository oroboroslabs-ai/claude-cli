import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = Path(r"Q:\claude-cli\better-clawd-src\src\utils\theme.ts")
t = p.read_text(encoding="utf-8")

# Orange + black "night sky": warm oranges for accents, near-black warm
# backgrounds instead of blue/grey, orange selection instead of blue.
REPL = [
    # accent family -> orange
    ("rgb(177,185,249)", "rgb(230,126,34)"),   # permission/suggestion/remember/rate_limit_fill
    ("rgb(207,215,255)", "rgb(255,160,80)"),   # permissionShimmer
    ("rgb(147,165,255)", "rgb(230,126,34)"),   # system spinner
    ("rgb(177,195,255)", "rgb(255,160,80)"),   # system spinner shimmer
    ("rgb(122,180,232)", "rgb(255,160,80)"),   # briefLabelYou
    ("rgb(80,83,112)",   "rgb(60,30,10)"),     # rate_limit_empty -> dark burnt
    # backgrounds -> warm near-black
    ("rgb(55, 55, 55)",  "rgb(24,20,16)"),     # userMessageBackground
    ("rgb(70, 70, 70)",  "rgb(42,34,26)"),     # userMessageBackgroundHover
    ("rgb(44, 50, 62)",  "rgb(26,22,18)"),     # messageActionsBackground (was blue-grey)
    ("rgb(65, 60, 65)",  "rgb(30,26,22)"),     # bashMessageBackgroundColor
    ("rgb(55, 65, 70)",  "rgb(28,24,20)"),     # memoryBackgroundColor
    ("rgb(38, 79, 120)", "rgb(74,38,8)"),      # selectionBg -> warm dark orange
    # cyan -> orange
    ("rgb(0,204,204)",   "rgb(204,85,0)"),
    # light-theme warm equivalents
    ("rgb(232, 236, 244)", "rgb(245,240,235)"),  # messageActionsBackground (light)
    ("rgb(180, 213, 255)", "rgb(255,225,200)"),  # selectionBg (light) -> warm
]
for a, b in REPL:
    t = t.replace(a, b)

p.write_text(t, encoding="utf-8")
leftover = [c for c in ("rgb(177,185,249)","rgb(207,215,255)","rgb(147,165,255)","rgb(44, 50, 62)","rgb(38, 79, 120)","rgb(0,204,204)") if c in t]
print("orange+black applied")
print("leftover blue-ish:", leftover if leftover else "none")
print("backgrounds warm-black present:", t.count("rgb(24,20,16)") + t.count("rgb(26,22,18)"))
