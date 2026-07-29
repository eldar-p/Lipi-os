"""List installed Lipi apps (with metadata)."""
from __future__ import annotations


def run(args):
    from sdk import list_apps

    apps = list_apps()
    if not apps:
        return "No applications installed."

    if args and args[0] in ("-v", "--verbose", "info"):
        lines = ["Installed applications:"]
        for app in apps:
            meta = app.get("meta") or {}
            lines.append(f"  [{app['id']}] {app['name']}")
            if meta.get("version"):
                lines.append(f"      version: {meta['version']}")
            if meta.get("author"):
                lines.append(f"      author:  {meta['author']}")
            if meta.get("description"):
                lines.append(f"      desc:    {meta['description']}")
            lines.append(f"      path:    {app['path']}")
            lines.append(f"      launch:  open {app['id']}")
        return "\n".join(lines)

    lines = ["Installed applications (open <id>):"]
    for app in apps:
        meta = app.get("meta") or {}
        desc = meta.get("description", "")
        suffix = f" — {desc}" if desc else ""
        lines.append(f"  {app['id']:16} {app['name']}{suffix}")
    return "\n".join(lines)
