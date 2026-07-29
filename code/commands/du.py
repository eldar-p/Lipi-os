from pathlib import Path
def run(args):
    path = Path(args[0]) if args else Path(".")
    if not path.exists():
        return f"du: {path}: not found"
    total = 0
    if path.is_file():
        total = path.stat().st_size
    else:
        for p in path.rglob("*"):
            if p.is_file():
                try: total += p.stat().st_size
                except OSError: pass
    if total > 1024**2:
        return f"{total / 1024**2:.2f}M\t{path}"
    if total > 1024:
        return f"{total / 1024:.1f}K\t{path}"
    return f"{total}\t{path}"
