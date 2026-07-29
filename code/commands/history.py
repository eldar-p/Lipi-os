"""Show Lipi shell command history."""
def run(args):
    try:
        from core import shell
        hist = getattr(shell, "HISTORY", [])
    except Exception:
        hist = []
    if not hist:
        return "(empty history)"
    n = 50
    if args:
        try: n = int(args[0])
        except ValueError: pass
    lines = [f"{i:4}  {line}" for i, line in enumerate(hist[-n:], start=max(1, len(hist)-n+1))]
    return "\n".join(lines)
