"""Count lines, words, bytes."""
from pathlib import Path

def run(args):
    if not args:
        return "Usage: wc <file>..."
    lines_out = []
    for p in args:
        path = Path(p)
        try:
            data = path.read_bytes()
            text = data.decode("utf-8", errors="replace")
            lc = text.count("\n") + (0 if text.endswith("\n") or not text else 1)
            wc = len(text.split())
            bc = len(data)
            lines_out.append(f"{lc:8} {wc:8} {bc:8} {p}")
        except OSError as e:
            lines_out.append(f"wc: {e}")
    return "\n".join(lines_out)
