"""Settings app — GUI/CLI wrapper around core.settings_manager."""
from __future__ import annotations

import sys
from pathlib import Path

_CODE = Path(__file__).resolve().parents[2]
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))

from sdk import run_app_main


def run_gui() -> None:
    from core.settings_manager import create_gui_settings

    create_gui_settings()


def run_cli() -> None:
    from core.settings_manager import cli_settings

    cli_settings()


if __name__ == "__main__":
    run_app_main(run_gui, run_cli)
