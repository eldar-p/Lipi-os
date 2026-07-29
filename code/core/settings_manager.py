"""Lipi OS settings (CLI + GUI).

NOTE: This module lives under core/ to avoid colliding with the settings/
directory that stores config.json and language files.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from i18n import ensure_lang_files, get_language_strings
from paths import APPS_DIR, CONFIG_FILE, SETTINGS_DIR, ensure_runtime_dirs

ensure_runtime_dirs()
ensure_lang_files()


def init_default_config() -> dict:
    default_config = {
        "language": "en",
        "theme": "light",
        "compiler_paths": {},
        "app_directory": str(APPS_DIR),
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(default_config, f, ensure_ascii=False, indent=2)
    return default_config


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return init_default_config()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return init_default_config()
        # Fill missing keys without wiping user values
        defaults = {
            "language": "en",
            "theme": "light",
            "compiler_paths": {},
            "app_directory": str(APPS_DIR),
        }
        changed = False
        for key, value in defaults.items():
            if key not in data:
                data[key] = value
                changed = True
        if changed:
            save_config(data)
        return data
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return init_default_config()


def save_config(config: dict) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_config() -> dict:
    return load_config()


def get_lang_strings() -> dict:
    config = load_config()
    return get_language_strings(config.get("language", "en"))


def cli_settings() -> None:
    config = load_config()
    lang = get_language_strings(config.get("language", "en"))

    while True:
        print(f"\n=== {lang['settings_title']} ===")
        print(f"1. {lang['language']}: {config.get('language', 'en')}")
        print(f"2. {lang['theme']}: {config.get('theme', 'light')}")
        print(f"3. {lang['app_directory']}: {config.get('app_directory', APPS_DIR)}")
        print(f"4. {lang['compiler_paths']}")
        print(f"0. {lang['exit']}")
        choice = input("> ").strip()

        if choice == "0":
            break
        if choice == "1":
            print("Available languages:")
            print("  en - English")
            print("  ru - Русский")
            new_lang = input("Enter language code: ").strip().lower()
            if new_lang in ("en", "ru"):
                config["language"] = new_lang
                lang = get_language_strings(new_lang)
                print(f"Language changed to {lang['language_name']}")
            else:
                print("Invalid language code")
        elif choice == "2":
            theme = input(
                f"Theme (light/dark) [current: {config.get('theme', 'light')}]: "
            ).strip().lower()
            if theme in ("light", "dark"):
                config["theme"] = theme
            else:
                print("Invalid theme")
        elif choice == "3":
            path = input(
                f"App directory [current: {config.get('app_directory')}]: "
            ).strip()
            if path:
                config["app_directory"] = path
        elif choice == "4":
            compilers = config.setdefault("compiler_paths", {})
            print("Current compiler paths:")
            if compilers:
                for name, path in compilers.items():
                    print(f"  {name}: {path}")
            else:
                print("  (none)")
            print("Enter '<name> <path>', or 'done' to finish:")
            while True:
                line = input("> ").strip()
                if line.lower() == "done":
                    break
                if " " in line:
                    name, path = line.split(" ", 1)
                    compilers[name] = path
                else:
                    print("Format: <name> <path>")

    save_config(config)
    print(lang["restart_required"])


def create_gui_settings(master=None) -> None:
    try:
        from core.gui_engine import LipiWindow
    except ImportError:
        print("GUI not available. Using CLI.")
        return cli_settings()

    config = load_config()
    lang = get_language_strings(config.get("language", "en"))

    win = LipiWindow(lang["settings_title"], 600, 500, master=master)
    from tkinter import Button, Entry, Frame, Label, OptionMenu, StringVar

    theme_map = {
        "light": lang["light"],
        "dark": lang["dark"],
    }
    theme_reverse = {v: k for k, v in theme_map.items()}

    lang_var = StringVar(value=config.get("language", "en"))
    theme_var = StringVar(value=theme_map.get(config.get("theme", "light"), lang["light"]))
    app_dir_var = StringVar(value=str(config.get("app_directory", APPS_DIR)))

    content = win.content
    row = 0

    Label(content, text=lang["language"], bg="white").grid(
        row=row, column=0, sticky="w", padx=10, pady=5
    )
    OptionMenu(content, lang_var, "en", "ru").grid(row=row, column=1, padx=10, pady=5)
    row += 1

    Label(content, text=lang["theme"], bg="white").grid(
        row=row, column=0, sticky="w", padx=10, pady=5
    )
    OptionMenu(content, theme_var, lang["light"], lang["dark"]).grid(
        row=row, column=1, padx=10, pady=5
    )
    row += 1

    Label(content, text=lang["app_directory"], bg="white").grid(
        row=row, column=0, sticky="w", padx=10, pady=5
    )
    Entry(content, textvariable=app_dir_var, width=40).grid(
        row=row, column=1, padx=10, pady=5
    )
    row += 1

    def save_and_close() -> None:
        new_config = dict(config)
        new_config["language"] = lang_var.get()
        new_config["theme"] = theme_reverse.get(theme_var.get(), "light")
        new_config["app_directory"] = app_dir_var.get()
        save_config(new_config)
        win.close()

    btn_frame = Frame(content, bg="white")
    btn_frame.grid(row=row, column=0, columnspan=2, pady=20)
    Button(btn_frame, text=lang["save"], command=save_and_close, width=12).pack(
        side="left", padx=5
    )
    Button(btn_frame, text=lang["cancel"], command=win.close, width=12).pack(
        side="left", padx=5
    )

    win.mainloop()


# Backward-compatible aliases used by older imports
DEFAULT_LANG = {
    "en": get_language_strings("en"),
    "ru": get_language_strings("ru"),
}


if __name__ == "__main__":
    # Allow running as: python -m core.settings_manager
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        create_gui_settings()
    else:
        cli_settings()
