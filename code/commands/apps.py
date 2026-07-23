"""List installed Lipi apps."""
from pathlib import Path

from paths import APPS_DIR


def run(args):
    from paths import BASE_DIR

    try:
        from core.settings_manager import load_config

        raw = Path(load_config().get("app_directory", APPS_DIR))
        apps_dir = raw if raw.is_absolute() else (BASE_DIR / raw)
        apps_dir = apps_dir.resolve()
    except Exception:
        apps_dir = APPS_DIR

    if not apps_dir.exists():
        return "No apps installed. Directory 'apps/' not found."

    app_folders = [f.name for f in apps_dir.iterdir() if f.is_dir()]
    if not app_folders:
        return "No applications installed."

    lines = ["Installed applications:"]
    for app in sorted(app_folders):
        lines.append(f"  - {app}")
    return "\n".join(lines)
