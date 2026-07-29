import os
def run(args):
    if not args:
        return "\n".join(f"{k}={v}" for k, v in sorted(os.environ.items()))
    if args[0] == "-u" and len(args) >= 2:
        os.environ.pop(args[1], None)
        return ""
    if "=" in args[0]:
        k, _, v = args[0].partition("=")
        os.environ[k] = v
        return ""
    return os.environ.get(args[0], "")
