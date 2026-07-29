import shutil
def run(args):
    if not args:
        return "Usage: which <cmd>..."
    lines = []
    for name in args:
        path = shutil.which(name)
        lines.append(path or f"{name} not found")
    return "\n".join(lines)
