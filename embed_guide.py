import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

GUIDE = Path(r"C:\Users\incoguser\Downloads\CLAUDE-CLI-GUIDE\CLAUDE-CLI-GUIDE.md").read_text(encoding="utf-8")
BLOCK = ("\nTOOL SYSTEMS — YOU HAVE TOOLS AND THEY WORK (local, no external calls). "
         "This is your operating guide; it is fed to you and you must use it.\n"
         + GUIDE + "\n")

def embed(p: Path) -> int:
    raw = p.read_bytes().decode("utf-8-sig")
    if "CLAUDE-CLI-GUIDE" in raw or "THE FULL GUIDE" in raw:
        return 0
    params = raw.find("\nPARAMETER ")
    close = raw.rfind('"""', 0, params if params != -1 else len(raw))
    if close == -1:
        return 0
    # strip any earlier tool-systems block
    for marker in ("\nTOOL SYSTEMS — YOU HAVE TOOLS", "\nTOOL SYSTEMS (AGENT TOOLSET)",
                   "\nTOOL SYSTEMS — YOU HAVE TOOLS AND THEY WORK"):
        i = raw.find(marker)
        if i != -1 and i < close:
            raw = raw[:i] + raw[close:]
            params = raw.find("\nPARAMETER ")
            close = raw.rfind('"""', 0, params if params != -1 else len(raw))
    new = raw[:close] + BLOCK + "\n" + raw[close:]
    p.write_bytes(new.encode("utf-8"))
    return len(new) - len(raw)

files = []
files += list(Path(r"Q:\the-dna-forge\deepseek-prime-cl").glob("Modelfile.deepseek*"))
files += list(Path(r"Q:\the-dna-forge").glob("Modelfile.deepseek*"))
files += list(Path(r"Q:\claude-cli\claude7-identity").glob("Modelfile.claude-7*"))

n = 0
for p in files:
    d = embed(p)
    if d:
        n += 1
        print(p.name, "guide embedded (+%d chars)" % d)
print("modelfiles updated:", n)
