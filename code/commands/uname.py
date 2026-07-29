import os, platform
def run(args):
    if "-a" in args or "--all" in args:
        return f"{platform.system()} {platform.node()} {platform.release()} {platform.version()} {platform.machine()}"
    if "-s" in args:
        return platform.system()
    if "-r" in args:
        return platform.release()
    if "-m" in args:
        return platform.machine()
    return platform.system()
