import os
import shutil

def run(args):
    if not args:
        return "rm: missing operand"
    for path in args:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except Exception as e:
            return f"rm: {e}"
    return ""
