# app_store.py
import os
import sys
import json
import zipfile
import shutil
import requests
from pathlib import Path
from urllib.parse import urljoin

# Пути
APP_DIR = Path("apps")
STORE_CONFIG = Path("settings/appstore.json")
LANG_DIR = Path("settings/lang")

# Создаём папки при первом запуске
APP_DIR.mkdir(exist_ok=True)
STORE_CONFIG.parent.mkdir(exist_ok=True)

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

    lang_file = LANG_DIR / f"{lang}.json"
    fallback = {
        "store_title": "Lipi App Store",
        "installed": "Installed Apps",
        "online": "Online Catalog",
        "install": "Install",
        "uninstall": "Uninstall",
        "name": "Name",
        "version": "Version",
        "author": "Author",
        "description": "Description",
        "back": "Back",
        "exit": "Exit",
        "enter_url": "Enter .lipi URL or local path:",
        "invalid_package": "Invalid package: missing description.json or main.py",
        "already_installed": "App already installed: {}",
        "installed_success": "Successfully installed: {}",
        "uninstalled": "Uninstalled: {}",
        "not_found": "App not found",
        "loading": "Loading...",
        "online_repo": "https://raw.githubusercontent.com/lipi-os/apps/main/catalog.json"
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

def get_installed_apps():
    """Возвращает список установленных приложений"""
    apps = []
    for app_folder in APP_DIR.iterdir():
        if app_folder.is_dir():
            desc_file = app_folder / "description.json"
            if desc_file.exists():
                try:
                    with open(desc_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        meta["id"] = app_folder.name
                        apps.append(meta)
                except:
                    continue
    return apps

def install_from_path(path: Path):
    """Устанавливает приложение из .lipi (zip) или папки"""
    app_name = None
    temp_dir = None

    try:
        if path.suffix == ".lipi" or path.suffix == ".zip":
            # Распаковка архива
            temp_dir = Path("temp_install")
            temp_dir.mkdir(exist_ok=True)
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            source = temp_dir
        elif path.is_dir():
            source = path
        else:
            return False, LANG["invalid_package"]

        # Проверка содержимого
        desc_file = source / "description.json"
        main_file = source / "main.py"
        if not (desc_file.exists() and main_file.exists()):
            return False, LANG["invalid_package"]

        with open(desc_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
            app_name = meta.get("name", meta.get("name_en", "Unknown"))

        app_id = "".join(c if c.isalnum() else "_" for c in app_name).lower()
        target = APP_DIR / app_id

        if target.exists():
            return False, LANG["already_installed"].format(app_name)

        shutil.copytree(source, target)
        return True, LANG["installed_success"].format(app_name)

    except Exception as e:
        return False, str(e)
    finally:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

def uninstall_app(app_id: str):
    """Удаляет приложение по ID (имени папки)"""
    app_path = APP_DIR / app_id
    if app_path.exists():
        shutil.rmtree(app_path, ignore_errors=True)
        return True
    return False

def get_online_catalog():
    """Загружает онлайн-каталог из GitHub"""
    try:
        repo_url = LANG.get("online_repo", "https://raw.githubusercontent.com/lipi-os/apps/main/catalog.json")
        response = requests.get(repo_url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"apps": []}
    except:
        return {"apps": []}

# ======================
# CLI-РЕЖИМ
# ======================

def cli_app_store():
    while True:
        print(f"\n=== {LANG['store_title']} ===")
        print("1. " + LANG["installed"])
        print("2. " + LANG["online"])
        print("3. " + LANG["install"] + " (.lipi)")
        print("0. " + LANG["exit"])
        choice = input("> ").strip()

        if choice == "0":
            break
        elif choice == "1":
            show_installed_cli()
        elif choice == "2":
            show_online_cli()
        elif choice == "3":
            path = input(LANG["enter_url"] + " ").strip()
            if path:
                success, msg = install_from_path(Path(path))
                print(msg)

def show_installed_cli():
    apps = get_installed_apps()
    if not apps:
        print(LANG["not_found"])
        return
    print(f"\n{LANG['installed']}:")
    for app in apps:
        name = app.get("name", app.get("name_en", "Unknown"))
        ver = app.get("version", "?.?")
        print(f"- {name} (v{ver}) [{app['id']}]")
        print(f"  {LANG['uninstall']}: uninstall {app['id']}")

    cmd = input("\n> ").strip()
    if cmd.startswith("uninstall "):
        app_id = cmd.split(" ", 1)[1]
        if uninstall_app(app_id):
            print(LANG["uninstalled"].format(app_id))
        else:
            print(LANG["not_found"])

def show_online_cli():
    print(LANG["loading"])
    catalog = get_online_catalog()
    apps = catalog.get("apps", [])
    if not apps:
        print(LANG["not_found"])
        return

    print(f"\n{LANG['online']}:")
    for i, app in enumerate(apps):
        name = app.get("name", app.get("name_en", "Unknown"))
        print(f"{i+1}. {name} (v{app.get('version', '?')}) - {app.get('author', '')}")

    try:
        choice = input("\n" + LANG["install"] + " # (0=cancel): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(apps):
            app = apps[int(choice)-1]
            url = app.get("download_url")
            if url:
                # Скачиваем .lipi
                local_path = Path(f"temp_{Path(url).name}")
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    with open(local_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                success, msg = install_from_path(local_path)
                print(msg)
                local_path.unlink(missing_ok=True)
    except Exception as e:
        print("Error:", e)

# ======================
# GUI-РЕЖИМ (опционально)
# ======================

def create_gui_app_store():
    try:
        from gui_engine import LipiWindow
    except ImportError:
        print("GUI not available. Using CLI.")
        return cli_app_store()

    win = LipiWindow(LANG["store_title"], 800, 600)
    from tkinter import Listbox, Scrollbar, Button, END, Frame, Label

    def show_installed():
        for widget in content_frame.winfo_children():
            widget.destroy()

        Label(content_frame, text=LANG["installed"], bg="white", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        listbox = Listbox(content_frame, width=100, height=20)
        scrollbar = Scrollbar(content_frame, orient="vertical", command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)

        apps = get_installed_apps()
        for app in apps:
            name = app.get("name", app.get("name_en", "Unknown"))
            listbox.insert(END, f"{name} (v{app.get('version', '?')}) [{app['id']}]")

        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def on_uninstall():
            sel = listbox.curselection()
            if sel:
                line = listbox.get(sel[0])
                # Извлекаем ID из скобок в конце: [app_id]
                if "[" in line and "]" in line:
                    app_id = line.split("[")[-1].rstrip("]")
                    if uninstall_app(app_id):
                        show_installed()

        Button(content_frame, text=LANG["uninstall"], command=on_uninstall).pack(pady=5)
        Button(content_frame, text=LANG["back"], command=main_menu).pack(pady=5)

    def show_online():
        for widget in content_frame.winfo_children():
            widget.destroy()

        Label(content_frame, text=LANG["loading"], bg="white").pack()
        win.root.update()

        catalog = get_online_catalog()
        apps = catalog.get("apps", [])

        for widget in content_frame.winfo_children():
            widget.destroy()

        if not apps:
            Label(content_frame, text=LANG["not_found"], bg="white").pack()
        else:
            Label(content_frame, text=LANG["online"], bg="white", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
            listbox = Listbox(content_frame, width=100, height=20)
            for app in apps:
                name = app.get("name", app.get("name_en", "Unknown"))
                listbox.insert(END, f"{name} (v{app.get('version', '?')})")
            listbox.pack(fill="both", expand=True)

            def on_install():
                sel = listbox.curselection()
                if sel and 0 <= sel[0] < len(apps):
                    app = apps[sel[0]]
                    url = app.get("download_url")
                    if url:
                        try:
                            local_path = Path(f"temp_{Path(url).name}")
                            with requests.get(url, stream=True) as r:
                                r.raise_for_status()
                                with open(local_path, 'wb') as f:
                                    for chunk in r.iter_content(chunk_size=8192):
                                        f.write(chunk)
                            success, msg = install_from_path(local_path)
                            print(msg)  # или показать в GUI
                            local_path.unlink(missing_ok=True)
                            show_online()
                        except Exception as e:
                            print("Install error:", e)

            Button(content_frame, text=LANG["install"], command=on_install).pack(pady=5)

        Button(content_frame, text=LANG["back"], command=main_menu).pack(pady=5)

    def install_manual():
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title=LANG["install"],
            filetypes=[("Lipi App", "*.lipi"), ("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        if path:
            success, msg = install_from_path(Path(path))
            print(msg)  # или messagebox

    def main_menu():
        for widget in content_frame.winfo_children():
            widget.destroy()
        Button(content_frame, text=LANG["installed"], command=show_installed, width=30).pack(pady=5)
        Button(content_frame, text=LANG["online"], command=show_online, width=30).pack(pady=5)
        Button(content_frame, text=LANG["install"] + " (.lipi)", command=install_manual, width=30).pack(pady=5)
        Button(content_frame, text=LANG["exit"], command=win.root.destroy, width=30).pack(pady=5)

    content_frame = Frame(win.content, bg="white")
    content_frame.pack(fill="both", expand=True, padx=10, pady=10)

    main_menu()
    win.mainloop()

# ======================
# ТОЧКА ВХОДА
# ======================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        create_gui_app_store()
    else:
        cli_app_store()
