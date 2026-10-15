import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

AGENT = Path(r"Q:\claude-cli\AGENT-TOOLSET.md").read_text(encoding="utf-8")
BLOCK = "\nTOOL SYSTEMS (AGENT TOOLSET) — YOU HAVE TOOLS AND THEY WORK, LOCALLY\n" + AGENT + "\n"

# DeepSeek modelfiles: replace the earlier short block (or add) with the full one.
DS_DIRS = [Path(r"Q:\the-dna-forge\deepseek-prime-cl"), Path(r"Q:\the-dna-forge")]
count = 0
for d in DS_DIRS:
    for p in d.glob("Modelfile.deepseek*"):
        raw = p.read_bytes().decode("utf-8-sig")
        if "AGENT TOOLSET" in raw:
            continue
        params = raw.find("\nPARAMETER ")
        close = raw.rfind('"""', 0, params if params != -1 else len(raw))
        if close == -1:
            continue
        # drop the earlier short TOOL SYSTEMS block if present
        idx = raw.find("\nTOOL SYSTEMS")
        if idx != -1 and idx < close:
            raw = raw[:idx] + raw[close:]
            params = raw.find("\nPARAMETER ")
            close = raw.rfind('"""', 0, params if params != -1 else len(raw))
        new = raw[:close] + BLOCK + "\n" + raw[close:]
        p.write_bytes(new.encode("utf-8"))
        count += 1
        print(p.name, "AGENT TOOLSET embedded (+%d chars)" % (len(new) - len(raw)))

# claude-7 modelfiles
C7 = Path(r"Q:\claude-cli\claude7-identity")
for p in C7.glob("Modelfile.claude-7*"):
    raw = p.read_bytes().decode("utf-8-sig")
    if "AGENT TOOLSET" in raw:
        continue
    params = raw.find("\nPARAMETER ")
    close = raw.rfind('"""', 0, params if params != -1 else len(raw))
    if close == -1:
        continue
    idx = raw.find("\nTOOL SYSTEMS")
    if idx != -1 and idx < close:
        raw = raw[:idx] + raw[close:]
        params = raw.find("\nPARAMETER ")
        close = raw.rfind('"""', 0, params if params != -1 else len(raw))
    new = raw[:close] + BLOCK + "\n" + raw[close:]
    p.write_bytes(new.encode("utf-8"))
    count += 1
    print(p.name, "AGENT TOOLSET embedded")

print("total modelfiles updated:", count)
