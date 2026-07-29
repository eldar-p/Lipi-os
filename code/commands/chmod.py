"""Basic chmod (octal mode)."""
import os
from pathlib import Path
def run(args):
    if len(args) < 2:
        return "Usage: chmod <mode> <file>...   e.g. chmod 755 script.sh"
    try:
        mode = int(args[0], 8)
    except ValueError:
        return "chmod: mode must be octal (e.g. 755)"
    out = []
    for f in args[1:]:
        try:
            os.chmod(f, mode)
        except OSError as e:
            out.append(f"chmod: {f}: {e}")
    return "\n".join(out)
