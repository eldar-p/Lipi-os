"""Extended help / command catalog."""
def run(args):
    from core.shell import COMMANDS
    cats = {
        "files": ["ls", "cd", "pwd", "mkdir", "cat", "touch", "cp", "mv", "rm", "ln", "chmod", "tree", "find", "head", "tail", "wc", "grep", "sort", "uniq", "diff", "basename", "dirname", "realpath", "tee"],
        "system": ["sysinfo", "uname", "hostname", "whoami", "env", "df", "du", "free", "uptime", "ps", "kill", "tasks", "sleep", "clear", "cls"],
        "net": ["ping", "fetch", "download", "netinfo", "serve"],
        "apps": ["apps", "open", "run", "store", "settings"],
        "dev": ["compile", "langs", "calc", "date"],
        "shell": ["help", "history", "echo", "exit", "quit"],
    }
    if args:
        key = args[0].lower()
        if key in cats:
            return f"{key}: " + ", ".join(c for c in cats[key] if c in COMMANDS)
        if key in COMMANDS:
            return f"{key}: built-in/external Lipi command. Try `{key} -h` if supported."
        return f"Unknown topic. Categories: {', '.join(cats)}"
    lines = ["Lipi OS commands (help <category>):", ""]
    for cat, names in cats.items():
        present = [n for n in names if n in COMMANDS]
        lines.append(f"  {cat:8} {', '.join(present)}")
    lines.append("")
    lines.append("Languages: langs | compile langs | compile run python 'print(1)'")
    lines.append(f"Total commands: {len(COMMANDS)}")
    return "\n".join(lines)
