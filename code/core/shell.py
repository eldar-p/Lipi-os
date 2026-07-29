"""Lipi OS command shell."""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

from i18n import get_language_strings
from paths import COMMANDS_DIR


def _load_lang() -> dict:
    return get_language_strings()


# ======================
# Built-in commands
# ======================

def cmd_ls(args):
    path = args[0] if args else os.getcwd()
    try:
        items = os.listdir(path)
        return "\n".join(sorted(items))
    except Exception as e:
        return f"ls: error: {e}"


def cmd_cd(args):
    if not args:
        os.chdir(str(Path.home()))
        return ""
    path = args[0]
    try:
        os.chdir(path)
        return ""
    except FileNotFoundError:
        return f"cd: no such directory: {path}"
    except Exception as e:
        return f"cd: error: {e}"


def cmd_pwd(args):
    return os.getcwd()


def cmd_clear(args):
    os.system("cls" if os.name == "nt" else "clear")
    return ""


def cmd_mkdir(args):
    if not args:
        return "mkdir: missing operand"
    for dir_name in args:
        try:
            Path(dir_name).mkdir(parents=True, exist_ok=False)
        except Exception as e:
            return f"mkdir: {e}"
    return ""


def cmd_cat(args):
    if not args:
        return "cat: missing file operand"
    chunks = []
    for path in args:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                chunks.append(f.read())
        except Exception as e:
            return f"cat: {e}"
    return "".join(chunks)


def cmd_echo(args):
    return " ".join(args)


def cmd_exit(args):
    lang = _load_lang()
    print(lang.get("exit_message", "Goodbye!"))
    sys.exit(0)


def cmd_help(args):
    lang = _load_lang()
    names = sorted(COMMANDS.keys())
    return lang.get("available_commands", "Available commands: {}").format(", ".join(names))


def cmd_settings(args):
    from core.settings_manager import cli_settings, create_gui_settings

    if args and args[0] == "--gui":
        create_gui_settings()
    else:
        cli_settings()
    return ""


def cmd_tasks(args):
    from core.task_manager import cli_mode, create_gui_task_manager

    if args and args[0] == "--gui":
        create_gui_task_manager()
    else:
        cli_mode()
    return ""


def cmd_store(args):
    from core.app_store import cli_app_store, create_gui_app_store

    if args and args[0] == "--gui":
        create_gui_app_store()
    else:
        cli_app_store()
    return ""


def cmd_compile(args):
    from core.compiler_hub import cli_compiler_hub, create_gui_compiler_hub

    if args and args[0] == "--gui":
        create_gui_compiler_hub()
    else:
        cli_compiler_hub()
    return ""


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "pwd": cmd_pwd,
    "mkdir": cmd_mkdir,
    "clear": cmd_clear,
    "cls": cmd_clear,
    "cat": cmd_cat,
    "echo": cmd_echo,
    "exit": cmd_exit,
    "quit": cmd_exit,
    "help": cmd_help,
    "settings": cmd_settings,
    "tasks": cmd_tasks,
    "store": cmd_store,
    "compile": cmd_compile,
}


def _load_external_commands() -> None:
    """Load commands/<name>.py modules that expose run(args)."""
    if not COMMANDS_DIR.exists():
        return

    for path in sorted(COMMANDS_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        name = path.stem
        if name in COMMANDS:
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"lipi_cmd_{name}", path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "run") and callable(module.run):
                COMMANDS[name] = module.run
        except Exception as e:
            print(f"[shell] failed to load command '{name}': {e}")


_load_external_commands()


def run_command(line: str) -> str:
    if not line.strip():
        return ""

    # Support simple quotes for paths with spaces
    parts = _split_args(line)
    if not parts:
        return ""

    cmd = parts[0]
    args = parts[1:]

    if cmd in COMMANDS:
        result = COMMANDS[cmd](args)
        return "" if result is None else str(result)

    try:
        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            shell=(os.name == "nt"),
        )
        output = result.stdout or ""
        if result.stderr:
            output = (output + "\n" + result.stderr).strip()
        return output
    except FileNotFoundError:
        lang = _load_lang()
        return lang.get("unknown_command", "Command not found: {}").format(cmd)
    except Exception as e:
        return f"Error executing '{cmd}': {e}"


def _split_args(line: str) -> list[str]:
    """Minimal shell-like split supporting single/double quotes."""
    parts: list[str] = []
    buf: list[str] = []
    quote = None
    for ch in line.strip():
        if quote:
            if ch == quote:
                quote = None
            else:
                buf.append(ch)
        elif ch in ("'", '"'):
            quote = ch
        elif ch.isspace():
            if buf:
                parts.append("".join(buf))
                buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf))
    return parts


def start_shell() -> None:
    while True:
        try:
            lang = _load_lang()
            prompt = f"{lang.get('prompt', 'lipi@os:')}{os.getcwd()}$ "
            line = input(prompt)
            output = run_command(line)
            if output:
                print(output)
        except KeyboardInterrupt:
            lang = _load_lang()
            print("\n" + lang.get("use_exit", "Use 'exit' to quit."))
        except EOFError:
            print()
            cmd_exit([])


if __name__ == "__main__":
    start_shell()
