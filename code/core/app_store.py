"""Lipi OS app store (install/uninstall local and online packages)."""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

from i18n import get_language_strings
from paths import APPS_DIR, TEMP_DIR, ensure_runtime_dirs

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

ensure_runtime_dirs()

_BUILTIN_APPS = frozenset(
    {
        "browser",
        "calculator",
        "console",
        "file_manager",
        "ide",
        "settings",
        "text_editor",
    }
)
_SAFE_APP_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


def _lang() -> dict:
    return get_language_strings()


def _apps_dir() -> Path:
    """Resolve configured apps directory, falling back to default."""
    from paths import BASE_DIR

    try:
        from core.settings_manager import load_config

        raw = Path(load_config().get("app_directory", APPS_DIR))
        configured = raw if raw.is_absolute() else (BASE_DIR / raw)
        configured = configured.resolve()
        configured.mkdir(parents=True, exist_ok=True)
        return configured
    except Exception:
        APPS_DIR.mkdir(parents=True, exist_ok=True)
        return APPS_DIR


def _is_within_directory(root: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _safe_extract_zip(zip_path: Path, dest: Path) -> None:
    """Extract zip without Zip Slip (members must stay under dest)."""
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            if name.startswith("/") or ".." in Path(name).parts:
                raise ValueError(f"Unsafe path in archive: {info.filename}")
            target = (dest / name).resolve()
            if not _is_within_directory(dest, target) and target != dest:
                raise ValueError(f"Zip Slip blocked: {info.filename}")
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info, "r") as src, open(target, "wb") as out:
                    shutil.copyfileobj(src, out)


def _normalize_app_id(raw: str, fallback: str = "app") -> str:
    cleaned = "".join(c if c.isalnum() else "_" for c in str(raw)).lower().strip("_")
    if not cleaned:
        cleaned = fallback.lower()
    if not _SAFE_APP_ID.match(cleaned):
        cleaned = re.sub(r"[^a-z0-9_-]", "", cleaned)[:64] or "app"
    return cleaned


