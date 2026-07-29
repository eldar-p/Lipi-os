from pathlib import Path
def run(args):
    if not args:
        return "Usage: dirname <path>"
    return str(Path(args[0]).parent)
