from pathlib import Path
def run(args):
    reverse = "-r" in args
    unique = "-u" in args
    files = [a for a in args if not a.startswith("-")]
    lines = []
    if not files:
        return "Usage: sort [-r] [-u] <file>..."
    for f in files:
        try:
            lines.extend(Path(f).read_text(encoding="utf-8", errors="replace").splitlines())
        except OSError as e:
            return f"sort: {e}"
    lines = sorted(lines, reverse=reverse)
    if unique:
        out, prev = [], object()
        for x in lines:
            if x != prev:
                out.append(x); prev = x
        lines = out
    return "\n".join(lines)
