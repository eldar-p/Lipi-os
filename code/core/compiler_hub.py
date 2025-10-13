# compiler_hub.py
import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path

# Пути
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# Поддерживаемые языки
SUPPORTED_LANGUAGES = {
    "c": {
        "name": "C",
        "name_ru": "Си",
        "extension": ".c",
        "compiler": "gcc",
        "compile_cmd": ["gcc", "{source}", "-o", "{output}"],
        "run_cmd": ["{output}"]
    },
    "cpp": {
        "name": "C++",
        "name_ru": "C++",
        "extension": ".cpp",
        "compiler": "g++",
        "compile_cmd": ["g++", "{source}", "-o", "{output}"],
        "run_cmd": ["{output}"]
    },
    "cs": {
        "name": "C#",
        "name_ru": "C#",
        "extension": ".cs",
        "compiler": "dotnet",
        "compile_cmd": ["dotnet", "script", "{source}"],  # или использовать csc
        "run_cmd": ["dotnet", "script", "{source}"]
    },
    "rust": {
        "name": "Rust",
        "name_ru": "Rust",
        "extension": ".rs",
        "compiler": "rustc",
        "compile_cmd": ["rustc", "{source}", "-o", "{output}"],
        "run_cmd": ["{output}"]
    },
    "asm": {
        "name": "Assembly (NASM)",
        "name_ru": "Ассемблер (NASM)",
        "extension": ".asm",
        "compiler": "nasm",
        "compile_cmd": ["nasm", "-f", "elf64", "{source}", "-o", "{output}.o"] + 
                      (["ld", "{output}.o", "-o", "{output}"] if os.name != "nt" else []),
        "run_cmd": ["{output}"]
    },
    "python": {
        "name": "Python",
        "name_ru": "Python",
        "extension": ".py",
        "compiler": "python",
        "compile_cmd": None,  # интерпретируемый
        "run_cmd": [sys.executable, "{source}"]
    },
    "javascript": {
        "name": "JavaScript",
        "name_ru": "JavaScript",
        "extension": ".js",
        "compiler": "node",
        "compile_cmd": None,
        "run_cmd": ["node", "{source}"]
    }
}

# ======================
# ЛОКАЛИЗАЦИЯ
# ======================

def load_language():
    config_path = Path("settings/config.json")
    lang = "en"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                lang = cfg.get("language", "en")
        except:
            pass

    lang_file = Path(f"settings/lang/{lang}.json")
    fallback = {
        "title": "Compiler Hub",
        "select_lang": "Select language:",
        "enter_code": "Enter your code (press Ctrl+D or Ctrl+Z to finish):",
        "compiling": "Compiling...",
        "running": "Running...",
        "success": "Execution completed.",
        "error_compile": "Compilation error:\n{}",
        "error_run": "Runtime error:\n{}",
        "compiler_not_found": "Compiler '{}' not found. Please install it or set path in settings.",
        "back": "Back",
        "exit": "Exit"
    }

    if lang_file.exists():
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                user_lang = json.load(f)
                for k in fallback:
                    if k not in user_lang:
                        user_lang[k] = fallback[k]
                return user_lang
        except:
            pass
    return fallback

LANG = load_language()

# ======================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ======================

def load_compiler_paths():
    """Загружает пути к компиляторам из настроек"""
    config_path = Path("settings/config.json")
    paths = {}
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                paths = cfg.get("compiler_paths", {})
        except:
            pass
    return paths

def find_compiler(name):
    """Ищет компилятор в PATH или в настройках"""
    compiler_paths = load_compiler_paths()
    custom_path = compiler_paths.get(name)
    if custom_path and Path(custom_path).exists():
        return custom_path

    # Поиск в системе
    import shutil
    return shutil.which(name)

def compile_and_run(language_id, code):
    """Компилирует и запускает код на указанном языке"""
    lang_info = SUPPORTED_LANGUAGES.get(language_id)
    if not lang_info:
        return False, "Unsupported language"

    compiler_name = lang_info["compiler"]
    compiler_path = find_compiler(compiler_name)
    if not compiler_path and lang_info["compile_cmd"] is not None:
        return False, LANG["compiler_not_found"].format(compiler_name)

    # Создаём временный файл с кодом
    source_file = TEMP_DIR / f"temp{lang_info['extension']}"
    with open(source_file, "w", encoding="utf-8") as f:
        f.write(code)

    output_file = TEMP_DIR / "temp_exec"
    if os.name == "nt" and language_id in ("c", "cpp", "rust"):
        output_file = output_file.with_suffix(".exe")

    try:
        # Компиляция (если требуется)
        if lang_info["compile_cmd"]:
            cmd = [part.format(source=source_file, output=output_file) for part in lang_info["compile_cmd"]]
            if compiler_path:
                cmd[0] = compiler_path

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=TEMP_DIR)
            if result.returncode != 0:
                return False, LANG["error_compile"].format(result.stderr or result.stdout)

        # Запуск
        run_cmd = [part.format(source=source_file, output=output_file) for part in lang_info["run_cmd"]]
        result = subprocess.run(run_cmd, capture_output=True, text=True, cwd=TEMP_DIR)
        output = result.stdout
        if result.stderr:
            output += "\n[STDERR]\n" + result.stderr
        if result.returncode != 0 and not output:
            output = f"Process exited with code {result.returncode}"

        return True, output

    except Exception as e:
        return False, str(e)
    finally:
        # Очистка (опционально — можно оставить для отладки)
        # source_file.unlink(missing_ok=True)
        # if output_file.exists():
        #     output_file.unlink()

