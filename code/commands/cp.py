import shutil
import os

def run(args):
    if len(args) < 2:
        return "cp: missing file operand"
    src, dst = args[0], args[1]
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        return ""
    except Exception as e:
        return f"cp: {e}"
