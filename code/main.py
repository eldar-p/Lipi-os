# main.py
import os
import sys
import json
import time
import threading
from pathlib import Path

# ANSI цвета для CLI (работают в Windows 10+, Linux, macOS)
COLORS = {
    "green": "\033[92m",
    "blue": "\033[94m",
    "cyan": "\033[96m",
    "reset": "\033[0m"
}

def print_boot_message(step, delay=0.3):
    """Печатает этап загрузки с задержкой (для CLI)"""
    print(f"{COLORS['cyan']}[BOOT]{COLORS['reset']} {step}")
    time.sleep(delay)

def show_cli_boot_screen():
    """Загрузочный экран в консоли"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    logo = f"""


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
    time.sleep(0.5)

    steps = [
        "Initializing core modules...",
        "Loading language settings...",
        "Mounting application directory...",
        "Scanning installed apps...",
        "Starting command interpreter...",
        "Launching desktop environment..."
    ]

    for step in steps:
        print_boot_message(step)
    
    print(f"\n{COLORS['green']}✓ Lipi OS is ready!{COLORS['reset']}\n")
    time.sleep(0.5)

def show_gui_boot_screen(callback):
    """Показывает сплэш-скрин в GUI и вызывает callback после загрузки"""
    try:
        import tkinter as tk
        from tkinter import ttk

        splash = tk.Tk()
        splash.title("Lipi OS")
        splash.geometry("500x300")
        splash.resizable(False, False)
        splash.overrideredirect(True)  # Без рамки

        # Центрирование
        splash.eval('tk::PlaceWindow . center')

        # Фон
        bg = tk.Frame(splash, bg="#0f0f1b")
        bg.pack(fill="both", expand=True)

        # Логотип
        logo_label = tk.Label(
            bg,
            text="Lipi OS",
            font=("Courier", 24, "bold"),
            fg="#4dff4d",
            bg="#0f0f1b"
        )
        logo_label.pack(pady=(40, 10))

        subtitle = tk.Label(
            bg,
            text="Your Python-based Operating Environment",
            font=("Arial", 10),
            fg="#a0a0ff",
            bg="#0f0f1b"
        )
        subtitle.pack()

        # Прогресс
        progress = ttk.Progressbar(bg, orient="horizontal", length=300, mode="determinate")
        progress.pack(pady=30)
        progress['value'] = 0

        status_label = tk.Label(bg, text="Starting...", fg="white", bg="#0f0f1b")
        status_label.pack()

        steps = [
            "Initializing core modules",
            "Loading language settings",
            "Mounting application directory",
            "Scanning installed apps",
            "Starting command interpreter",
            "Launching desktop environment"
        ]

        def animate_progress():
            for i, step in enumerate(steps):
                time.sleep(0.4)
                progress['value'] = (i + 1) * 100 / len(steps)
                status_label.config(text=step)
                splash.update()
            time.sleep(0.3)
            splash.destroy()
            callback()

        # Запуск анимации в фоне
        threading.Thread(target=animate_progress, daemon=True).start()
        splash.mainloop()

    except Exception as e:
        print(f"GUI boot screen failed: {e}")
        callback()

# === ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ ===
def init_lipi_os():
    dirs = ["apps", "commands", "settings", "settings/lang", "temp"]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)

    config_file = Path("settings/config.json")
    if not config_file.exists():
        default_config = {
            "language": "en",
            "theme": "light",
            "compiler_paths": {},
            "app_directory": "apps"
        }
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)

    # Языковые файлы
    from settings import DEFAULT_LANG
    for lang_code, data in DEFAULT_LANG.items():
        lang_file = Path(f"settings/lang/{lang_code}.json")
        if not lang_file.exists():
            with open(lang_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

def show_help():
    print("""
Lipi OS v8+ — Your Python-based Operating Environment

Usage:
  python main.py                # Auto: GUI if available, else CLI
  python main.py --gui          # Force GUI mode
  python main.py --cli          # Force CLI mode
  python main.py --help         # Show this help
""")
    sys.exit(0)

# === ЗАПУСК РЕЖИМОВ ===
def launch_gui():
    try:
        from gui_engine import LipiWindow
        from settings import create_gui_settings
        from task_manager import create_gui_task_manager
        from app_store import create_gui_app_store
        from compiler_hub import create_gui_compiler_hub
    except ImportError:
        return False

    desktop = LipiWindow("Lipi OS Desktop", 1000, 700)
    from tkinter import Menu, Label

    menubar = Menu(desktop.root)
    apps_menu = Menu(menubar, tearoff=0)
    
    apps_dir = Path("apps")
    if apps_dir.exists():
        for app_folder in apps_dir.iterdir():
            if app_folder.is_dir():
                desc_file = app_folder / "description.json"
                app_name = app_folder.name
                if desc_file.exists():
                    try:
                        with open(desc_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            app_name = meta.get("name", meta.get("name_en", app_folder.name))
                    except:
                        pass
                apps_menu.add_command(
                    label=app_name,
                    command=lambda f=app_folder: run_app_from_gui(f)
                )
    
    apps_menu.add_separator()
    apps_menu.add_command(label="Task Manager", command=create_gui_task_manager)
    apps_menu.add_command(label="App Store", command=create_gui_app_store)
    apps_menu.add_command(label="Compiler Hub", command=create_gui_compiler_hub)
    apps_menu.add_command(label="Settings", command=create_gui_settings)
    
    menubar.add_cascade(label="Applications", menu=apps_menu)
    desktop.root.config(menu=menubar)

    Label(desktop.content, text="Welcome to Lipi OS!", bg="white", font=("Arial", 16)).pack(pady=20)
    Label(desktop.content, text="Click 'Applications' to launch programs", bg="white").pack()

    desktop.mainloop()
    return True

def run_app_from_gui(app_path):
    import subprocess
    import sys
    main_py = app_path / "main.py"
    if main_py.exists():
        subprocess.Popen([sys.executable, str(main_py)], cwd=str(app_path))

def launch_cli():
    try:
        from shell import start_shell
        start_shell()
    except ImportError:
        print("Shell module not found!")
        sys.exit(1)

# === ТОЧКА ВХОДА ===
if __name__ == "__main__":
    init_lipi_os()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            show_help()
        elif sys.argv[1] == "--gui":
            show_gui_boot_screen(lambda: launch_gui() or launch_cli())
        elif sys.argv[1] == "--cli":
            show_cli_boot_screen()
            launch_cli()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            show_help()
    else:
        # Авто-режим
        try:
            import tkinter
            show_gui_boot_screen(lambda: launch_gui() or launch_cli())
        except ImportError:
            show_cli_boot_screen()
            launch_cli()
