"""List programming language toolchains available to Lipi OS."""
def run(args):
    from core.compiler_hub import language_status
    only = None
    if args and args[0] in ("ready", "-r"):
        only = True
    if args and args[0] in ("missing", "-m"):
        only = False
    rows = language_status()
    lines = [f"{'ID':12} {'NAME':24} {'OK':4} NOTE"]
    for r in rows:
        if only is True and not r["ready"]:
            continue
        if only is False and r["ready"]:
            continue
        lines.append(f"{r['id']:12} {r['name'][:24]:24} {('yes' if r['ready'] else 'no'):4} {r['note']}")
    lines.append("")
    lines.append("Run code:  compile run <lang> <code>")
    lines.append("From file: compile file <lang> <path>")
    lines.append("Interactive: compile")
    return "\n".join(lines)
