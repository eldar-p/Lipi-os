import os
from pathlib import Path
def run(args):
    symbolic = False
    if args and args[0] in ("-s", "--symbolic"):
        symbolic = True
        args = args[1:]
    if len(args) < 2:
        return "Usage: ln [-s] <target> <link>"
    target, link = args[0], args[1]
    try:
        if symbolic:
            os.symlink(target, link)
        else:
            os.link(target, link)
        return ""
    except OSError as e:
        return f"ln: {e}"
