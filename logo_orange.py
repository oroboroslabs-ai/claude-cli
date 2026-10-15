import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = Path(r"Q:\claude-cli\better-clawd-src\src\utils\theme.ts")
t = p.read_text(encoding="utf-8")

# little-guy mascot -> brand orange in every color theme; white only in mono
lines = t.split("\n")
out = []
for ln in lines:
    s = ln.strip()
    if s.startswith("clawd_body:"):
        if "'ansi:whiteBright'" in s:
            out.append("  clawd_body: 'ansi:yellow',")
            continue
        if "'rgb(255,255,255)'" in s:
            # only the RGB themes that are NOT the mono theme get orange.
            out.append(ln)  # keep; fixed below by mono detection
            continue
    out.append(ln)
t2 = "\n".join(out)

# Set the non-mono RGB themes' black/white mascot to orange, but leave the
# oroborosMonoTheme block white. Find the mono block span.
mono_start = t2.find("const oroborosMonoTheme")
head, tail = t2[:mono_start], t2[mono_start:]
head = head.replace("clawd_body: 'rgb(255,255,255)'", "clawd_body: 'rgb(217,119,87)'")
t2 = head + tail
p.write_text(t2, encoding="utf-8")
print("orange mascot:", t2.count("clawd_body: 'rgb(217,119,87)'"),
      "| white (mono):", t2.count("clawd_body: 'rgb(255,255,255)'"),
      "| ansi yellow:", t2.count("clawd_body: 'ansi:yellow'"))
