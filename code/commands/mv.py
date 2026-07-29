"""Move/rename files or directories."""
import shutil


def run(args):
    if len(args) < 2:
        return "mv: missing file operand"
    src, dst = args[0], args[1]
    try:
        shutil.move(src, dst)
        return ""
    except Exception as e:
        return f"mv: {e}"
