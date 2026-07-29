"""Find files by name glob under a directory."""
from pathlib import Path

def run(args):
    root = Path(args[0]) if args else Path(".")
    pattern = "*"
    if "-name" in args:
        idx = args.index("-name")
        if idx + 1 < len(args):
            pattern = args[idx + 1]
        root = Path(args[0]) if args and args[0] != "-name" else Path(".")
    elif len(args) >= 2:
        root, pattern = Path(args[0]), args[1]
    if not root.exists():
        return f"find: {root}: No such directory"
    matches = sorted(str(p) for p in root.rglob(pattern) if p.is_file() or p.is_dir())
    return "\n".join(matches[:500]) + ("\n...(truncated)" if len(matches) > 500 else "")
