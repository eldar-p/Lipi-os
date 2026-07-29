"""Central path helpers for Lipi OS.

All modules should resolve files relative to the code/ directory
(the directory that contains main.py), not the process CWD.
"""
from pathlib import Path

# Directory containing main.py (the Lipi OS root for runtime files)
BASE_DIR = Path(__file__).resolve().parent

APPS_DIR = BASE_DIR / "apps"
COMMANDS_DIR = BASE_DIR / "commands"
CORE_DIR = BASE_DIR / "core"
SETTINGS_DIR = BASE_DIR / "settings"
LANG_DIR = SETTINGS_DIR / "lang"
CONFIG_FILE = SETTINGS_DIR / "config.json"
TEMP_DIR = BASE_DIR / "temp"


def ensure_runtime_dirs() -> None:
    """Create required runtime directories if they are missing."""
    for path in (APPS_DIR, COMMANDS_DIR, SETTINGS_DIR, LANG_DIR, TEMP_DIR):
        path.mkdir(parents=True, exist_ok=True)
