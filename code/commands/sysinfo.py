"""Show Lipi OS / host system information."""
import platform
import sys
from pathlib import Path

def run(args):
    lines = [
        f"Lipi OS shell on {platform.system()} {platform.release()}",
        f"Node: {platform.node()}",
        f"Arch: {platform.machine()}",
        f"Python: {sys.version.split()[0]} ({sys.executable})",
    ]
    edition = Path(__file__).resolve().parents[1] / "EDITION"
    if edition.exists():
        lines.append(f"Edition: {edition.read_text().strip()}")
    try:
        import psutil
        v = psutil.virtual_memory()
        lines.append(f"CPU: {psutil.cpu_count(logical=True)} logical, load {psutil.cpu_percent(interval=0.2)}%")
        lines.append(f"RAM: {v.percent}% used ({v.used // 1024**2}M / {v.total // 1024**2}M)")
    except Exception:
        pass
    try:
        from core.compiler_hub import language_status
        ready = sum(1 for r in language_status() if r["ready"])
        total = len(language_status())
        lines.append(f"Languages ready: {ready}/{total}  (see: langs)")
    except Exception:
        pass
    return "\n".join(lines)
