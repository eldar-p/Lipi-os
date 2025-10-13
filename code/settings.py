# settings.py
import os
import json
import sys
from pathlib import Path

# Пути
SETTINGS_DIR = Path("settings")
LANG_DIR = SETTINGS_DIR / "lang"
CONFIG_FILE = SETTINGS_DIR / "config.json"

# Создаём папки
SETTINGS_DIR.mkdir(exist_ok=True)
LANG_DIR.mkdir(exist_ok=True)

# Языковые файлы по умолчанию
DEFAULT_LANG = {
    "en": {
        "language_name": "English",
        "settings_title": "Lipi OS Settings",
        "language": "Language",
        "theme": "Theme",
        "light": "Light",
        "dark": "Dark",
        "compiler_paths": "Compiler Paths",
        "app_directory": "App Directory",
        "save": "Save",
        "cancel": "Cancel",
        "restart_required": "Some changes require restart.",
        "browse": "Browse...",
        "back": "Back",
        "exit": "Exit"
    },
    "ru": {
        "language_name": "Русский",
        "settings_title": "Настройки Lipi OS",
        "language": "Язык",
        "theme": "Тема",
        "light": "Светлая",
        "dark": "Тёмная",
        "compiler_paths": "Пути к компиляторам",
        "app_directory": "Каталог приложений",
        "save": "Сохранить",
        "cancel": "Отмена",
        "restart_required": "Некоторые изменения требуют перезапуска.",
        "browse": "Обзор...",
        "back": "Назад",
        "exit": "Выход"
    }
}