# ======================
# CLI-РЕЖИМ
# ======================

def cli_compiler_hub():
    print(f"\n=== {LANG['title']} ===")
    
    # Выбор языка
    print(LANG["select_lang"])
    lang_list = list(SUPPORTED_LANGUAGES.keys())
    for i, lid in enumerate(lang_list, 1):
        name = SUPPORTED_LANGUAGES[lid].get("name_ru" if "ru" in str(LANG_DIR) else "name", lid)
        print(f"{i}. {name}")

    try:
        choice = int(input("> ")) - 1
        if choice < 0 or choice >= len(lang_list):
            print("Invalid choice")
            return
        lang_id = lang_list[choice]
    except:
        print("Invalid input")
        return

    print(LANG["enter_code"])
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    code = "\n".join(lines)
    if not code.strip():
        print("Empty code")
        return

    print(LANG["compiling"])
    success, output = compile_and_run(lang_id, code)
    print(LANG["running"])
    if success:
        print(output)
        print(LANG["success"])
    else:
        print(output)

# ======================
# GUI-РЕЖИМ
# ======================

def create_gui_compiler_hub():
    try:
        from gui_engine import LipiWindow
    except ImportError:
        print("GUI not available. Using CLI.")
        return cli_compiler_hub()

    win = LipiWindow(LANG["title"], 900, 600)
    from tkinter import Text, Scrollbar, OptionMenu, StringVar, Button, Frame, Label

    # Выбор языка
    lang_var = StringVar(win.root)
    lang_list = list(SUPPORTED_LANGUAGES.keys())
    lang_names = []
    for lid in lang_list:
        name = SUPPORTED_LANGUAGES[lid].get("name_ru", SUPPORTED_LANGUAGES[lid]["name"])
        lang_names.append(name)
    lang_var.set(lang_names[0])

    lang_menu = OptionMenu(win.content, lang_var, *lang_names)
    lang_menu.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    # Поле ввода кода
    code_text = Text(win.content, wrap="word", font=("Courier", 10))
    code_scroll = Scrollbar(win.content, command=code_text.yview)
    code_text.config(yscrollcommand=code_scroll.set)
    code_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5)
    code_scroll.grid(row=1, column=2, sticky="ns")

    # Кнопки
    button_frame = Frame(win.content, bg="white")
    button_frame.grid(row=2, column=0, columnspan=3, pady=5)

    output_text = None

    def run_code():
        nonlocal output_text
        if output_text:
            output_text.destroy()

        # Получаем ID языка по отображаемому имени
        selected_name = lang_var.get()
        lang_id = None
        for lid, info in SUPPORTED_LANGUAGES.items():
            if info.get("name_ru", info["name"]) == selected_name:
                lang_id = lid
                break
        if not lang_id:
            lang_id = "python"

        code = code_text.get("1.0", "end-1c")
        if not code.strip():
            return

        win.root.config(cursor="watch")
        win.root.update()
        success, output = compile_and_run(lang_id, code)
        win.root.config(cursor="")

        # Вывод результата
        output_frame = Frame(win.content, bg="white")
        output_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        output_text = Text(output_frame, wrap="word", font=("Courier", 10), bg="#f0f0f0", height=10)
        out_scroll = Scrollbar(output_frame, command=output_text.yview)
        output_text.config(yscrollcommand=out_scroll.set)
        output_text.pack(side="left", fill="both", expand=True)
        out_scroll.pack(side="right", fill="y")
        output_text.insert("1.0", output)

    Button(button_frame, text="Run", command=run_code, width=15).pack(side="left", padx=5)
    Button(button_frame, text=LANG["exit"], command=win.root.destroy, width=15).pack(side="left", padx=5)

    # Настройка растягивания
    win.content.grid_rowconfigure(1, weight=1)
    win.content.grid_columnconfigure(0, weight=1)
    win.content.grid_rowconfigure(3, weight=1)

    win.mainloop()

# ======================
# ТОЧКА ВХОДА
# ======================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        create_gui_compiler_hub()
    else:
        cli_compiler_hub()
