"""Print directory tree."""
from pathlib import Path

def _walk(path: Path, prefix: str, lines: list, depth: int, max_depth: int):
    if depth > max_depth:
        return
    try:
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except OSError:
        return
    entries = [e for e in entries if e.name not in (".git", "__pycache__", ".work")]
    for i, e in enumerate(entries):
        last = i == len(entries) - 1
        branch = "└── " if last else "├── "
        lines.append(prefix + branch + e.name + ("/" if e.is_dir() else ""))
        if e.is_dir():
            _walk(e, prefix + ("    " if last else "│   "), lines, depth + 1, max_depth)

def run(args):
    root = Path(args[0]) if args else Path(".")
    max_depth = 3
    if "-L" in args:
        i = args.index("-L")
        if i + 1 < len(args):
            try: max_depth = int(args[i + 1])
            except ValueError: pass
        if args[0] != "-L":
            root = Path(args[0])
    if not root.exists():
        return f"tree: {root}: not found"
    lines = [str(root)]
    _walk(root, "", lines, 1, max_depth)
    return "\n".join(lines[:1000])