def get_installed_apps() -> list[dict]:
    apps = []
    root = _apps_dir()
    if not root.exists():
        return apps
    for app_folder in root.iterdir():
        if not app_folder.is_dir():
            continue
        desc_file = app_folder / "description.json"
        if not desc_file.exists():
            continue
        try:
            with open(desc_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            if isinstance(meta, dict):
                meta = dict(meta)
                meta["id"] = app_folder.name
                apps.append(meta)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            continue
    return apps


def install_from_path(path: Path) -> tuple[bool, str]:
    lang = _lang()
    app_name = None
    temp_dir = None

    try:
        path = Path(path)
        if path.suffix.lower() in (".lipi", ".zip"):
            temp_dir = Path(tempfile.mkdtemp(prefix="lipi_install_", dir=str(TEMP_DIR)))
            _safe_extract_zip(path, temp_dir)
            source = temp_dir
            children = [p for p in temp_dir.iterdir() if not p.name.startswith(".")]
            if len(children) == 1 and children[0].is_dir():
                if (children[0] / "description.json").exists():
                    source = children[0]
        elif path.is_dir():
            source = path
        else:
            return False, lang["invalid_package"]

        desc_file = source / "description.json"
        main_file = source / "main.py"
        if not (desc_file.exists() and main_file.exists()):
            return False, lang["invalid_package"]

        with open(desc_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
        app_name = meta.get("name") or meta.get("name_en") or path.stem
        app_id = _normalize_app_id(str(app_name), fallback=path.stem)

        apps_root = _apps_dir().resolve()
        target = (apps_root / app_id).resolve()
        if not _is_within_directory(apps_root, target):
            return False, "Invalid app id"
        if target.exists():
            return False, lang["already_installed"].format(app_name)

        shutil.copytree(source, target)
        return True, lang["installed_success"].format(app_name)
    except Exception as e:
        return False, str(e)
    finally:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def install_from_url_or_path(spec: str) -> tuple[bool, str]:
    """Install from local path or http(s) URL."""
    lang = _lang()
    text = (spec or "").strip()
    if not text:
        return False, lang["invalid_package"]

    parsed = urlparse(text)
    if parsed.scheme in ("http", "https"):
        if requests is None:
            return False, "requests is not installed"
        try:
            name = Path(parsed.path).name or "download.lipi"
            local_path = TEMP_DIR / name
            with requests.get(text, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(local_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            try:
                return install_from_path(local_path)
            finally:
                local_path.unlink(missing_ok=True)
        except Exception as e:
            return False, str(e)

    return install_from_path(Path(text))


def uninstall_app(app_id: str) -> bool:
    if not app_id or not _SAFE_APP_ID.match(app_id):
        return False
    if app_id in _BUILTIN_APPS:
        return False

    apps_root = _apps_dir().resolve()
    app_path = (apps_root / app_id).resolve()
    if not _is_within_directory(apps_root, app_path):
        return False
    if app_path.exists() and app_path.is_dir():
        shutil.rmtree(app_path, ignore_errors=True)
        return not app_path.exists()
    return False


def get_online_catalog() -> dict:
    lang = _lang()
    if requests is None:
        return {"apps": [], "error": "requests is not installed"}
    try:
        # Prefer settings/config over language strings for the catalog URL
        repo_url = None
        try:
            from core.settings_manager import load_config

            repo_url = load_config().get("app_store_catalog_url")
        except Exception:
            repo_url = None
        if not repo_url:
            repo_url = lang.get(
                "online_repo",
                "https://raw.githubusercontent.com/lipi-os/apps/main/catalog.json",
            )
        response = requests.get(repo_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, dict) else {"apps": []}
        return {"apps": [], "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"apps": [], "error": str(e)}


def cli_app_store() -> None:
    lang = _lang()
    while True:
        print(f"\n=== {lang['store_title']} ===")
        print("1. " + lang["installed"])
        print("2. " + lang["online"])
        print("3. " + lang["install"] + " (.lipi / URL)")
        print("0. " + lang["exit"])
        choice = input("> ").strip()

        if choice == "0":
            break
        if choice == "1":
            show_installed_cli()
        elif choice == "2":
            show_online_cli()
        elif choice == "3":
            path = input(lang["enter_url"] + " ").strip()
            if path:
                _, msg = install_from_url_or_path(path)
                print(msg)


def show_installed_cli() -> None:
    lang = _lang()
    apps = get_installed_apps()
    if not apps:
        print(lang["not_found"])
        return
    print(f"\n{lang['installed']}:")
    for app in apps:
        name = app.get("name") or app.get("name_en") or "Unknown"
        ver = app.get("version", "?.?")
        builtin = " [builtin]" if app["id"] in _BUILTIN_APPS else ""
        print(f"- {name} (v{ver}) [{app['id']}]{builtin}")
        if app["id"] not in _BUILTIN_APPS:
            print(f"  {lang['uninstall']}: uninstall {app['id']}")

    cmd = input("\n> ").strip()
    if cmd.startswith("uninstall "):
        app_id = cmd.split(" ", 1)[1].strip()
        if app_id in _BUILTIN_APPS:
            print("Cannot uninstall built-in app")
        elif uninstall_app(app_id):
            print(lang["uninstalled"].format(app_id))
        else:
            print(lang["not_found"])


def show_online_cli() -> None:
    lang = _lang()
    print(lang["loading"])
    catalog = get_online_catalog()
    apps = catalog.get("apps", [])
    if not apps:
        err = catalog.get("error")
        print(f"{lang['not_found']}" + (f" ({err})" if err else ""))
        return

    print(f"\n{lang['online']}:")
    for i, app in enumerate(apps):
        name = app.get("name") or app.get("name_en") or "Unknown"
        print(f"{i + 1}. {name} (v{app.get('version', '?')}) - {app.get('author', '')}")

    try:
        choice = input("\n" + lang["install"] + " # (0=cancel): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(apps):
            app = apps[int(choice) - 1]
            url = app.get("download_url")
            if url:
                ok, msg = install_from_url_or_path(url)
                print(msg)
            else:
                print(lang["not_found"])
    except Exception as e:
        print("Error:", e)


def create_gui_app_store(master=None) -> None:
    try:
        from core.gui_engine import LipiWindow
    except ImportError:
        print("GUI not available. Using CLI.")
        return cli_app_store()

    lang = _lang()
    win = LipiWindow(lang["store_title"], 800, 600, master=master)
    from tkinter import END, Button, Frame, Label, Listbox, Scrollbar, messagebox

    content_frame = Frame(win.content, bg="white")
    content_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def clear_content() -> None:
        for widget in content_frame.winfo_children():
            widget.destroy()

    def show_installed() -> None:
        clear_content()
        Label(
            content_frame, text=lang["installed"], bg="white", font=("Arial", 12, "bold")
        ).pack(anchor="w", pady=5)
        listbox = Listbox(content_frame, width=100, height=20)
        scrollbar = Scrollbar(content_frame, orient="vertical", command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)

        apps = get_installed_apps()
        for app in apps:
            name = app.get("name") or app.get("name_en") or "Unknown"
            tag = " builtin" if app["id"] in _BUILTIN_APPS else ""
            listbox.insert(END, f"{name} (v{app.get('version', '?')}) [{app['id']}]{tag}")

        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def on_uninstall() -> None:
            sel = listbox.curselection()
            if not sel:
                return
            line = listbox.get(sel[0])
            if "[" in line and "]" in line:
                app_id = line.split("[")[-1].split("]")[0].strip()
                if app_id in _BUILTIN_APPS:
                    messagebox.showwarning(lang["store_title"], "Cannot uninstall built-in app")
                    return
                if not messagebox.askyesno(lang["store_title"], f"Uninstall {app_id}?"):
                    return
                if uninstall_app(app_id):
                    show_installed()
                else:
                    messagebox.showerror(lang["store_title"], lang["not_found"])

        Button(content_frame, text=lang["uninstall"], command=on_uninstall).pack(pady=5)
        Button(content_frame, text=lang["back"], command=main_menu).pack(pady=5)

    def show_online() -> None:
        clear_content()
        Label(content_frame, text=lang["loading"], bg="white").pack()
        win.root.update()

        catalog = get_online_catalog()
        apps = catalog.get("apps", [])
        clear_content()

        if not apps:
            msg = lang["not_found"]
            if catalog.get("error"):
                msg = f"{msg}\n{catalog['error']}"
            Label(content_frame, text=msg, bg="white").pack()
        else:
            Label(
                content_frame, text=lang["online"], bg="white", font=("Arial", 12, "bold")
            ).pack(anchor="w", pady=5)
            listbox = Listbox(content_frame, width=100, height=20)
            for app in apps:
                name = app.get("name") or app.get("name_en") or "Unknown"
                listbox.insert(END, f"{name} (v{app.get('version', '?')})")
            listbox.pack(fill="both", expand=True)

            def on_install() -> None:
                sel = listbox.curselection()
                if not sel:
                    return
                idx = sel[0]
                if not (0 <= idx < len(apps)):
                    return
                app = apps[idx]
                url = app.get("download_url")
                if not url:
                    return
                try:
                    ok, msg = install_from_url_or_path(url)
                    messagebox.showinfo(lang["store_title"], msg)
                    if ok:
                        show_online()
                except Exception as e:
                    messagebox.showerror(lang["store_title"], str(e))

            Button(content_frame, text=lang["install"], command=on_install).pack(pady=5)

        Button(content_frame, text=lang["back"], command=main_menu).pack(pady=5)

    def install_manual() -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            title=lang["install"],
            filetypes=[
                ("Lipi App", "*.lipi"),
                ("ZIP files", "*.zip"),
                ("All files", "*.*"),
            ],
        )
        if path:
            _, msg = install_from_path(Path(path))
            messagebox.showinfo(lang["store_title"], msg)

    def main_menu() -> None:
        clear_content()
        Button(content_frame, text=lang["installed"], command=show_installed, width=30).pack(
            pady=5
        )
        Button(content_frame, text=lang["online"], command=show_online, width=30).pack(pady=5)
        Button(
            content_frame,
            text=lang["install"] + " (.lipi)",
            command=install_manual,
            width=30,
        ).pack(pady=5)
        Button(content_frame, text=lang["exit"], command=win.close, width=30).pack(pady=5)

    main_menu()
    win.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        create_gui_app_store()
    else:
        cli_app_store()