# Создаём языковые файлы, если их нет
for lang_code, data in DEFAULT_LANG.items():
    lang_file = LANG_DIR / f"{lang_code}.json"
    if not lang_file.exists():
        with open(lang_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

# Загрузка текущего языка
def load_current_language():
    lang = "en"
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                lang = config.get("language", "en")
        except:
            pass
    return lang

def get_language_strings(lang_code):
    lang_file = LANG_DIR / f"{lang_code}.json"
    if lang_file.exists():
        with open(lang_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_LANG.get(lang_code, DEFAULT_LANG["en"])

# Инициализация конфига по умолчанию
def init_default_config():
    default_config = {
        "language": "en",
        "theme": "light",
        "compiler_paths": {},
        "app_directory": str(Path("apps").resolve())
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(default_config, f, ensure_ascii=False, indent=2)
    return default_config

def load_config():
    if not CONFIG_FILE.exists():
        return init_default_config()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return init_default_config()

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# ======================
# CLI-РЕЖИМ
# ======================

def cli_settings():
    config = load_config()
    LANG = get_language_strings(config["language"])

    while True:
        print(f"\n=== {LANG['settings_title']} ===")
        print(f"1. {LANG['language']}: {config['language']}")
        print(f"2. {LANG['theme']}: {config['theme']}")
        print(f"3. {LANG['app_directory']}: {config['app_directory']}")
        print("4. Compiler Paths")
        print("0. " + LANG["exit"])
        choice = input("> ").strip()

        if choice == "0":
            break
        elif choice == "1":
            print("Available languages:")
            print("  en - English")
            print("  ru - Русский")
            lang = input("Enter language code: ").strip().lower()
            if lang in ["en", "ru"]:
                config["language"] = lang
                LANG = get_language_strings(lang)  # обновляем строки
                print(f"Language changed to {LANG['language_name']}")
            else:
                print("Invalid language code")
        elif choice == "2":
            theme = input(f"Theme (light/dark) [current: {config['theme']}]: ").strip().lower()
            if theme in ["light", "dark"]:
                config["theme"] = theme
            else:
                print("Invalid theme")
        elif choice == "3":
            path = input(f"App directory [current: {config['app_directory']}]: ").strip()
            if path:
                config["app_directory"] = path
        elif choice == "4":
            print("Current compiler paths:")
            for name, path in config["compiler_paths"].items():
                print(f"  {name}: {path}")
            print("Enter compiler name and path (e.g., 'gcc /usr/bin/gcc'), or 'done' to finish:")
            while True:
                line = input("> ").strip()
                if line.lower() == "done":
                    break
                if " " in line:
                    name, path = line.split(" ", 1)
                    config["compiler_paths"][name] = path
                else:
                    print("Format: <name> <path>")

    save_config(config)
    print(LANG["restart_required"])

# ======================
# GUI-РЕЖИМ
# ======================

def create_gui_settings():
    try:
        from gui_engine import LipiWindow
    except ImportError:
        print("GUI not available. Using CLI.")
        return cli_settings()

    config = load_config()
    LANG = get_language_strings(config["language"])

    win = LipiWindow(LANG["settings_title"], 600, 500)
    from tkinter import StringVar, OptionMenu, Button, Entry, Label, Frame

    # Переменные для GUI
    lang_var = StringVar(value=config["language"])
    theme_var = StringVar(value=config["theme"])
    app_dir_var = StringVar(value=config["app_directory"])

    content = win.content
    row = 0

    # Язык
    Label(content, text=LANG["language"], bg="white").grid(row=row, column=0, sticky="w", padx=10, pady=5)
    lang_menu = OptionMenu(content, lang_var, "en", "ru")
    lang_menu.grid(row=row, column=1, padx=10, pady=5)
    row += 1

    # Тема
    Label(content, text=LANG["theme"], bg="white").grid(row=row, column=0, sticky="w", padx=10, pady=5)
    theme_menu = OptionMenu(content, theme_var, LANG["light"], LANG["dark"])
    theme_menu.grid(row=row, column=1, padx=10, pady=5)
    # Сопоставление отображаемого имени с внутренним значением
    def on_theme_change(*args):
        display = theme_var.get()
        if display == LANG["dark"]:
            theme_var.set_internal("dark")
        elif display == LANG["light"]:
            theme_var.set_internal("light")
    # Хак для хранения внутреннего значения
    theme_var.set_internal = lambda v: setattr(theme_var, '_internal', v)
    theme_var.get_internal = lambda: getattr(theme_var, '_internal', theme_var.get())
    theme_var.set_internal(config["theme"])
    theme_var.trace_add("write", on_theme_change)
    row += 1

    # Каталог приложений
    Label(content, text=LANG["app_directory"], bg="white").grid(row=row, column=0, sticky="w", padx=10, pady=5)
    app_dir_entry = Entry(content, textvariable=app_dir_var, width=40)
    app_dir_entry.grid(row=row, column=1, padx=10, pady=5)
    row += 1

    # Кнопки
    def save_and_close():
        # Обновляем конфиг
        new_config = config.copy()
        new_config["language"] = lang_var.get()
        new_config["theme"] = theme_var.get_internal()
        new_config["app_directory"] = app_dir_var.get()

        # Обновляем пути к компиляторам (пока не редактируем в GUI — можно добавить позже)
        save_config(new_config)
        win.root.destroy()
        # Применяем тему (опционально)
        apply_theme(new_config["theme"])

    def apply_theme(theme):
        # Здесь можно применить тему к другим окнам (если поддерживается)
        pass

    btn_frame = Frame(content, bg="white")
    btn_frame.grid(row=row, column=0, columnspan=2, pady=20)
    Button(btn_frame, text=LANG["save"], command=save_and_close, width=12).pack(side="left", padx=5)
    Button(btn_frame, text=LANG["cancel"], command=win.root.destroy, width=12).pack(side="left", padx=5)

    win.mainloop()

# ======================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ВСЕЙ СИСТЕМЫ
# ======================

def get_config():
    """Возвращает текущую конфигурацию (для других модулей)"""
    return load_config()

def get_lang_strings():
    """Возвращает строки текущего языка (для других модулей)"""
    config = load_config()
    return get_language_strings(config["language"])

# ======================
# ТОЧКА ВХОДА
# ======================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        create_gui_settings()
    else:
        cli_settings()
