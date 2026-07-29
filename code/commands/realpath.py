from pathlib import Path
def run(args):
    if not args:
        return "Usage: realpath <path>"
    try:
        return str(Path(args[0]).resolve())
    except OSError as e:
        return f"realpath: {e}"
