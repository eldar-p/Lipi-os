def run(args):
    from core.task_manager import get_processes, print_table
    procs = get_processes()
    if args and args[0].isdigit():
        procs = [p for p in procs if str(p.get("pid")) == args[0]]
    print_table(procs[:40])
    return ""
