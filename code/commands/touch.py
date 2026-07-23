"""Create empty files or update timestamps."""
from pathlib import Path


def run(args):
    if not args:
        return "touch: missing file operand"
    for name in args:
        path = Path(name)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True)
        except Exception as e:
            return f"touch: {e}"
    return ""
