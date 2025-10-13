# shell.py
import os
import sys
import subprocess
import json
from pathlib import Path

# Загрузка языка из настроек
def load_language():
    config_path = Path("settings/config.json")
    lang = "en"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            lang = config.get("language", "en")
    # Загрузка переводов
    lang_file = Path(f"settings/lang/{lang}.json")
    if lang_file.exists():
        with open(lang_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # fallback на английский
        return {
            "prompt": "lipi@os: ",
            "unknown_command": "Command not found: {}",
            "exit_message": "Goodbye!"
        }

LANG = load_language()

# Встроенные команды
def cmd_ls(args):
    try:
        items = os.listdir(os.getcwd())
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
    os.system('cls' if os.name == 'nt' else 'clear')
    return ""

def cmd_mkdir(args):
    if not args:
        return "mkdir: missing operand"
    for dir_name in args:
        try:
            os.mkdir(dir_name)
        except Exception as e:
            return f"mkdir: {e}"
    return ""

def cmd_exit(args):
    print(LANG.get("exit_message", "Goodbye!"))
    sys.exit(0)

def cmd_help(args):
    return "Available commands: ls, cd, pwd, mkdir, clear, exit, help"

# Регистрация команд
COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "pwd": cmd_pwd,
    "mkdir": cmd_mkdir,
    "clear": cmd_clear,
    "exit": cmd_exit,
    "help": cmd_help,
}

def run_command(line):
    if not line.strip():
        return ""
    parts = line.split()
    cmd = parts[0]
    args = parts[1:]
    if cmd in COMMANDS:
        return COMMANDS[cmd](args)
    else:
        # Попытка запустить как внешнюю программу (например, python, nano)
        try:
            result = subprocess.run(parts, capture_output=True, text=True, shell=(os.name == 'nt'))
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
            return output
        except FileNotFoundError:
            return LANG.get("unknown_command", "Command not found: {}").format(cmd)
        except Exception as e:
            return f"Error executing '{cmd}': {e}"

def start_shell():
    while True:
        try:
            prompt = LANG.get("prompt", "lipi@os: ") + os.getcwd() + "$ "
            line = input(prompt)
            output = run_command(line)
            if output:
                print(output)
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit.")
        except EOFError:
            print()
            cmd_exit([])

if __name__ == "__main__":
    start_shell()
