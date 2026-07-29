"""Lipi OS entry point."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Ensure imports resolve from the code/ directory regardless of CWD
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
os.chdir(BASE_DIR)

from i18n import ensure_lang_files, get_language_strings
from paths import APPS_DIR, ensure_runtime_dirs


def _resolved_apps_dir():
    """Prefer configured app_directory (same as store / open)."""
    try:
        from core.app_store import _apps_dir

        return _apps_dir()
    except Exception:
        return APPS_DIR

COLORS = {
    "green": "\033[92m",
    "cyan": "\033[96m",
    "reset": "\033[0m",
}


def print_boot_message(step: str, delay: float = 0.15) -> None:
    print(f"{COLORS['cyan']}[BOOT]{COLORS['reset']} {step}")
    time.sleep(delay)


def show_cli_boot_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")
    logo = r"""
 __
/\ \       __          __
\ \ \     /\_\  _____ /\_\      ___     ____
 \ \ \  __\/\ \/\ '__`\/\ \    / __`\  /',__\
  \ \ \L\ \\ \ \ \ \L\ \ \ \  /\ \L\ \/\__, `\
   \ \____/ \ \_\ \ ,__/\ \_\ \ \____/\/\____/
    \/___/   \/_/\ \ \/  \/_/  \/___/  \/___/
                  \ \_\
                   \/_/
          Lipi OS v8+ — Your Python OS
"""
    print(logo)
    time.sleep(0.2)

    steps = [
        "Initializing core modules...",
        "Loading language settings...",
        "Mounting application directory...",
        "Scanning installed apps...",
        "Starting command interpreter...",
        "Ready.",
    ]
    for step in steps:
        print_boot_message(step)

    print(f"\n{COLORS['green']}✓ Lipi OS is ready!{COLORS['reset']}\n")
    time.sleep(0.2)


def show_gui_boot_screen(callback) -> None:
    """Splash screen animated on the Tk main thread (thread-safe)."""
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError as e:
        print(f"GUI boot screen failed: {e}")
        callback()
        return

    splash = tk.Tk()
    splash.title("Lipi OS")
    splash.geometry("500x300")
    splash.resizable(False, False)
    splash.overrideredirect(True)
    splash.eval("tk::PlaceWindow . center")

    bg = tk.Frame(splash, bg="#0f0f1b")
    bg.pack(fill="both", expand=True)

    tk.Label(
        bg,
        text="Lipi OS",
        font=("Courier", 24, "bold"),
        fg="#4dff4d",
        bg="#0f0f1b",
    ).pack(pady=(40, 10))

    tk.Label(
        bg,
        text="Your Python-based Operating Environment",
        font=("Arial", 10),
        fg="#a0a0ff",
        bg="#0f0f1b",
    ).pack()

    progress = ttk.Progressbar(bg, orient="horizontal", length=300, mode="determinate")
    progress.pack(pady=30)
    progress["value"] = 0

    status_label = tk.Label(bg, text="Starting...", fg="white", bg="#0f0f1b")
    status_label.pack()

    steps = [
        "Initializing core modules",
        "Loading language settings",
        "Mounting application directory",
        "Scanning installed apps",
        "Starting command interpreter",
        "Launching desktop environment",
    ]
    state = {"index": 0}

    def tick() -> None:
        i = state["index"]
        if i < len(steps):
            progress["value"] = (i + 1) * 100 / len(steps)
            status_label.config(text=steps[i])
            state["index"] = i + 1
            splash.after(250, tick)
        else:
            splash.destroy()
            callback()

    splash.after(200, tick)
    splash.mainloop()


def init_lipi_os() -> None:
    ensure_runtime_dirs()
    ensure_lang_files()
    from core.settings_manager import load_config

    load_config()


def show_help() -> None:
    print(
        """
Lipi OS v8+ — Your Python-based Operating Environment

Usage:
  python main.py                # Auto: GUI if available, else CLI
  python main.py --gui          # Force GUI mode
  python main.py --cli          # Force CLI mode
  python main.py --help         # Show this help
"""
    )
    sys.exit(0)


def run_app_from_gui(app_path: Path) -> None:
    main_py = app_path / "main.py"
    if main_py.exists():
        env = os.environ.copy()
        prev = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(BASE_DIR) + (os.pathsep + prev if prev else "")
        subprocess.Popen(
            [sys.executable, str(main_py)],
            cwd=str(app_path),
            env=env,
        )


def launch_gui() -> bool:
    try:
        import tkinter  # noqa: F401
        from tkinter import Label, Menu

        from core.app_store import create_gui_app_store
        from core.compiler_hub import create_gui_compiler_hub
        from core.gui_engine import LipiWindow
        from core.settings_manager import create_gui_settings
        from core.task_manager import create_gui_task_manager
    except ImportError:
        return False

    lang = get_language_strings()
    from i18n import load_config_language

    lang_code = load_config_language()
    desktop = LipiWindow("Lipi OS Desktop", 1000, 700)

    menubar = Menu(desktop.root)
    apps_menu = Menu(menubar, tearoff=0)

    if _resolved_apps_dir().exists():
        for app_folder in sorted(_resolved_apps_dir().iterdir()):
            if not app_folder.is_dir() or not (app_folder / "main.py").exists():
                continue
            desc_file = app_folder / "description.json"
            app_name = app_folder.name
            if desc_file.exists():
                try:
                    with open(desc_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    if lang_code.startswith("ru") and meta.get("name_ru"):
                        app_name = meta["name_ru"]
                    else:
                        app_name = meta.get("name") or meta.get("name_en") or app_folder.name
                except (OSError, json.JSONDecodeError, TypeError, ValueError):
                    pass
            apps_menu.add_command(
                label=app_name,
                command=lambda f=app_folder: run_app_from_gui(f),
            )

    apps_menu.add_separator()
    apps_menu.add_command(
        label=lang.get("task_manager", "Task Manager"),
        command=lambda: create_gui_task_manager(desktop.root),
    )
    apps_menu.add_command(
        label=lang.get("app_store", "App Store"),
        command=lambda: create_gui_app_store(desktop.root),
    )
    apps_menu.add_command(
        label=lang.get("compiler_hub", "Compiler Hub"),
        command=lambda: create_gui_compiler_hub(desktop.root),
    )
    apps_menu.add_command(
        label=lang.get("settings", "Settings"),
        command=lambda: create_gui_settings(desktop.root),
    )

    menubar.add_cascade(label=lang.get("applications", "Applications"), menu=apps_menu)
    desktop.root.config(menu=menubar)

    Label(
        desktop.content,
        text=lang.get("welcome", "Welcome to Lipi OS!"),
        bg="white",
        font=("Arial", 16),
    ).pack(pady=20)
    Label(
        desktop.content,
        text=lang.get("desktop_hint", "Open Applications to launch programs"),
        bg="white",
    ).pack()

    desktop.mainloop()
    return True


def launch_cli() -> None:
    try:
        from core.shell import start_shell

        start_shell()
    except ImportError as e:
        print(f"Shell module not found: {e}")
        sys.exit(1)


def main() -> None:
    init_lipi_os()

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--help":
            show_help()
        elif arg == "--gui":
            show_gui_boot_screen(lambda: launch_gui() or (show_cli_boot_screen() or launch_cli()))
        elif arg == "--cli":
            show_cli_boot_screen()
            launch_cli()
        else:
            print(f"Unknown argument: {arg}")
            show_help()
        return

    try:
        import tkinter  # noqa: F401

        show_gui_boot_screen(lambda: launch_gui() or (show_cli_boot_screen() or launch_cli()))
    except ImportError:
        show_cli_boot_screen()
        launch_cli()


if __name__ == "__main__":
    main()
