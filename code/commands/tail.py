"""Print last N lines of files."""
from pathlib import Path

def run(args):
    n = 10
    paths = []
    i = 0
    while i < len(args):
        if args[i] in ("-n", "--lines") and i + 1 < len(args):
            try:
                n = int(args[i + 1])
            except ValueError:
                return "tail: invalid line count"
            i += 2
            continue
        paths.append(args[i])
        i += 1
    if not paths:
        return "Usage: tail [-n N] <file>..."
    out = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            out.append(f"tail: {p}: No such file")
            continue
        if len(paths) > 1:
            out.append(f"==> {p} <==")
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            out.extend(lines[-n:])
        except OSError as e:
            out.append(f"tail: {e}")
    return "\n".join(out)
