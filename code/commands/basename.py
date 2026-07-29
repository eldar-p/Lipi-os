from pathlib import Path
def run(args):
    if not args:
        return "Usage: basename <path>"
    return Path(args[0]).name
