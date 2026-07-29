"""Search text in files (simple substring/regex)."""
import re
from pathlib import Path

def run(args):
    use_re = False
    ignore = False
    files = []
    pattern = None
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-i",):
            ignore = True; i += 1; continue
        if a in ("-E", "--regex"):
            use_re = True; i += 1; continue
        if pattern is None:
            pattern = a; i += 1; continue
        files.append(a); i += 1
    if pattern is None or not files:
        return "Usage: grep [-i] [-E] <pattern> <file>..."
    flags = re.IGNORECASE if ignore else 0
    rx = re.compile(pattern if use_re else re.escape(pattern), flags)
    out = []
    for f in files:
        path = Path(f)
        if not path.exists():
            out.append(f"grep: {f}: No such file"); continue
        try:
            for ln, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if rx.search(line):
                    prefix = f"{f}:" if len(files) > 1 else ""
                    out.append(f"{prefix}{ln}:{line}")
        except OSError as e:
            out.append(f"grep: {e}")
    return "\n".join(out) if out else ""
