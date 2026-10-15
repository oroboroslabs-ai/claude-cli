import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = Path(r"Q:\claude-cli\better-clawd-src\src\utils\theme.ts")
t = p.read_text(encoding="utf-8")
# clawd logo -> white (keep background black), all themes
t = t.replace("clawd_body: 'rgb(226,74,15)',", "clawd_body: 'rgb(255,255,255)',")
t = t.replace("clawd_body: 'rgb(255,110,45)',", "clawd_body: 'rgb(255,255,255)',")
t = t.replace("clawd_body: 'ansi:blueBright',", "clawd_body: 'ansi:whiteBright',")
p.write_text(t, encoding="utf-8")
print("clawd_body white count:", t.count("clawd_body: 'rgb(255,255,255)'") + t.count("clawd_body: 'ansi:whiteBright'"))
print("leftover colored:", t.count("clawd_body: 'rgb(226,74,15)'") + t.count("clawd_body: 'rgb(255,110,45)'") + t.count("clawd_body: 'ansi:blueBright'"))
