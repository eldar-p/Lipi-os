"""Open / launch a Lipi application by id or name.

Usage:
  open calculator
  open text_editor --cli
  open browser https://example.com
"""
from __future__ import annotations


def run(args):
    import subprocess
    import sys

    from sdk import find_app, launch_app, list_apps

    if not args or args[0] in ("-h", "--help"):
        apps = list_apps()
        lines = [
            "Usage: open <app_id> [--cli] [args...]",
            "",
            "Installed apps:",
        ]
        if not apps:
            lines.append("  (none)")
        for app in apps:
            meta = app.get("meta") or {}
            ver = meta.get("version", "")
            desc = meta.get("description", "")
            extra = f" — {desc}" if desc else ""
            lines.append(f"  {app['id']:16} {app['name']} {ver}{extra}")
        return "\n".join(lines)

    app_id = args[0]
    rest = args[1:]
    app = find_app(app_id)
    if not app:
        return f"App not found: {app_id}"

    # Foreground CLI in the current terminal
    if "--cli" in rest:
        import os

        env = os.environ.copy()
        from paths import BASE_DIR

        prev = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(BASE_DIR) + (os.pathsep + prev if prev else "")
        code = subprocess.call(
            [sys.executable, str(app["main"]), *rest],
            cwd=str(app["path"]),
            env=env,
        )
        return "" if code == 0 else f"App exited with code {code}"

    ok, msg = launch_app(app_id, rest)
    return msg
