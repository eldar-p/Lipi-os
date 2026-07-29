import difflib
from pathlib import Path
def run(args):
    if len(args) < 2:
        return "Usage: diff <file1> <file2>"
    try:
        a = Path(args[0]).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        b = Path(args[1]).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    except OSError as e:
        return f"diff: {e}"
    return "".join(difflib.unified_diff(a, b, fromfile=args[0], tofile=args[1])) or "(no differences)"
