def run(args):
    if not args:
        return "Usage: kill <pid>..."
    from core.task_manager import terminate_process
    out = []
    for a in args:
        try:
            pid = int(a.lstrip("-"))
        except ValueError:
            out.append(f"kill: invalid pid {a}"); continue
        ok = terminate_process(pid)
        out.append(f"killed {pid}" if ok else f"failed {pid}")
    return "\n".join(out)
