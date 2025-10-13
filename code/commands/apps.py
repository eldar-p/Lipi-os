# commands/apps.py
from pathlib import Path

def run(args):
    apps_dir = Path("apps")
    if not apps_dir.exists():
        return "No apps installed. Directory 'apps/' not found."
    
    app_folders = [f.name for f in apps_dir.iterdir() if f.is_dir()]
    
    if not app_folders:
        return "No applications installed."
    
    output = "Installed applications:\n"
    for app in sorted(app_folders):
        output += f"  - {app}\n"
    return output.strip()
