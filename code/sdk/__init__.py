"""Lipi OS App SDK — helpers for third-party and built-in apps.

Apps are launched as separate processes with cwd=app folder, so this
module puts the Lipi ``code/`` root on ``sys.path`` and exposes common
helpers (config, i18n, paths, CLI/GUI mode detection).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def lipi_root() -> Path:
    """Return the Lipi ``code/`` directory (contains main.py, apps/, core/)."""
    # sdk/ lives at code/sdk/ → parent is code/
    return Path(__file__).resolve().parent.parent


def ensure_import_path() -> Path:
    """Make ``import paths``, ``import core`` work from app processes."""
    root = lipi_root()
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    return root


ensure_import_path()


def is_cli(argv: list[str] | None = None) -> bool:
    argv = argv if argv is not None else sys.argv
    return "--cli" in argv


def load_description(app_dir: Path | None = None) -> dict[str, Any]:
    """Load description.json next to the calling app (or given dir)."""
    base = app_dir or Path.cwd()
    path = base / "description.json"
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return {}


def display_name(meta: dict[str, Any] | None = None, lang_code: str | None = None) -> str:
    from i18n import load_config_language

    meta = meta or {}
    lang = lang_code or load_config_language()
    if lang.startswith("ru") and meta.get("name_ru"):
        return str(meta["name_ru"])
    return str(meta.get("name") or meta.get("name_en") or "Lipi App")


def get_config() -> dict:
    from core.settings_manager import load_config

    return load_config()


def get_lang() -> dict:
    from i18n import get_language_strings

    return get_language_strings()


def apps_directory() -> Path:
    from paths import APPS_DIR, BASE_DIR
    from core.settings_manager import load_config

    raw = Path(load_config().get("app_directory", APPS_DIR))
    return raw if raw.is_absolute() else (BASE_DIR / raw).resolve()


def list_apps() -> list[dict[str, Any]]:
    """Return installed apps with id, path, and description meta."""
    apps_dir = apps_directory()
    result: list[dict[str, Any]] = []
    if not apps_dir.exists():
        return result
    for folder in sorted(apps_dir.iterdir()):
        if not folder.is_dir():
            continue
        main_py = folder / "main.py"
        if not main_py.exists():
            continue
        meta = load_description(folder)
        result.append(
            {
                "id": folder.name,
                "path": folder,
                "main": main_py,
                "meta": meta,
                "name": display_name(meta),
            }
        )
    return result


def find_app(app_id: str) -> dict[str, Any] | None:
    app_id = app_id.strip().lower().replace(" ", "_")
    for app in list_apps():
        if app["id"] == app_id:
            return app
        meta = app.get("meta") or {}
        for key in ("name", "name_en", "name_ru"):
            val = str(meta.get(key, "")).lower().replace(" ", "_")
            if val and val == app_id:
                return app
    return None


def launch_app(app_id: str, extra_args: list[str] | None = None) -> tuple[bool, str]:
    """Start an installed app as a subprocess. Returns (ok, message)."""
    import os
    import subprocess

    app = find_app(app_id)
    if not app:
        return False, f"App not found: {app_id}"
    cmd = [sys.executable, str(app["main"])]
    if extra_args:
        cmd.extend(extra_args)
    env = os.environ.copy()
    root = str(lipi_root())
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = root + (os.pathsep + prev if prev else "")
    try:
        subprocess.Popen(cmd, cwd=str(app["path"]), env=env)
        return True, f"Started {app['name']} ({app['id']})"
    except OSError as e:
        return False, f"Failed to start {app_id}: {e}"


def run_app_main(run_gui, run_cli, argv: list[str] | None = None) -> None:
    """Standard dual-mode entry: prefer GUI unless --cli or GUI fails."""
    argv = argv if argv is not None else sys.argv
    if is_cli(argv):
        run_cli()
        return
    try:
        run_gui()
    except Exception:
        run_cli()
