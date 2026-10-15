import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = Path(r"Q:\claude-cli\better-clawd-src\src\utils\theme.ts")
t = p.read_text(encoding="utf-8")

# Anthropic blue family  ->  Oroboros burnt orange family
REPL = [
    ("rgb(59,130,246)",  "rgb(204,85,0)"),    # claude (light)      -> burnt orange
    ("rgb(96,165,250)",  "rgb(230,126,34)"),  # claudeShimmer (light) / claude (dark)
    ("rgb(87,105,247)",  "rgb(204,85,0)"),    # spinner / permission / suggestion / rate_limit_fill
    ("rgb(117,135,255)", "rgb(230,126,34)"),  # spinner shimmer
    ("rgb(137,155,255)", "rgb(230,126,34)"),  # permission shimmer
    ("rgb(71,130,200)",  "rgb(204,85,0)"),    # ide
    ("rgb(37,99,235)",   "rgb(191,79,0)"),    # fastMode (deep burnt)
    ("rgb(51,102,255)",  "rgb(204,85,0)"),    # daltonized (light)
    ("rgb(101,152,255)", "rgb(230,126,34)"),  # daltonized shimmer (light)
    ("rgb(147,197,253)", "rgb(230,126,34)"),  # claudeShimmer (dark)
    ("rgb(153,204,255)", "rgb(230,126,34)"),  # daltonized (dark)
    ("rgb(183,224,255)", "rgb(255,160,80)"),  # daltonized shimmer (dark)
    ("rgb(39,47,111)",   "rgb(90,38,6)"),     # rate_limit_empty (dark burnt)
]
total = 0
for a, b in REPL:
    n = t.count(a)
    if n:
        t = t.replace(a, b)
ch = t.count("rgb(204,85,0)") + t.count("rgb(230,126,34)")
p.write_text(t, encoding="utf-8")
print("replaced blue -> burnt orange family")
print("burnt-orange primary present:", t.count("rgb(204,85,0)"), "| shimmer:", t.count("rgb(230,126,34)"))
print("remaining raw blue accent refs:", sum(t.count(x) for x in ("rgb(59,130,246)","rgb(96,165,250)","rgb(87,105,247)","rgb(71,130,200)")))
