"""Write stdin-like args to file and stdout (echo | tee file)."""
from pathlib import Path
def run(args):
    # Usage: tee [-a] file  text...
    append = False
    if args and args[0] == "-a":
        append = True
        args = args[1:]
    if len(args) < 2:
        return "Usage: tee [-a] <file> <text...>"
    path = Path(args[0])
    text = " ".join(args[1:]) + "\n"
    with open(path, "a" if append else "w", encoding="utf-8") as f:
        f.write(text)
    return text.rstrip("\n")
