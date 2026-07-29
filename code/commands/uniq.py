from pathlib import Path
def run(args):
    if not args:
        return "Usage: uniq <file>"
    try:
        lines = Path(args[0]).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        return f"uniq: {e}"
    out, prev = [], object()
    for x in lines:
        if x != prev:
            out.append(x); prev = x
    return "\n".join(out)
