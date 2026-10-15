import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = Path(r"Q:\claude-cli\better-clawd-src\src\components\LogoV2\Clawd.tsx")
t = p.read_text(encoding="utf-8")

# Make every pose render the Oroboros flipped-A (∀) mark.
REPL = [
    # row 1 eye segments (all poses) -> top bar of the ∀
    ("r1E: '▛███▜'", "r1E: '▛▀▀▀▜'"),
    ("r1E: '▟███▟'", "r1E: '▛▀▀▀▜'"),
    ("r1E: '▙███▙'", "r1E: '▛▀▀▀▜'"),
    # drop the arms/side strokes
    ("r1L: ' ▐'", "r1L: ''"),
    ("r1L: '▗▟'", "r1L: ''"),
    ("r1R: '▌'", "r1R: ''"),
    ("r1R: '▙▖'", "r1R: ''"),
    ("r2L: '▝▜'", "r2L: ''"),
    ("r2L: ' ▜'", "r2L: ''"),
    ("r2R: '▛▘'", "r2R: ''"),
    ("r2R: '▛ '", "r2R: ''"),
    # row 2 body -> middle band of the ∀
    ('<Text color="clawd_body" backgroundColor="clawd_background">█████</Text>',
     '<Text color="clawd_body" backgroundColor="clawd_background">{" ▜▄▛ "}</Text>'),
    # row 3 -> the point of the ∀
    ('<Text color="clawd_body">{"  "}▘▘ ▝▝{"  "}</Text>',
     '<Text color="clawd_body">{"  ▜  "}</Text>'),
    # Apple-terminal path: same mark
    ("<Text color=\"clawd_background\" backgroundColor=\"clawd_body\">{t2}</Text>",
     "<Text color=\"clawd_background\" backgroundColor=\"clawd_body\">{' ▜▄▛ '}</Text>"),
    ('<Text backgroundColor="clawd_body">{" ".repeat(7)}</Text>',
     '<Text backgroundColor="clawd_body">{"  ▜  "}</Text>'),
    ('<Text color="clawd_body">▘▘ ▝▝</Text>',
     '<Text color="clawd_body">{"  ▜  "}</Text>'),
]
n = 0
for a, b in REPL:
    c = t.count(a)
    n += c
    t = t.replace(a, b)
p.write_text(t, encoding="utf-8")
print("Clawd mark replacements applied:", n)
print("old body blocks left:", t.count("███"))
