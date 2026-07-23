"""Remove files; use -r/-rf to remove directories."""
import os
import shutil


def run(args):
    if not args:
        return "rm: missing operand"

    recursive = False
    force = False
    paths = []
    for arg in args:
        if arg in ("-r", "-R", "--recursive"):
            recursive = True
        elif arg in ("-f", "--force"):
            force = True
        elif arg in ("-rf", "-fr"):
            recursive = True
            force = True
        elif arg.startswith("-"):
            return f"rm: invalid option: {arg}"
        else:
            paths.append(arg)

    if not paths:
        return "rm: missing operand"

    for path in paths:
        try:
            if os.path.isdir(path) and not os.path.islink(path):
                if not recursive:
                    return f"rm: cannot remove '{path}': Is a directory (use -r)"
                shutil.rmtree(path)
            else:
                os.remove(path)
        except FileNotFoundError:
            if not force:
                return f"rm: cannot remove '{path}': No such file or directory"
        except Exception as e:
            if not force:
                return f"rm: {e}"
    return ""
